"""AngelList (Wellfound) job scraper - Startup jobs."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from scrapers.base_scraper import JobScraper
import config


class AngelListScraper(JobScraper):
    """Scraper for AngelList/Wellfound - Startup jobs"""
    
    BASE_URL = "https://wellfound.com"
    
    def __init__(self):
        super().__init__(use_selenium=True)
        
    def build_search_url(self, filters: Dict) -> str:
        """Build AngelList search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        keywords = quote(filters.get('keywords', ''))
        
        url = f"{self.BASE_URL}/role/r/{keywords}"
        
        # Remote filter
        if filters.get('remote', False):
            url += "?remote=true"
            
        return url
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from AngelList/Wellfound.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        print(f"Scraping AngelList/Wellfound...")
        
        url = self.build_search_url(filters)
        
        html = self.get_page(url, wait_element=(By.CLASS_NAME, 'styles_component__UCLp3'))
        
        if not html:
            return jobs
            
        # Scroll multiple times for infinite scroll
        self.scroll_page(scrolls=filters.get('max_pages', config.MAX_PAGES) * 2)
        
        if self.driver:
            html = self.driver.page_source
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all('div', class_='styles_component__UCLp3')
        
        if not job_cards:
            job_cards = soup.find_all('div', {'data-test': 'JobSearchCard'})
            
        print(f"Found {len(job_cards)} job cards on AngelList")
        
        for card in job_cards[:filters.get('max_pages', config.MAX_PAGES) * 25]:
            job = self.parse_job_card(card)
            if job:
                jobs.append(job)
                
        return jobs
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse AngelList job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'AngelList',
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'description': '',
                'url': '',
                'remote': False
            }
            
            # Title and URL
            title_elem = card.find('h2')
            if not title_elem:
                title_elem = card.find('a', {'data-test': 'job-title'})
                
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link:
                    job['title'] = self.clean_text(link.get_text())
                    job['url'] = link.get('href', '')
                    if job['url'] and not job['url'].startswith('http'):
                        job['url'] = self.BASE_URL + job['url']
                        
            # Company
            company_elem = card.find('h3')
            if not company_elem:
                company_elem = card.find('a', class_='styles_company__')
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Location
            location_elem = card.find('span', class_='styles_location__')
            if not location_elem:
                # Look for text with location indicators
                text = card.get_text()
                if 'Remote' in text:
                    job['location'] = 'Remote'
                    job['remote'] = True
                elif 'San Francisco' in text:
                    job['location'] = 'San Francisco, CA'
                    
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job['location'] = location_text
                if 'remote' in location_text.lower():
                    job['remote'] = True
                    
            # Check for remote badge
            if card.find(string=lambda x: x and 'remote' in str(x).lower()):
                job['remote'] = True
                
            # Salary/Compensation
            salary_elem = card.find('span', class_='styles_compensation__')
            if salary_elem:
                job['salary'] = self.clean_text(salary_elem.get_text())
                
            # Tags as description
            tags = card.find_all('span', class_='styles_tag__')
            if tags:
                tag_texts = [self.clean_text(tag.get_text()) for tag in tags]
                job['description'] = ', '.join(tag_texts)
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing AngelList job card: {e}")
            return None
