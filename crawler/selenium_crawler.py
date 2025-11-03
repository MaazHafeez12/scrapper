import os
import time
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import hashlib
import urllib.robotparser as robotparser

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# Allow importing JobDatabase
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import JobDatabase

TOKENS = [
    'job', 'position', 'vacancy', 'remote', 'apply', 'career', 'freelance',
    'role', 'opening', 'opportunity', 'hiring'
]

TITLE_SELECTORS = [
    (By.CSS_SELECTOR, 'h1'),
    (By.CSS_SELECTOR, 'h2.job-title'),
    (By.CSS_SELECTOR, '.job-title'),
]
COMPANY_SELECTORS = [
    (By.CSS_SELECTOR, '.company'),
    (By.CSS_SELECTOR, '.employer'),
    (By.CSS_SELECTOR, '[data-company]'),
]
LOCATION_SELECTORS = [
    (By.CSS_SELECTOR, '.location'),
    (By.CSS_SELECTOR, '.job-location'),
    (By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'remote')]")
]
POSTED_SELECTORS = [
    (By.CSS_SELECTOR, 'time'),
    (By.CSS_SELECTOR, '.posted'),
]
BUDGET_SELECTORS = [
    (By.CSS_SELECTOR, '.budget'),
    (By.CSS_SELECTOR, '.rate'),
]
DESC_SELECTORS = [
    (By.CSS_SELECTOR, '.description'),
    (By.CSS_SELECTOR, 'article'),
    (By.CSS_SELECTOR, 'main'),
]

@dataclass
class SeleniumCrawlerConfig:
    wait_js_listing_min: float = 1.0
    wait_js_listing_max: float = 3.0
    wait_js_job: float = 1.0
    max_candidates_per_listing: int = 15
    per_domain_delay: float = 2.0
    max_pages_per_domain: int = 30
    user_agent: str = 'JobScraperBot/0.1 (+contact@example.com)'
    override_robots: bool = False
    keywords: Optional[List[str]] = None


def _sleep(seconds: float):
    try:
        time.sleep(seconds)
    except Exception:
        pass


