"""Glassdoor scraper using Playwright with stealth support."""
from typing import List, Dict
from urllib.parse import quote
import asyncio
import time
from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError as PlaywrightTimeout
from scrapers.playwright_scraper import PlaywrightScraper
import config


class GlassdoorPlaywrightScraper(PlaywrightScraper):
    BASE_URL = "https://www.glassdoor.com"

    def build_search_url(self, filters: Dict) -> str:
        keywords = quote(filters.get('keywords', '') or '')
        location = quote(filters.get('location', '') or '')
        url = f"{self.BASE_URL}/Job/jobs.htm?sc.keyword={keywords}"
        if location:
            url += f"&locT=C&locId={location}"
        if filters.get('remote', False):
            url += "&remoteWorkType=1"
        return url

    async def _accept_cookies(self):
        if not self.page:
            return
        selectors = [
            'button[aria-label="Accept All"]',
            'button#onetrust-accept-btn-handler',
            'button[aria-label="Accept"]',
            'button:has-text("Accept All")',
            'button:has-text("Accept")',
        ]
        for sel in selectors:
            try:
                btn = await self.page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(0.2)
                    return
            except Exception:
                continue

    async def _close_popups(self):
        if not self.page:
            return
        selectors = [
            'button[aria-label="Dismiss"]',
            'button[aria-label="Close"]',
            'button[class*="CloseButton"]',
            'div.modal button.close'
        ]
        for sel in selectors:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    await el.click()
                    await asyncio.sleep(0.2)
            except Exception:
                continue

    async def _dismiss_login_wall(self):
        if not self.page:
            return
        selectors = [
            'button[aria-label="Dismiss"]',
            'button[aria-label="Close"]',
            'button[class*="CloseButton"]',
            'button:has-text("No thanks")',
            'button:has-text("Maybe later")',
        ]
        for sel in selectors:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    await el.click()
                    await asyncio.sleep(0.2)
            except Exception:
                continue

    async def _wait_for_any(self, selectors: List[str], timeout_ms: int = 25000):
        if not self.page:
            return False
        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            for sel in selectors:
                try:
                    elems = await self.page.query_selector_all(sel)
                    if elems:
                        return True
                except Exception:
                    pass
            await asyncio.sleep(0.3)
        return False

    async def scrape_jobs_async(self, filters: Dict) -> List[Dict]:
        jobs: List[Dict] = []
        max_pages = filters.get('max_pages', config.MAX_PAGES)

        for page_idx in range(max_pages):
            url = self.build_search_url(filters)
            if page_idx > 0:
                url += f"&p={page_idx + 1}"

            print(f"[Playwright] Scraping Glassdoor page {page_idx + 1}...")
            ok = await self.goto_page(url, wait_until='networkidle')
            if not ok:
                break

            # Handle consent and popups
            await self._accept_cookies()
            await self._close_popups()
            await self._dismiss_login_wall()

            # Wait for listings
            listing_selectors = [
                'li.react-job-listing',
                'div[data-test="jobListing"]',
                'ul.jobs-search__results-list li',
                'a[data-test="job-link"]',
                'a[data-test="job-title"]'
            ]
            ok = await self._wait_for_any(listing_selectors, timeout_ms=30000)
            if not ok:
                # try a small wait and another scroll in case of late hydration
                await asyncio.sleep(2)
                await self.scroll_page(scrolls=2)

            # Scroll to load more
            await self.scroll_page(scrolls=5)

            html = await self.get_html()
            soup = BeautifulSoup(html, 'html.parser')

            cards = soup.find_all('li', class_='react-job-listing')
            if not cards:
                cards = soup.find_all('div', {'data-test': 'jobListing'})

            for card in cards:
                job = {
                    'platform': 'Glassdoor',
                    'title': '',
                    'company': '',
                    'location': '',
                    'salary': '',
                    'description': '',
                    'url': '',
                    'remote': False
                }

                title_elem = card.find('a', class_='job-title') or card.find('a', {'data-test': 'job-link'})
                if title_elem:
                    job['title'] = ' '.join(title_elem.get_text(strip=True).split())
                    href = title_elem.get('href', '')
                    job['url'] = href if href.startswith('http') else f"{self.BASE_URL}{href}"

                company_elem = card.find('div', class_='employer-name') or card.find('span', {'data-test': 'employer-name'})
                if company_elem:
                    job['company'] = ' '.join(company_elem.get_text(strip=True).split())

                location_elem = card.find('div', class_='location') or card.find('span', {'data-test': 'emp-location'})
                if location_elem:
                    loc = ' '.join(location_elem.get_text(strip=True).split())
                    job['location'] = loc
                    if 'remote' in loc.lower():
                        job['remote'] = True

                salary_elem = card.find('div', class_='salary-estimate')
                if salary_elem:
                    job['salary'] = ' '.join(salary_elem.get_text(strip=True).split())

                if job['title']:
                    jobs.append(job)

            await asyncio.sleep(max(0.1, config.REQUEST_DELAY))

        await self.close_browser()
        return jobs
