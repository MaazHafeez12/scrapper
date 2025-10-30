"""SimplyHired job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from scrapers.base_scraper import JobScraper
import config


class SimplyHiredScraper(JobScraper):
    """Scraper for SimplyHired.com"""
    
    BASE_URL = "https://www.simplyhired.com"
    
    def __init__(self):
        super().__init__(use_selenium=True)
        
    def build_search_url(self, filters: Dict) -> str:
        """Build SimplyHired search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        keywords = quote(filters.get('keywords', ''))
        location = quote(filters.get('location', ''))
        
        url = f"{self.BASE_URL}/search?q={keywords}&l={location}"
        
        # Job type
        job_type = filters.get('job_type', '')
        if job_type:
            type_map = {
                'fulltime': 'fulltime',
                'parttime': 'parttime',
                'contract': 'contract'
            }
            if job_type.lower() in type_map:
                url += f"&jt={type_map[job_type.lower()]}"
                
        return url
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from SimplyHired.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for page in range(filters.get('max_pages', config.MAX_PAGES)):
            url = self.build_search_url(filters)
            if page > 0:
                url += f"&pn={page}"
                
            print(f"Scraping SimplyHired page {page + 1}...")
            
            html = self.get_page(url, wait_element=(By.CLASS_NAME, 'SerpJob-jobCard'))
            
            if not html:
                break
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='SerpJob-jobCard')
            
            if not job_cards:
                job_cards = soup.find_all('article')
                
            for card in job_cards:
                job = self.parse_job_card(card)
                if job:
                    jobs.append(job)
                    
            self.delay()
            
        return jobs
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse SimplyHired job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'SimplyHired',
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'description': '',
                'url': '',
                'remote': False
            }
            
            # Title and URL
            title_elem = card.find('h3', class_='jobposting-title')
            if not title_elem:
                title_elem = card.find('a', class_='SerpJob-link')
                
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link:
                    job['title'] = self.clean_text(link.get_text())
                    job['url'] = link.get('href', '')
                    if job['url'] and not job['url'].startswith('http'):
                        job['url'] = self.BASE_URL + job['url']
                        
            # Company
            company_elem = card.find('span', class_='JobPosting-labelWithIcon')
            if not company_elem:
                company_elem = card.find('span', class_='jobposting-company')
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Location
            location_elem = card.find('span', class_='jobposting-location')
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job['location'] = location_text
                if 'remote' in location_text.lower():
                    job['remote'] = True
                    
            # Salary
            salary_elem = card.find('span', class_='jobposting-salary')
            if salary_elem:
                job['salary'] = self.clean_text(salary_elem.get_text())
                
            # Description
            desc_elem = card.find('p', class_='jobposting-snippet')
            if desc_elem:
                job['description'] = self.clean_text(desc_elem.get_text())
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing SimplyHired job card: {e}")
            return None
