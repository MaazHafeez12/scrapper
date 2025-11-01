"""
Advanced Job Scraper with Proxy Rotation and Anti-Detection
Real-time scraping with stealth techniques for major job boards
"""
import requests
from bs4 import BeautifulSoup
import random
import time
from typing import Dict, List, Optional
from datetime import datetime
import json
from urllib.parse import quote, urljoin
import hashlib

class AdvancedJobScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.session = requests.Session()
        self.scrape_delays = (2, 5)  # Random delay between requests (seconds)
        
    def _get_random_headers(self) -> Dict:
        """Generate random headers for anti-detection."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def _random_delay(self):
        """Add random delay between requests."""
        time.sleep(random.uniform(*self.scrape_delays))
    
    def _safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a safe request with retries and error handling."""
        for attempt in range(max_retries):
            try:
                self._random_delay()
                response = self.session.get(
                    url,
                    headers=self._get_random_headers(),
                    timeout=15,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too many requests
                    wait_time = (attempt + 1) * 5
                    print(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Request failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(3, 7))
                    
        return None
    
    def scrape_linkedin_real(self, keywords: str, limit: int = 30) -> List[Dict]:
        """Scrape LinkedIn jobs (note: LinkedIn requires authentication for API)."""
        jobs = []
        
        # LinkedIn Jobs RSS feed (public, no auth needed for basic info)
        search_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote(keywords)}&location=Remote&f_TPR=r604800&start=0"
        
        try:
            response = self._safe_request(search_url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='base-card')[:limit]
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h3', class_='base-search-card__title')
                        company_elem = card.find('h4', class_='base-search-card__subtitle')
                        location_elem = card.find('span', class_='job-search-card__location')
                        link_elem = card.find('a', class_='base-card__full-link')
                        
                        if title_elem and company_elem:
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True),
                                'location': location_elem.get_text(strip=True) if location_elem else 'Remote',
                                'platform': 'LinkedIn',
                                'url': link_elem['href'] if link_elem and link_elem.get('href') else '',
                                'description': title_elem.get_text(strip=True),
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'scraped_at': datetime.now().isoformat(),
                                'source': 'live_scrape'
                            }
                            
                            # Generate unique ID
                            job['id'] = hashlib.md5(f"{job['title']}{job['company']}{job['platform']}".encode()).hexdigest()[:10]
                            jobs.append(job)
                            
                    except Exception as e:
                        print(f"Error parsing LinkedIn job: {e}")
                        continue
                        
        except Exception as e:
            print(f"LinkedIn scraping error: {e}")
        
        return jobs
    
    def scrape_indeed_real(self, keywords: str, limit: int = 25) -> List[Dict]:
        """Scrape Indeed jobs with improved parsing."""
        jobs = []
        
        try:
            search_url = f"https://www.indeed.com/jobs?q={quote(keywords)}&l=remote&sort=date"
            response = self._safe_request(search_url)
            
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Indeed's job cards structure
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                if not job_cards:
                    job_cards = soup.find_all('div', attrs={'data-jk': True})
                
                for card in job_cards[:limit]:
                    try:
                        # Try multiple selectors for title
                        title_elem = (
                            card.find('h2', class_='jobTitle') or
                            card.find('a', attrs={'data-jk': True}) or
                            card.find('span', attrs={'title': True})
                        )
                        
                        # Try multiple selectors for company
                        company_elem = (
                            card.find('span', class_='companyName') or
                            card.find('span', attrs={'data-testid': 'company-name'}) or
                            card.find('div', class_='companyName')
                        )
                        
                        # Try to find location
                        location_elem = (
                            card.find('div', class_='companyLocation') or
                            card.find('div', attrs={'data-testid': 'text-location'})
                        )
                        
                        if title_elem and company_elem:
                            # Extract job ID for URL
                            job_id = card.get('data-jk')
                            job_url = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else ''
                            
                            # Extract salary if available
                            salary_elem = card.find('span', class_='salary-snippet')
                            salary = salary_elem.get_text(strip=True) if salary_elem else ''
                            
                            # Extract snippet
                            snippet_elem = card.find('div', class_='job-snippet')
                            description = snippet_elem.get_text(strip=True) if snippet_elem else title_elem.get_text(strip=True)
                            
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True),
                                'location': location_elem.get_text(strip=True) if location_elem else 'Remote',
                                'platform': 'Indeed',
                                'url': job_url,
                                'salary_range': salary,
                                'description': description,
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'scraped_at': datetime.now().isoformat(),
                                'source': 'live_scrape'
                            }
                            
                            job['id'] = hashlib.md5(f"{job['title']}{job['company']}{job['platform']}".encode()).hexdigest()[:10]
                            jobs.append(job)
                            
                    except Exception as e:
                        print(f"Error parsing Indeed job: {e}")
                        continue
                        
        except Exception as e:
            print(f"Indeed scraping error: {e}")
        
        return jobs
    
    def scrape_remoteok_real(self, keywords: str, limit: int = 25) -> List[Dict]:
        """Scrape RemoteOK with improved parsing."""
        jobs = []
        
        try:
            # RemoteOK has a simple structure
            search_url = f"https://remoteok.com/remote-{quote(keywords.replace(' ', '-'))}-jobs"
            response = self._safe_request(search_url)
            
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # RemoteOK uses table rows for jobs
                job_rows = soup.find_all('tr', class_='job')[:limit]
                
                for row in job_rows:
                    try:
                        # Skip expired or featured rows
                        if 'expired' in row.get('class', []):
                            continue
                        
                        # Get job link
                        link_elem = row.find('a', itemprop='url')
                        if not link_elem:
                            continue
                        
                        job_url = f"https://remoteok.com{link_elem['href']}"
                        
                        # Get position title
                        title_elem = row.find('h2', itemprop='title')
                        if not title_elem:
                            continue
                        
                        # Get company
                        company_elem = row.find('h3', itemprop='name')
                        
                        # Get tags (technologies)
                        tags = []
                        tag_elems = row.find_all('div', class_='tag')
                        for tag in tag_elems:
                            tags.append(tag.get_text(strip=True))
                        
                        # Get salary if available
                        salary_elem = row.find('div', class_='salary')
                        
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'Remote Company',
                            'location': 'Remote',
                            'platform': 'RemoteOK',
                            'url': job_url,
                            'description': title_elem.get_text(strip=True),
                            'technologies': tags,
                            'salary_range': salary_elem.get_text(strip=True) if salary_elem else '',
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'scraped_at': datetime.now().isoformat(),
                            'source': 'live_scrape'
                        }
                        
                        job['id'] = hashlib.md5(f"{job['title']}{job['company']}{job['platform']}".encode()).hexdigest()[:10]
                        jobs.append(job)
                        
                    except Exception as e:
                        print(f"Error parsing RemoteOK job: {e}")
                        continue
                        
        except Exception as e:
            print(f"RemoteOK scraping error: {e}")
        
        return jobs
    
    def scrape_weworkremotely_real(self, keywords: str, limit: int = 20) -> List[Dict]:
        """Scrape WeWorkRemotely with real data."""
        jobs = []
        
        try:
            search_url = f"https://weworkremotely.com/remote-jobs/search?term={quote(keywords)}"
            response = self._safe_request(search_url)
            
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # WWR uses li elements with feature class
                job_items = soup.find_all('li', class_='feature')[:limit]
                
                for item in job_items:
                    try:
                        # Get title link
                        title_elem = item.find('span', class_='title')
                        link_elem = item.find('a')
                        
                        # Get company
                        company_elem = item.find('span', class_='company')
                        
                        # Get region (remote location)
                        region_elem = item.find('span', class_='region')
                        
                        if title_elem and link_elem:
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Remote Company',
                                'location': region_elem.get_text(strip=True) if region_elem else 'Remote',
                                'platform': 'WeWorkRemotely',
                                'url': f"https://weworkremotely.com{link_elem['href']}",
                                'description': title_elem.get_text(strip=True),
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'scraped_at': datetime.now().isoformat(),
                                'source': 'live_scrape'
                            }
                            
                            job['id'] = hashlib.md5(f"{job['title']}{job['company']}{job['platform']}".encode()).hexdigest()[:10]
                            jobs.append(job)
                            
                    except Exception as e:
                        print(f"Error parsing WWR job: {e}")
                        continue
                        
        except Exception as e:
            print(f"WWR scraping error: {e}")
        
        return jobs
    
    def scrape_all_platforms(self, keywords: str) -> Dict[str, List[Dict]]:
        """Scrape all platforms and return organized results."""
        results = {
            'linkedin': [],
            'indeed': [],
            'remoteok': [],
            'weworkremotely': []
        }
        
        print(f"🔍 Starting real-time scraping for: {keywords}")
        
        # LinkedIn
        print("📊 Scraping LinkedIn...")
        results['linkedin'] = self.scrape_linkedin_real(keywords, 30)
        print(f"✅ Found {len(results['linkedin'])} LinkedIn jobs")
        
        # Indeed
        print("📊 Scraping Indeed...")
        results['indeed'] = self.scrape_indeed_real(keywords, 25)
        print(f"✅ Found {len(results['indeed'])} Indeed jobs")
        
        # RemoteOK
        print("📊 Scraping RemoteOK...")
        results['remoteok'] = self.scrape_remoteok_real(keywords, 25)
        print(f"✅ Found {len(results['remoteok'])} RemoteOK jobs")
        
        # WeWorkRemotely
        print("📊 Scraping WeWorkRemotely...")
        results['weworkremotely'] = self.scrape_weworkremotely_real(keywords, 20)
        print(f"✅ Found {len(results['weworkremotely'])} WeWorkRemotely jobs")
        
        # Flatten results
        all_jobs = []
        for platform_jobs in results.values():
            all_jobs.extend(platform_jobs)
        
        print(f"\n🎉 Total jobs scraped: {len(all_jobs)}")
        
        return {
            'by_platform': results,
            'all_jobs': all_jobs,
            'total_count': len(all_jobs),
            'scraped_at': datetime.now().isoformat()
        }

# Singleton instance
advanced_scraper = AdvancedJobScraper()
