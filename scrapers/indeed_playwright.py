"""Indeed scraper using Playwright (Puppeteer-like approach)."""
from typing import List, Dict, Optional
from urllib.parse import quote
from bs4 import BeautifulSoup
import asyncio
from scrapers.playwright_scraper import PlaywrightScraper
import config


class IndeedPlaywrightScraper(PlaywrightScraper):
    """Scraper for Indeed.com using Playwright (Puppeteer alternative)"""
    
    BASE_URL = "https://www.indeed.com"
    
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
        
    async def scrape_jobs_async(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from Indeed using Playwright.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            await self.setup_browser()
            
            for page in range(filters.get('max_pages', config.MAX_PAGES)):
                url = self.build_search_url(filters)
                if page > 0:
                    url += f"&start={page * 10}"
                    
                print(f"Scraping Indeed page {page + 1} with Playwright...")
                
                # Navigate to page
                success = await self.goto_page(url)
                if not success:
                    break
                    
                # Wait for job listings to load
                await self.wait_for_selector('.job_seen_beacon', timeout=10000)
                
                # Scroll to load all jobs
                await self.scroll_page(scrolls=3)
                
                # Get page HTML
                html = await self.get_html()
                
                if not html:
                    break
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find job cards
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    job_cards = soup.find_all('td', class_='resultContent')
                    
                print(f"Found {len(job_cards)} job cards on page {page + 1}")
                    
                for card in job_cards:
                    job = self.parse_job_card(card)
                    if job:
                        jobs.append(job)
                        
                # Delay between pages
                await asyncio.sleep(config.REQUEST_DELAY)
                
        finally:
            await self.close_browser()
            
        return jobs
        
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse Indeed job card.
        
        Args:
            card: BeautifulSoup element
            
        Returns:
            Job dictionary
        """
        try:
            job = {
                'platform': 'Indeed (Playwright)',
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
            
    def clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        return ' '.join(text.strip().split())
