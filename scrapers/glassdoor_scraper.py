"""Glassdoor job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from scrapers.base_scraper import JobScraper
import config
import time


class GlassdoorScraper(JobScraper):
    """Scraper for Glassdoor.com"""
    
    BASE_URL = "https://www.glassdoor.com"
    
    def __init__(self):
        super().__init__(use_selenium=True)  # Glassdoor requires JavaScript
        
    def build_search_url(self, filters: Dict) -> str:
        """Build Glassdoor search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        keywords = quote(filters.get('keywords', ''))
        location = quote(filters.get('location', ''))
        
        url = f"{self.BASE_URL}/Job/jobs.htm?sc.keyword={keywords}"
        
        if location:
            url += f"&locT=C&locId={location}"
            
        # Remote filter
        if filters.get('remote', False):
            url += "&remoteWorkType=1"
            
        return url
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from Glassdoor using Selenium.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for page in range(filters.get('max_pages', config.MAX_PAGES)):
            url = self.build_search_url(filters)
            if page > 0:
                url += f"&p={page + 1}"
                
            print(f"Scraping Glassdoor page {page + 1}...")
            
            # Load page first; handle consent/login walls before waiting for listings
            html = self.get_page(url, wait_element=(By.CSS_SELECTOR, 'body'), wait_time=20)
            
            if not html:
                break
            
            # Handle consent and popups that block listings
            self._accept_cookies()
            self._close_popups()
            self._dismiss_login_wall()
            
            # Try multiple selectors for resilience
            listing_selectors = [
                'li.react-job-listing',
                'div[data-test="jobListing"]',
                'ul.jobs-search__results-list li',
                'a[data-test="job-link"]',
                'a[data-test="job-title"]'
            ]
            # Wait progressively for any listing to appear
            self._wait_for_any(listing_selectors, timeout=25)
            
            # Scroll to load all jobs
            self.scroll_page(scrolls=5)
            
            # Get updated HTML after scrolling
            if self.driver:
                html = self.driver.page_source
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('li', class_='react-job-listing')
            if not job_cards:
                job_cards = soup.find_all('div', {'data-test': 'jobListing'})
                
            if not job_cards:
                # Fallback: get via Selenium elements then wrap into soup
                job_cards = self._get_jobs_with_selenium()
                
            for card in job_cards:
                job = self.parse_job_card(card)
                if job:
                    jobs.append(job)
                    
            self.delay()
            
        return jobs
        
    def _close_popups(self):
        """Close any popup overlays or modals on Glassdoor."""
        if not self.driver:
            return
            
        try:
            # Common Glassdoor popup close buttons
            close_selectors = [
                'button[class*="CloseButton"]',
                'button[aria-label="Close"]',
                'div.modal button.close',
                'svg[class*="SVGInline-svg CloseIcon"]',
                'button#close'  # generic fallback
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if close_btn.is_displayed():
                        close_btn.click()
                        time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error closing popups: {e}")
    
    def _accept_cookies(self):
        """Accept cookie banners if present to unblock listings."""
        if not self.driver:
            return
        selectors = [
            'button[aria-label="Accept All"]',
            'button[aria-label="Accept"]',
            'button:has-text("Accept All")',
            'button:has-text("Accept")',
            'button#onetrust-accept-btn-handler',
            'button[aria-label="OK"]'
        ]
        for sel in selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, sel) if ':' not in sel else []
                if btns:
                    for b in btns:
                        if b.is_displayed():
                            b.click(); time.sleep(0.5)
                            return
            except Exception:
                continue
    
    def _dismiss_login_wall(self):
        """Dismiss sign-in walls if they appear."""
        if not self.driver:
            return
        selectors = [
            'button[aria-label="Dismiss"]',
            'button[aria-label="Close"]',
            'button[class*="CloseButton"]'
        ]
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    el.click(); time.sleep(0.5)
            except Exception:
                continue
    
    def _wait_for_any(self, selectors: list, timeout: int = 20):
        """Wait until any of the selectors appears."""
        if not self.driver:
            return
        end = time.time() + timeout
        while time.time() < end:
            try:
                for sel in selectors:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        return
            except Exception:
                pass
            time.sleep(0.5)
            
    def _get_jobs_with_selenium(self) -> List:
        """Get job cards directly using Selenium."""
        if not self.driver:
            return []
            
        try:
            job_elements = self.get_elements(By.CSS_SELECTOR, 'li.react-job-listing, div[data-test="jobListing"]')
            
            html_cards = []
            for elem in job_elements:
                soup = BeautifulSoup(elem.get_attribute('outerHTML'), 'html.parser')
                html_cards.append(soup)
                
            return html_cards
        except Exception as e:
            print(f"Error getting jobs with Selenium: {e}")
            return []
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse Glassdoor job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
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
            
            # Title
            title_elem = card.find('a', class_='job-title')
            if not title_elem:
                title_elem = card.find('a', {'data-test': 'job-link'})
            if title_elem:
                job['title'] = self.clean_text(title_elem.get_text())
                job['url'] = self.BASE_URL + title_elem.get('href', '')
                
            # Company
            company_elem = card.find('div', class_='employer-name')
            if not company_elem:
                company_elem = card.find('span', {'data-test': 'employer-name'})
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Location
            location_elem = card.find('div', class_='location')
            if not location_elem:
                location_elem = card.find('span', {'data-test': 'emp-location'})
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job['location'] = location_text
                if 'remote' in location_text.lower():
                    job['remote'] = True
                    
            # Salary
            salary_elem = card.find('div', class_='salary-estimate')
            if salary_elem:
                job['salary'] = self.clean_text(salary_elem.get_text())
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing Glassdoor job card: {e}")
            return None
