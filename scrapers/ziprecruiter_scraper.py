"""ZipRecruiter job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from scrapers.base_scraper import JobScraper
import config


class ZipRecruiterScraper(JobScraper):
    """Scraper for ZipRecruiter.com"""
    
    BASE_URL = "https://www.ziprecruiter.com"
    
    def __init__(self):
        super().__init__(use_selenium=True)
        
    def build_search_url(self, filters: Dict) -> str:
        """Build ZipRecruiter search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        keywords = quote(filters.get('keywords', ''))
        location = quote(filters.get('location', ''))
        
        url = f"{self.BASE_URL}/jobs-search?search={keywords}&location={location}"
        
        # Remote filter
        if filters.get('remote', False):
            url += "&refine_by_location_type=only_remote"
            
        return url
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from ZipRecruiter.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for page in range(filters.get('max_pages', config.MAX_PAGES)):
            url = self.build_search_url(filters)
            if page > 0:
                url += f"&page={page + 1}"
                
            print(f"Scraping ZipRecruiter page {page + 1}...")
            
            html = self.get_page(url, wait_element=(By.CLASS_NAME, 'job_result'))
            
            if not html:
                break
                
            self.scroll_page(scrolls=3)
            
            if self.driver:
                html = self.driver.page_source
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='job_result')
            
            if not job_cards:
                job_cards = soup.find_all('article', {'data-test': 'job-card'})
                
            for card in job_cards:
                job = self.parse_job_card(card)
                if job:
                    jobs.append(job)
                    
            self.delay()
            
        return jobs
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse ZipRecruiter job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'ZipRecruiter',
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'description': '',
                'url': '',
                'remote': False
            }
            
            # Title and URL
            title_elem = card.find('h2', class_='title')
            if not title_elem:
                title_elem = card.find('a', {'data-test': 'job-link'})
                
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link:
                    job['title'] = self.clean_text(link.get_text())
                    job['url'] = link.get('href', '')
                    if job['url'] and not job['url'].startswith('http'):
                        job['url'] = self.BASE_URL + job['url']
                        
            # Company
            company_elem = card.find('a', class_='t_org_link')
            if not company_elem:
                company_elem = card.find('span', {'data-test': 'job-company'})
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Location
            location_elem = card.find('p', class_='location')
            if not location_elem:
                location_elem = card.find('span', {'data-test': 'job-location'})
            if location_elem:
                location_text = self.clean_text(location_elem.get_text())
                job['location'] = location_text
                if 'remote' in location_text.lower():
                    job['remote'] = True
                    
            # Check for remote badge
            remote_badge = card.find('span', class_='remote_label')
            if remote_badge:
                job['remote'] = True
                
            # Salary
            salary_elem = card.find('span', class_='job_salary')
            if not salary_elem:
                salary_elem = card.find('p', class_='compensation')
            if salary_elem:
                job['salary'] = self.clean_text(salary_elem.get_text())
                
            # Description
            desc_elem = card.find('p', class_='job_snippet')
            if desc_elem:
                job['description'] = self.clean_text(desc_elem.get_text())
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing ZipRecruiter job card: {e}")
            return None