def canonicalize(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        return url


def sha1_url(url: str) -> str:
    return hashlib.sha1(canonicalize(url).encode('utf-8')).hexdigest()


def url_depth(url: str) -> int:
    try:
        return len((urlparse(url).path or '/').strip('/').split('/'))
    except Exception:
        return 0


def should_consider_link(href: str, text: str) -> bool:
    if not href:
        return False
    h = href.lower()
    t = (text or '').lower()
    if any(tok in h or tok in t for tok in TOKENS):
        return True
    if url_depth(h) >= 2:
        return True
    if text and len(text.strip()) >= 12:
        return True
    return False


class DomainBudget:
    def __init__(self, delay: float, max_pages: int):
        self.delay = delay
        self.max_pages = max_pages
        self.counts: Dict[str, int] = {}
        self.last: Dict[str, float] = {}

    def acquire(self, url: str):
        try:
            d = (urlparse(url).netloc or '').lower()
            c = self.counts.get(d, 0)
            if c >= self.max_pages:
                raise RuntimeError(f"Domain page budget exceeded for {d}")
            now = time.time()
            last = self.last.get(d, 0.0)
            wait = max(0.0, self.delay - (now - last))
            if wait > 0:
                _sleep(wait)
            self.counts[d] = c + 1
            self.last[d] = time.time()
        except Exception:
            pass


def robots_allowed(url: str, ua: str) -> Tuple[bool, Optional[str]]:
    try:
        p = urlparse(url)
        robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(ua, url)
        return allowed, robots_url
    except Exception:
        return True, None


def extract_text(driver, selector: Tuple[str, str]) -> Optional[str]:
    by, value = selector
    try:
        el = driver.find_element(by, value)
        txt = el.text.strip()
        if not txt and el.get_attribute('content'):
            txt = (el.get_attribute('content') or '').strip()
        return txt or None
    except Exception:
        return None


def extract_description(driver) -> str:
    for sel in DESC_SELECTORS:
        txt = extract_text(driver, sel)
        if txt:
            return txt[:4000]
    try:
        return (driver.find_element(By.TAG_NAME, 'body').text or '')[:4000]
    except Exception:
        return ''


def score_keywords(title: str, description: str, keywords: Optional[List[str]]) -> int:
    if not keywords:
        return 0
    blob = f"{title or ''} {description or ''}".lower()
    score = 0
    for kw in keywords:
        kw = (kw or '').strip().lower()
        if not kw:
            continue
        score += blob.count(kw)
    # Clamp and weight lightly
    return min(score * 5, 100)


def build_driver(user_agent: str) -> webdriver.Chrome:
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    if user_agent:
        opts.add_argument(f'--user-agent={user_agent}')
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def crawl_listings(listing_urls: List[str], cfg: SeleniumCrawlerConfig, db: Optional[JobDatabase] = None) -> Dict:
    domain_budget = DomainBudget(cfg.per_domain_delay, cfg.max_pages_per_domain)
    driver = build_driver(cfg.user_agent)
    results: List[Dict] = []
    logs: List[Dict] = []

    try:
        for listing_url in listing_urls:
            log = {
                'domain': (urlparse(listing_url).netloc or '').lower(),
                'listing_url': listing_url,
                'status': 'ok',
                'found_count': 0,
                'error_message': None,
                'started_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'finished_at': None,
            }
            try:
                allowed, robots_url = robots_allowed(listing_url, cfg.user_agent)
                if not allowed and not cfg.override_robots:
                    log['status'] = 'robots-blocked'
                    log['error_message'] = f'Disallowed by robots.txt ({robots_url})'
                    logs.append(log)
                    if db and hasattr(db, 'log_crawl'):
                        db.log_crawl(log['domain'], listing_url, log['status'], 0, log['error_message'], log['started_at'], time.strftime('%Y-%m-%dT%H:%M:%S'))
                    continue

                domain_budget.acquire(listing_url)
                driver.get(listing_url)
                _sleep(max(cfg.wait_js_listing_min, min(cfg.wait_js_listing_max, cfg.wait_js_listing_max)))

                anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                candidates: List[Tuple[str, str]] = []  # (url, text)
                for a in anchors:
                    try:
                        href = a.get_attribute('href')
                        text = a.text or ''
                        if not href:
                            continue
                        if should_consider_link(href, text):
                            candidates.append((href, text))
                    except Exception:
                        continue
                # rank: deeper URLs and longer text first
                candidates = sorted(candidates, key=lambda x: (url_depth(x[0]), len(x[1] or '')), reverse=True)
                candidates = candidates[: cfg.max_candidates_per_listing]

                # Visit job candidates
                per_listing_found = 0
                for href, _text in candidates:
                    try:
                        domain_budget.acquire(href)
                        driver.get(href)
                        _sleep(cfg.wait_js_job)
                        # Extract fields
                        title = None
                        for sel in TITLE_SELECTORS:
                            title = extract_text(driver, sel)
                            if title:
                                break
                        company = None
                        for sel in COMPANY_SELECTORS:
                            company = extract_text(driver, sel)
                            if company:
                                break
                        location = None
                        for sel in LOCATION_SELECTORS:
                            location = extract_text(driver, sel)
                            if location:
                                break
                        posted = None
                        for sel in POSTED_SELECTORS:
                            posted = extract_text(driver, sel)
                            if posted:
                                break
                        budget = None
                        for sel in BUDGET_SELECTORS:
                            budget = extract_text(driver, sel)
                            if budget:
                                break
                        desc = extract_description(driver)
                        canon = canonicalize(driver.current_url)

                        score = score_keywords(title or '', desc or '', cfg.keywords)
                        job = {
                            'title': title or 'Job Posting',
                            'company': company or (urlparse(canon).netloc or '').split(':')[0],
                            'location': location or 'Remote',
                            'date_posted': (posted or '')[:32],
                            'budget': budget or '',
                            'description': desc,
                            'url': canon,
                            'platform': (urlparse(canon).netloc or '').lower(),
                            'source_listing': listing_url,
                            'crawled_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                            'lead_score': score,
                        }

                        # Dedupe: by URL then by title+company+date
                        exists_id = None
                        if db and hasattr(db, 'job_exists_by_url'):
                            exists_id = db.job_exists_by_url(job['url'])
                        if not exists_id and db and hasattr(db, 'job_exists_by_title_company_date'):
                            exists_id = db.job_exists_by_title_company_date(job['title'], job['company'], job['date_posted'])

                        if exists_id and db:
                            db.update_job_last_seen(exists_id)
                            try:
                                db.update_job_extra(exists_id, source_listing=listing_url, crawled_at=job['crawled_at'], lead_score=job['lead_score'])
                            except Exception:
                                pass
                        else:
                            if db:
                                try:
                                    jid = db.insert_job(job)
                                    try:
                                        db.update_job_extra(jid, source_listing=listing_url, crawled_at=job['crawled_at'], lead_score=job['lead_score'])
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                            results.append(job)
                            per_listing_found += 1
                    except WebDriverException as we:
                        # Skip bad candidate
                        continue
                    except Exception:
                        continue

                log['found_count'] = per_listing_found
                logs.append(log)
                if db and hasattr(db, 'log_crawl'):
                    db.log_crawl(log['domain'], listing_url, 'ok', per_listing_found, None, log['started_at'], time.strftime('%Y-%m-%dT%H:%M:%S'))

            except Exception as e:
                log['status'] = 'error'
                log['error_message'] = str(e)
                logs.append(log)
                if db and hasattr(db, 'log_crawl'):
                    db.log_crawl(log['domain'], listing_url, 'error', 0, log['error_message'], log['started_at'], time.strftime('%Y-%m-%dT%H:%M:%S'))
            finally:
                log['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')

        return {
            'results': results,
            'logs': logs,
            'total_found': sum(l.get('found_count', 0) for l in logs),
        }
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Selenium-based job crawler (MVP)')
    parser.add_argument('--urls', help='Path to file with listing URLs (one per line) or comma/newline-separated string')
    parser.add_argument('--keywords', help='Comma-separated keywords for scoring', default='')
    parser.add_argument('--override-robots', action='store_true', help='Override robots.txt (not recommended)')
    parser.add_argument('--wait-listing', type=float, default=2.0, help='Seconds to wait on listing page (1-3s recommended)')
    parser.add_argument('--wait-job', type=float, default=1.0, help='Seconds to wait on job page')
    parser.add_argument('--max-candidates', type=int, default=15)
    parser.add_argument('--per-domain-delay', type=float, default=2.0)
    parser.add_argument('--max-pages-per-domain', type=int, default=30)
    args = parser.parse_args()

    # Prepare URLs
    urls: List[str] = []
    if args.urls and os.path.exists(args.urls):
        with open(args.urls, 'r', encoding='utf-8') as f:
            urls = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
    elif args.urls:
        urls = [u.strip() for u in re.split(r'[\n,]', args.urls) if u.strip()]
    else:
        print('Provide --urls')
        return 1

    keywords = [k.strip() for k in (args.keywords or '').split(',') if k.strip()]
    cfg = SeleniumCrawlerConfig(
        wait_js_listing_min=max(1.0, min(3.0, args.wait_listing)),
        wait_js_listing_max=max(1.0, min(3.0, args.wait_listing)),
        wait_js_job=max(0.2, args.wait_job),
        max_candidates_per_listing=max(1, args.max_candidates),
        per_domain_delay=max(0.0, args.per_domain_delay),
        max_pages_per_domain=max(1, args.max_pages_per_domain),
        override_robots=bool(args.override_robots),
        keywords=keywords or None,
    )

    # Use DB if available
    try:
        db = JobDatabase('business_leads.db')
    except Exception:
        db = None

    out = crawl_listings(urls, cfg, db)
    print(f"Crawl complete. Found: {out.get('total_found')}\nLogs: {len(out.get('logs', []))}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
