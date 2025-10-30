"""Lead/contact extraction utilities for jobs.

Tier 2 implementation:
- Extract emails from job description and posting page/contact page
- Heuristically guess emails from company domain and names
- No external paid APIs
- No SMTP verification by default (can be added later)
"""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging
import dns.resolver  # type: ignore
from functools import lru_cache

import config

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DOMAIN_REGEX = re.compile(r"\b([a-z0-9-]+\.[a-z]{2,}(?:\.[a-z]{2,})?)\b", re.IGNORECASE)

# platform domains to ignore when inferring company domain
PLATFORM_DOMAINS = {
    'indeed.com','linkedin.com','glassdoor.com','remoteok.com','weworkremotely.com',
    'monster.com','dice.com','simplyhired.com','ziprecruiter.com','wellfound.com','angel.co','angellist.com'
}

HEADERS = {
    'User-Agent': config.USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def extract_emails_from_text(text: str) -> Set[str]:
    if not text:
        return set()
    emails = set(m.group(0).lower() for m in EMAIL_REGEX.finditer(text))
    # Filter obvious non-personal addresses? Keep generic like jobs@, careers@
    return emails


def get_domain_from_url(url: str) -> Optional[str]:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc or None
    except Exception:
        return None


def is_platform_domain(domain: str) -> bool:
    if not domain:
        return False
    return any(domain == d or domain.endswith('.' + d) for d in PLATFORM_DOMAINS)


def http_get(url: str, timeout: int = 12) -> Optional[str]:
    try:
        proxies = {'http': config.PROXY_URL, 'https': config.PROXY_URL} if getattr(config, 'PROXY_URL', '') else None
        resp = requests.get(url, headers=HEADERS, timeout=timeout, proxies=proxies, allow_redirects=True)
        if resp.status_code >= 200 and resp.status_code < 300:
            return resp.text
        return None
    except Exception as e:
        logging.debug(f"http_get failed for {url}: {e}")
        return None


def http_get_cached(cache: Optional[dict], url: str, timeout: int = 12) -> Optional[str]:
    if cache is None:
        return http_get(url, timeout=timeout)
    if url in cache:
        return cache[url]
    html = http_get(url, timeout=timeout)
    cache[url] = html
    return html


def find_contact_page_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    links = []
    for a in soup.find_all('a', href=True):
        text = (a.get_text() or '').strip().lower()
        href = a['href']
        if any(k in text for k in ['contact', 'about', 'team', 'careers']) or 'mailto:' in href:
            if href.startswith('mailto:'):
                links.append(href)
            else:
                links.append(urljoin(base_url, href))
    return links[:10]


def guess_company_domain(job: Dict, soup: Optional[BeautifulSoup], page_url: str) -> Optional[str]:
    # 1) from job.url if not a platform domain
    dom = get_domain_from_url(page_url)
    if dom and not is_platform_domain(dom):
        return dom
    # 2) from visible emails on page (prefer non-platform domains)
    if soup:
        text = soup.get_text(" ", strip=True)
        emails = extract_emails_from_text(text)
        domains = {get_domain_from_url('http://' + e.split('@')[-1]) for e in emails}
        domains = {d for d in domains if d and not is_platform_domain(d)}
        if domains:
            # pick the most frequent or first
            return sorted(domains)[0]
        # 3) from visible domains in anchors/text
        candidates: Set[str] = set()
        for a in soup.find_all('a', href=True):
            d = get_domain_from_url(a['href'])
            if d and not is_platform_domain(d):
                candidates.add(d)
        if candidates:
            return sorted(candidates)[0]
    return None


def generate_guessed_emails(first_name: Optional[str], last_name: Optional[str], domain: str) -> List[str]:
    # If no name, return generic inboxes
    if not first_name or not last_name:
        return [
            f"jobs@{domain}", f"careers@{domain}", f"hr@{domain}", f"recruiting@{domain}", f"talent@{domain}",
            f"hiring@{domain}", f"people@{domain}", f"info@{domain}", f"contact@{domain}"
        ]
    fn = re.sub(r"[^a-z]", "", first_name.lower())
    ln = re.sub(r"[^a-z]", "", last_name.lower())
    if not fn or not ln:
        return [f"jobs@{domain}", f"careers@{domain}", f"hr@{domain}"]
    patterns = [
        f"{fn}@{domain}",
        f"{ln}@{domain}",
        f"{fn}.{ln}@{domain}",
        f"{fn}{ln}@{domain}",
        f"{fn[0]}{ln}@{domain}",
        f"{fn}{ln[0]}@{domain}",
        f"{fn}_{ln}@{domain}",
        f"{fn}-{ln}@{domain}",
        f"{fn[0]}.{ln}@{domain}",
    ]
    # Add generic inboxes too
    patterns += [f"jobs@{domain}", f"careers@{domain}", f"hr@{domain}"]
    # De-duplicate
    dedup: List[str] = []
    seen: Set[str] = set()
    for p in patterns:
        if p not in seen:
            dedup.append(p)
            seen.add(p)
    return dedup


def is_generic_inbox(email: str) -> bool:
    local = email.split('@', 1)[0]
    return local in {
        'jobs','careers','hr','recruiting','talent','hiring','people','info','contact','hello','team','support'
    }


@lru_cache(maxsize=512)
def check_mx(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except Exception:
        return False


def score_contact(email: str, meta: Dict, mx_ok: Optional[bool]) -> float:
    # Base score by type/source
    base = 0.0
    src = meta.get('source') or ''
    typ = meta.get('type') or 'extracted'
    if typ == 'guessed':
        base = 0.45
    else:
        # extracted
        if src == 'mailto':
            base = 0.95
        elif src == 'description':
            base = 0.90
        elif src == 'posting_page':
            base = 0.85
        elif src == 'contact_page':
            base = 0.80
        else:
            base = 0.75

    # Penalize generic inboxes a bit
    if is_generic_inbox(email):
        base -= 0.15

    # MX presence small boost
    if mx_ok is True:
        base += 0.05
    elif mx_ok is False:
        base -= 0.10

    # Clamp
    return max(0.0, min(1.0, base))


def find_contacts_for_job(job: Dict, verify_mx: bool = False, fetch_cache: Optional[dict] = None) -> Dict:
    """Find contacts for a job: extracted emails + guessed emails from domain.

    Returns dict with keys: emails (list), sources (mapping), company_domain (str), guessed (list)
    """
    emails: Set[str] = set()
    sources: Dict[str, Dict] = {}

    # 1) Extract from description
    desc_emails = extract_emails_from_text(job.get('description', '') or '')
    for e in desc_emails:
        emails.add(e)
        sources[e] = {'source': 'description', 'verified': False, 'type': 'extracted'}

    # 2) Fetch posting page
    url = job.get('url') or ''
    html = http_get_cached(fetch_cache, url) if url else None
    soup = BeautifulSoup(html, 'lxml') if html else None

    page_domain = guess_company_domain(job, soup, url) if url else None

    # Extract from posting page text and mailto links
    if soup:
        text = soup.get_text(" ", strip=True)
        page_emails = extract_emails_from_text(text)
        for e in page_emails:
            if e not in emails:
                emails.add(e)
                sources[e] = {'source': 'posting_page', 'verified': False, 'type': 'extracted'}
        # mailto
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().startswith('mailto:'):
                e = href.split(':',1)[1].split('?')[0].strip().lower()
                if EMAIL_REGEX.fullmatch(e):
                    emails.add(e)
                    sources[e] = {'source': 'mailto', 'verified': False, 'type': 'extracted'}

        # Try a few contact-like pages
        for link in find_contact_page_links(soup, url):
            if link.startswith('mailto:'):
                continue
            sub_html = http_get_cached(fetch_cache, link)
            if not sub_html:
                continue
            sub_soup = BeautifulSoup(sub_html, 'lxml')
            sub_text = sub_soup.get_text(" ", strip=True)
            sub_emails = extract_emails_from_text(sub_text)
            for e in sub_emails:
                if e not in emails:
                    emails.add(e)
                    sources[e] = {'source': 'contact_page', 'verified': False, 'type': 'extracted'}

    # 3) Guess from company domain and names
    domain = page_domain
    if not domain:
        # fallback: try parse from any extracted email's domain if non-platform
        for e in list(emails):
            d = e.split('@')[-1]
            if d and not is_platform_domain(d):
                domain = d
                break

    guessed: List[str] = []
    if domain and not is_platform_domain(domain):
        # names if available
        poster_name = job.get('poster_name') or ''
        first_name, last_name = None, None
        if poster_name:
            parts = [p for p in re.split(r"\s+", poster_name.strip()) if p]
            if len(parts) >= 2:
                first_name, last_name = parts[0], parts[-1]
        guessed = generate_guessed_emails(first_name, last_name, domain)
        for e in guessed:
            if e not in emails:
                sources[e] = {'source': 'pattern', 'verified': False, 'type': 'guessed'}

    all_emails = sorted(set(list(emails) + guessed))

    # Optional domain MX verification
    mx_ok: Optional[bool] = None
    if verify_mx and domain:
        mx_ok = check_mx(domain)

    # Attach confidence scores
    confidences: Dict[str, float] = {}
    for e in all_emails:
        confidences[e] = score_contact(e, sources.get(e, {}), mx_ok)

    # Sort by confidence desc, then prefer extracted over guessed
    def sort_key(e: str):
        t = sources.get(e, {}).get('type', 'extracted')
        return (-confidences.get(e, 0.0), 0 if t == 'extracted' else 1, e)
    all_emails.sort(key=sort_key)

    return {
        'emails': all_emails,
        'sources': sources,
        'company_domain': domain,
        'guessed': guessed,
        'mx_ok': mx_ok,
        'confidence': confidences,
    }
