"""WeWorkRemotely job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import JobScraper
import config


class WeWorkRemotelyScraper(JobScraper):
    """Scraper for WeWorkRemotely.com"""
    
    BASE_URL = "https://weworkremotely.com"
    
    def __init__(self):
        super().__init__(use_selenium=False)
        
    def build_search_url(self, filters: Dict) -> str:
        """Build WeWorkRemotely search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        # WeWorkRemotely has categories instead of search
        category = filters.get('category', 'remote-jobs')
        return f"{self.BASE_URL}/{category}"
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from WeWorkRemotely.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs: List[Dict] = []
        
        # Try different categories
        categories = ['remote-jobs', 'categories/remote-programming-jobs', 
                      'categories/remote-devops-sysadmin-jobs']
        
        for category in categories[:filters.get('max_pages', 1)]:
            url = f"{self.BASE_URL}/{category}"
            print(f"Scraping WeWorkRemotely: {category}...")
            html = self.get_page(url)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            
            # WWR jobs are within sections with class 'jobs'. Each section contains multiple lists.
            sections = soup.select('section.jobs')
            for section in sections:
                # Each job anchor links to /remote-jobs/... Use that to find real jobs
                anchors = section.select('a[href*="/remote-jobs/"]')
                for a in anchors:
                    # Skip non-job actions like Post a Job
                    href = a.get('href', '')
                    if '/remote-jobs/new' in href or '/remote-jobs/all-jobs' in href:
                        continue
                    # Build job object by inspecting anchor subtree
                    title_elem = a.select_one('span.title')
                    company_elem = a.select_one('span.company')
                    region_elem = a.select_one('span.region')
                    title = self.clean_text(title_elem.get_text() if title_elem else a.get_text())
                    company = self.clean_text(company_elem.get_text() if company_elem else '')
                    location = self.clean_text(region_elem.get_text() if region_elem else 'Remote')
                    job = {
                        'platform': 'WeWorkRemotely',
                        'title': title,
                        'company': company,
                        'location': location or 'Remote',
                        'salary': '',
                        'description': '',
                        'url': self.BASE_URL + href if href.startswith('/') else href,
                        'remote': True
                    }
                    # Keyword filter if provided
                    keywords = (filters.get('keywords') or '').lower()
                    if not keywords or (keywords in job['title'].lower()) or (keywords in job['company'].lower()):
                        jobs.append(job)
            self.delay()
        return jobs
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse WeWorkRemotely job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'WeWorkRemotely',
                'title': '',
                'company': '',
                'location': 'Remote',
                'salary': '',
                'description': '',
                'url': '',
                'remote': True
            }
            
            # Robust parsing: card may be <li> or nested inside anchor
            a = card.find('a', href=True) if card else None
            if a and '/remote-jobs/' in a.get('href', ''):
                title_elem = a.select_one('span.title')
                company_elem = a.select_one('span.company')
                region_elem = a.select_one('span.region')
            else:
                title_elem = card.find('span', class_='title')
                company_elem = card.find('span', class_='company')
                region_elem = card.find('span', class_='region')
            if title_elem:
                job['title'] = self.clean_text(title_elem.get_text())
            if a:
                href = a.get('href', '')
                if href:
                    job['url'] = self.BASE_URL + href if href.startswith('/') else href
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
            if region_elem:
                job['location'] = self.clean_text(region_elem.get_text()) or 'Remote'
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing WeWorkRemotely job card: {e}")
            return None
