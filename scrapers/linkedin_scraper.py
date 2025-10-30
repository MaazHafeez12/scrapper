"""LinkedIn job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from scrapers.base_scraper import JobScraper
import config
import time


class LinkedInScraper(JobScraper):
    """Scraper for LinkedIn Jobs"""
    
    BASE_URL = "https://www.linkedin.com"
    
    def __init__(self):
        super().__init__(use_selenium=True)  # LinkedIn often requires JS
        
    def build_search_url(self, filters: Dict) -> str:
        """Build LinkedIn search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        keywords = quote(filters.get('keywords', ''))
        location = quote(filters.get('location', ''))
        
        url = f"{self.BASE_URL}/jobs/search/?keywords={keywords}&location={location}"
        
        # Remote filter
        if filters.get('remote', False):
            url += "&f_WT=2"  # Remote filter
            
        # Job type
        job_type = filters.get('job_type', '')
        if job_type:
            type_map = {
                'fulltime': 'F',
                'parttime': 'P',
                'contract': 'C',
                'internship': 'I'
            }
            if job_type.lower() in type_map:
                url += f"&f_JT={type_map[job_type.lower()]}"
                
        return url
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from LinkedIn using Selenium.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for page in range(filters.get('max_pages', config.MAX_PAGES)):
            url = self.build_search_url(filters)
            if page > 0:
                url += f"&start={page * 25}"
                
            print(f"Scraping LinkedIn page {page + 1}...")
            
            # Wait for job listings to load
            html = self.get_page(url, wait_element=(By.CLASS_NAME, 'jobs-search-results__list'))
            
            if not html:
                break
            
            # Scroll to load more jobs (LinkedIn uses infinite scroll)
            self._scroll_and_load_jobs()
            
            # Get updated page source after scrolling
            if self.driver:
                html = self.driver.page_source
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='base-card')
            if not job_cards:
                job_cards = soup.find_all('li', class_='jobs-search-results__list-item')
                
            if not job_cards:
                # Try direct Selenium approach
                job_cards = self._get_jobs_with_selenium()
                
            for card in job_cards:
                job = self.parse_job_card(card)
                if job:
                    jobs.append(job)
                    
            self.delay()
            
        return jobs
        
    def _scroll_and_load_jobs(self):
        """Scroll the page to trigger loading of more jobs."""
        if not self.driver:
            return
            
        try:
            # Scroll multiple times to load all jobs
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
            # Try to click "See more jobs" button if it exists
            try:
                see_more = self.driver.find_element(By.CSS_SELECTOR, 'button.infinite-scroller__show-more-button')
                if see_more:
                    see_more.click()
                    time.sleep(2)
            except:
                pass
                
        except Exception as e:
            print(f"Error scrolling LinkedIn page: {e}")
            
    def _get_jobs_with_selenium(self) -> List:
        """Get job cards directly using Selenium."""
        if not self.driver:
            return []
            
        try:
            job_elements = self.get_elements(By.CSS_SELECTOR, 'div.base-card, li.jobs-search-results__list-item')
            
            html_cards = []
            for elem in job_elements:
                soup = BeautifulSoup(elem.get_attribute('outerHTML'), 'html.parser')
                html_cards.append(soup)
                
            return html_cards
        except Exception as e:
            print(f"Error getting jobs with Selenium: {e}")
            return []
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse LinkedIn job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'LinkedIn',
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'description': '',
                'url': '',
                'remote': False
            }
            
            # Title and URL
            title_elem = card.find('h3', class_='base-search-card__title')
            if not title_elem:
                title_elem = card.find('a', class_='base-card__full-link')
                
            if title_elem:
                if title_elem.name == 'a':
                    job['title'] = self.clean_text(title_elem.get_text())
                    job['url'] = title_elem.get('href', '')
                else:
                    link = title_elem.find_parent('a')
                    if link:
                        job['title'] = self.clean_text(title_elem.get_text())
                        job['url'] = link.get('href', '')
                        
            # Company
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            if not company_elem:
                company_elem = card.find('a', class_='hidden-nested-link')
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Location
            location_elem = card.find('span', class_='job-search-card__location')
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job['location'] = location_text
                if 'remote' in location_text.lower():
                    job['remote'] = True
                    
            # Check for remote badge
            if card.find('span', string=lambda x: x and 'remote' in x.lower()):
                job['remote'] = True
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing LinkedIn job card: {e}")
            return None
