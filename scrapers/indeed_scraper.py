"""Indeed job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from scrapers.base_scraper import JobScraper
import config
import time


class IndeedScraper(JobScraper):
    """Scraper for Indeed.com using Selenium for better reliability"""
    
    BASE_URL = "https://www.indeed.com"
    
    def __init__(self):
        super().__init__(use_selenium=True)  # Use Selenium for Indeed
    
    def build_search_url(self, filters: Dict) -> str:
        """Build Indeed search URL.
        
        Args:
            filters: Dictionary with keys: keywords, location, remote, job_type
        """
        keywords = quote(filters.get('keywords', ''))
        location = quote(filters.get('location', ''))
        
        url = f"{self.BASE_URL}/jobs?q={keywords}&l={location}"
        
        # Add remote filter
        if filters.get('remote', False):
            url += "&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
            
        # Add job type
        job_type = filters.get('job_type', '')
        if job_type:
            type_map = {
                'fulltime': 'fulltime',
                'parttime': 'parttime',
                'contract': 'contract',
                'internship': 'internship'
            }
            if job_type.lower() in type_map:
                url += f"&jt={type_map[job_type.lower()]}"
                
        return url
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from Indeed using Selenium.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for page in range(filters.get('max_pages', config.MAX_PAGES)):
            url = self.build_search_url(filters)
            if page > 0:
                url += f"&start={page * 10}"
                
            print(f"Scraping Indeed page {page + 1}...")
            
            # Wait for job listings to load
            html = self.get_page(url, wait_element=(By.CLASS_NAME, 'job_seen_beacon'))
            
            if not html:
                break
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find job cards with multiple selectors
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            if not job_cards:
                job_cards = soup.find_all('td', class_='resultContent')
                
            if not job_cards:
                # Try using Selenium directly
                job_cards = self._get_jobs_with_selenium()
                
            for card in job_cards:
                job = self.parse_job_card(card)
                if job:
                    jobs.append(job)
                    
            self.delay()
            
        return jobs
        
    def _get_jobs_with_selenium(self) -> List:
        """Get job cards directly using Selenium when BeautifulSoup fails.
        
        Returns:
            List of job card elements or BeautifulSoup objects
        """
        if not self.driver:
            return []
            
        try:
            # Wait for job cards to load
            job_elements = self.get_elements(By.CSS_SELECTOR, 'div.job_seen_beacon, td.resultContent')
            
            # Convert to BeautifulSoup for consistent parsing
            html_cards = []
            for elem in job_elements:
                soup = BeautifulSoup(elem.get_attribute('outerHTML'), 'html.parser')
                html_cards.append(soup)
                
            return html_cards
        except Exception as e:
            print(f"Error getting jobs with Selenium: {e}")
            return []
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse Indeed job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'Indeed',
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'description': '',
                'url': '',
                'remote': False
            }
            
            # Title and URL
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                title_elem = card.find('a', class_='jcs-JobTitle')
                
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link:
                    job['title'] = self.clean_text(link.get_text())
                    job['url'] = self.BASE_URL + link.get('href', '')
                    
            # Company
            company_elem = card.find('span', {'data-testid': 'company-name'})
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Location
            location_elem = card.find('div', {'data-testid': 'text-location'})
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job['location'] = location_text
                if 'remote' in location_text.lower():
                    job['remote'] = True
                    
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            if not salary_elem:
                salary_elem = card.find('span', class_='estimated-salary')
            if salary_elem:
                job['salary'] = self.clean_text(salary_elem.get_text())
                
            # Description snippet
            desc_elem = card.find('div', class_='job-snippet')
            if desc_elem:
                job['description'] = self.clean_text(desc_elem.get_text())
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing Indeed job card: {e}")
            return None
