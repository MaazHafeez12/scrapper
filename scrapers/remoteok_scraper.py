"""RemoteOK job scraper."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from scrapers.base_scraper import JobScraper
import config


class RemoteOKScraper(JobScraper):
    """Scraper for RemoteOK.com - focused on remote jobs"""
    
    BASE_URL = "https://remoteok.com"
    API_URL = "https://remoteok.com/api"
    
    def __init__(self):
        super().__init__(use_selenium=False)  # Prefer fast requests path
        
    def build_search_url(self, filters: Dict) -> str:
        """Build RemoteOK search URL.
        
        Args:
            filters: Dictionary with search filters
        """
        keywords = filters.get('keywords', '')
        
        if keywords:
            # RemoteOK uses tags/categories
            url = f"{self.BASE_URL}/remote-{quote(keywords.lower().replace(' ', '-'))}-jobs"
        else:
            url = f"{self.BASE_URL}/remote-jobs"
            
        return url
        
    def _fetch_api_jobs(self, filters: Dict) -> List[Dict]:
        """Fetch jobs using RemoteOK's public API.
        Returns list of normalized job dicts or empty list on failure."""
        try:
            text = self.get_page(self.API_URL)
            if not text:
                return []
            # API returns JSON array; sometimes first element is metadata
            import json
            data = json.loads(text)
            if isinstance(data, dict):
                posts = data.get('jobs') or data.get('data') or []
            else:
                # Filter out metadata records without 'position'
                posts = [row for row in data if isinstance(row, dict) and ('position' in row or 'id' in row)]
            jobs: List[Dict] = []
            keywords = (filters.get('keywords') or '').lower()
            max_items = filters.get('max_pages', config.MAX_PAGES) * 25
            for row in posts:
                title = row.get('position') or row.get('title') or ''
                company = row.get('company') or row.get('company_name') or ''
                if not title:
                    continue
                # Keyword filter if provided
                if keywords and (keywords not in (title or '').lower()) and (keywords not in (row.get('description') or '').lower()):
                    continue
                url = row.get('url') or row.get('apply_url') or ''
                if url and url.startswith('/'):
                    url = f"{self.BASE_URL}{url}"
                tags = row.get('tags') or []
                salary = row.get('salary') or ''
                job = {
                    'platform': 'RemoteOK',
                    'title': self.clean_text(title),
                    'company': self.clean_text(company),
                    'location': self.clean_text(row.get('location') or 'Remote'),
                    'salary': self.clean_text(salary),
                    'description': self.clean_text(', '.join(tags) or (row.get('description') or '')),
                    'url': url,
                    'remote': True
                }
                jobs.append(job)
                if len(jobs) >= max_items:
                    break
            return jobs
        except Exception as e:
            print(f"RemoteOK API parse error: {e}")
            return []
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from RemoteOK with API-first strategy and HTML fallback."""
        print("Scraping RemoteOK...")
        # Try API first (more stable than HTML which changes often)
        api_jobs = self._fetch_api_jobs(filters)
        if api_jobs:
            return api_jobs
        
        jobs: List[Dict] = []
        url = self.build_search_url(filters)
        html = self.get_page(url)
        if not html:
            return jobs
        
        soup = BeautifulSoup(html, 'html.parser')
        job_table = soup.find('table', id='jobsboard')
        if not job_table:
            return jobs
        
        # RemoteOK frequently injects placeholder rows; select rows with actual content
        rows = job_table.find_all('tr')
        max_jobs = filters.get('max_pages', config.MAX_PAGES) * 25
        for row in rows:
            cls = row.get('class') or []
            if 'placeholder' in cls:
                continue
            job = self.parse_job_card(row)
            if job:
                jobs.append(job)
                if len(jobs) >= max_jobs:
                    break
        return jobs
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse RemoteOK job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'RemoteOK',
                'title': '',
                'company': '',
                'location': 'Remote',
                'salary': '',
                'description': '',
                'url': '',
                'remote': True  # All RemoteOK jobs are remote
            }
            
            # Title and URL (support multiple layouts)
            title_elem = card.find('h2', itemprop='title') or card.find('h2')
            if title_elem:
                job['title'] = self.clean_text(title_elem.get_text())
            # URL can be in data-id or anchor
            job_id = card.get('data-id', '')
            if job_id:
                job['url'] = f"{self.BASE_URL}/job/{job_id}"
            else:
                a = card.find('a', href=True)
                if a and '/job/' in a['href']:
                    job['url'] = a['href'] if a['href'].startswith('http') else f"{self.BASE_URL}{a['href']}"
                
            # Company
            company_elem = card.find('h3', itemprop='name') or card.find('h3')
            if company_elem:
                job['company'] = self.clean_text(company_elem.get_text())
                
            # Salary
            salary_elem = card.find('div', class_='salary') or card.find('div', attrs={'class': lambda c: c and 'salary' in c})
            if salary_elem:
                job['salary'] = self.clean_text(salary_elem.get_text())
                
            # Tags (can be used as description)
            tags = card.find_all('div', class_='tag') or card.find_all('span', class_='tag')
            if tags:
                tag_texts = [self.clean_text(tag.get_text()) for tag in tags]
                job['description'] = ', '.join(tag_texts)
                
            return job if job['title'] else None
            
        except Exception as e:
            print(f"Error parsing RemoteOK job card: {e}")
            return None
