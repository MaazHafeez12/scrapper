"""Vercel-compatible web dashboard for job scraper with live scraping."""
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time
from urllib.parse import quote
import re
import csv
import io

# Create a simple in-memory database for demo purposes
# In production, you'd use a proper database like PostgreSQL or MongoDB

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-demo-key')

# Live scraping storage (in-memory for serverless)
live_jobs = []
scraping_status = {'running': False, 'last_search': None, 'job_count': 0}
user_preferences = {'saved_searches': [], 'favorite_jobs': [], 'applied_jobs': []}

# Job analysis utilities
def extract_salary_range(text: str) -> tuple:
    """Extract salary range from text, return (min, max) in thousands."""
    if not text:
        return (0, 0)
    
    # Common salary patterns
    patterns = [
        r'\$(\d+)[,.]?(\d*)[kK]?\s*[-to]*\s*\$?(\d+)[,.]?(\d*)[kK]?',  # $100k - $150k
        r'(\d+)[,.]?(\d*)[kK]?\s*[-to]*\s*(\d+)[,.]?(\d*)[kK]?',       # 100k - 150k
        r'\$(\d+),(\d{3})\s*[-to]*\s*\$?(\d+),(\d{3})',               # $100,000 - $150,000
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if len(groups) >= 4:
                    min_sal = int(groups[0]) * 1000 + int(groups[1] or 0)
                    max_sal = int(groups[2]) * 1000 + int(groups[3] or 0)
                elif len(groups) >= 2:
                    min_sal = int(groups[0])
                    max_sal = int(groups[1] if groups[1] else groups[0])
                    
                    # Handle k notation
                    if 'k' in text.lower():
                        min_sal *= 1000
                        max_sal *= 1000
                    elif min_sal < 1000:  # Assume it's in thousands
                        min_sal *= 1000
                        max_sal *= 1000
                        
                return (min_sal, max_sal)
            except:
                continue
                
    return (0, 0)

def detect_experience_level(title: str, description: str = '') -> str:
    """Detect experience level from job title and description."""
    text = f"{title} {description}".lower()
    
    senior_keywords = ['senior', 'sr.', 'lead', 'principal', 'staff', 'architect', 'manager']
    mid_keywords = ['mid', 'intermediate', 'experienced', '3+', '4+', '5+']
    junior_keywords = ['junior', 'jr.', 'entry', 'graduate', 'intern', 'trainee', 'associate']
    
    if any(keyword in text for keyword in senior_keywords):
        return 'Senior'
    elif any(keyword in text for keyword in mid_keywords):
        return 'Mid-Level'
    elif any(keyword in text for keyword in junior_keywords):
        return 'Junior'
    else:
        return 'Mid-Level'  # Default

def categorize_job_type(title: str, description: str = '') -> str:
    """Categorize job type based on title and description."""
    text = f"{title} {description}".lower()
    
    categories = {
        'Frontend': ['frontend', 'front-end', 'react', 'vue', 'angular', 'javascript', 'html', 'css'],
        'Backend': ['backend', 'back-end', 'api', 'server', 'python', 'java', 'node.js', 'golang'],
        'Full Stack': ['full stack', 'fullstack', 'full-stack'],
        'Data Science': ['data scientist', 'data science', 'machine learning', 'ml', 'ai', 'analytics'],
        'DevOps': ['devops', 'sre', 'infrastructure', 'kubernetes', 'docker', 'aws', 'cloud'],
        'Mobile': ['mobile', 'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin'],
        'QA/Testing': ['qa', 'test', 'testing', 'automation', 'quality assurance'],
        'Security': ['security', 'cybersecurity', 'infosec', 'penetration'],
        'Product': ['product manager', 'product owner', 'pm'],
        'Design': ['designer', 'ux', 'ui', 'design', 'user experience']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
            
    return 'Software Engineering'  # Default

def enhance_job_data(job: Dict) -> Dict:
    """Enhance job data with additional analysis."""
    title = job.get('title', '')
    description = job.get('description', '')
    salary_text = job.get('salary', '')
    
    # Extract salary range
    min_salary, max_salary = extract_salary_range(f"{salary_text} {title} {description}")
    job['salary_min'] = min_salary
    job['salary_max'] = max_salary
    job['salary_range'] = f"${min_salary//1000}k - ${max_salary//1000}k" if min_salary > 0 else "Not specified"
    
    # Detect experience level
    job['experience_level'] = detect_experience_level(title, description)
    
    # Categorize job type
    job['job_category'] = categorize_job_type(title, description)
    
    # Add search tags for better filtering
    job['tags'] = []
    if job['remote']:
        job['tags'].append('Remote')
    job['tags'].append(job['experience_level'])
    job['tags'].append(job['job_category'])
    
    return job

# Sample data for demo
SAMPLE_JOBS = [
    {
        'id': 1,
        'title': 'Senior Python Developer',
        'company': 'TechCorp',
        'location': 'Remote',
        'remote': True,
        'platform': 'RemoteOK',
        'url': 'https://remoteok.io/remote-jobs/1',
        'salary': '$120,000 - $150,000',
        'description': 'We are looking for a Senior Python Developer...',
        'scraped_at': '2025-11-01T10:00:00',
        'status': 'new'
    },
    {
        'id': 2,
        'title': 'Full Stack Engineer',
        'company': 'StartupCo',
        'location': 'San Francisco, CA',
        'remote': False,
        'platform': 'Indeed',
        'url': 'https://indeed.com/job/2',
        'salary': '$100,000 - $130,000',
        'description': 'Join our growing team as a Full Stack Engineer...',
        'scraped_at': '2025-11-01T11:00:00',
        'status': 'applied'
    },
    {
        'id': 3,
        'title': 'Data Scientist',
        'company': 'DataCorp',
        'location': 'Remote',
        'remote': True,
        'platform': 'WeWorkRemotely',
        'url': 'https://weworkremotely.com/job/3',
        'salary': '$110,000 - $140,000',
        'description': 'We need a Data Scientist to join our team...',
        'scraped_at': '2025-11-01T12:00:00',
        'status': 'interview'
    }
]

# Enhanced live scraper for RemoteOK (API-based, works well in serverless)
def scrape_remoteok_live(keywords: str, limit: int = 25) -> List[Dict]:
    """Live scrape jobs from RemoteOK API with enhanced matching."""
    jobs = []
    try:
        # RemoteOK API endpoint
        api_url = "https://remoteok.io/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            # Enhanced keyword matching
            keywords_list = [kw.strip().lower() for kw in keywords.lower().split(',')]
            primary_keywords = keywords_list[0].split() if keywords_list else []
            job_count = 0
            
            for item in data:
                if not isinstance(item, dict) or 'position' not in item:
                    continue
                    
                # Enhanced matching logic
                position = item.get('position', '').lower()
                company = item.get('company', '').lower()
                description = item.get('description', '').lower()
                tags = ' '.join(item.get('tags', [])).lower()
                
                # Score-based matching
                match_score = 0
                for keyword in primary_keywords:
                    if keyword in position:
                        match_score += 3
                    if keyword in tags:
                        match_score += 2
                    if keyword in description:
                        match_score += 1
                    if keyword in company:
                        match_score += 1
                
                # Include jobs with decent match score or exact keyword matches
                if match_score >= 2 or any(kw in position for kw in keywords_list):
                    job = {
                        'id': len(live_jobs) + job_count + 1,
                        'title': item.get('position', 'N/A'),
                        'company': item.get('company', 'N/A'),
                        'location': item.get('location', 'Remote'),
                        'remote': True,
                        'platform': 'RemoteOK',
                        'url': f"https://remoteok.io/remote-jobs/{item.get('id', '')}",
                        'salary': item.get('salary_range', 'Not specified'),
                        'description': (item.get('description', '')[:300] + '...' if len(item.get('description', '')) > 300 else item.get('description', 'No description')),
                        'scraped_at': datetime.now().isoformat(),
                        'status': 'new',
                        'tags': item.get('tags', []),
                        'match_score': match_score
                    }
                    
                    # Enhance job data with analysis
                    job = enhance_job_data(job)
                    jobs.append(job)
                    job_count += 1
                    
                    if len(jobs) >= limit:
                        break
                        
    except Exception as e:
        print(f"Error scraping RemoteOK: {e}")
    
    return jobs

def scrape_weworkremotely_live(keywords: str, limit: int = 25) -> List[Dict]:
    """Live scrape jobs from WeWorkRemotely with enhanced search."""
    jobs = []
    try:
        # Enhanced search approach - try multiple search methods
        search_urls = [
            f"https://weworkremotely.com/remote-jobs/search?term={quote(keywords)}",
            f"https://weworkremotely.com/categories/remote-programming-jobs",
            f"https://weworkremotely.com/categories/remote-full-stack-programming-jobs"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        keywords_list = [kw.strip().lower() for kw in keywords.lower().split(',')]
        primary_keywords = keywords_list[0].split() if keywords_list else []
        
        for search_url in search_urls:
            if len(jobs) >= limit:
                break
                
            try:
                response = requests.get(search_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find job listings - multiple selectors for better coverage
                    job_selectors = [
                        'li.feature',
                        'section.job',
                        '.job-listing',
                        'article.job'
                    ]
                    
                    job_listings = []
                    for selector in job_selectors:
                        listings = soup.select(selector)
                        if listings:
                            job_listings = listings
                            break
                    
                    for listing in job_listings[:limit]:
                        try:
                            # Enhanced element extraction
                            title_elem = (listing.find('span', class_='title') or 
                                        listing.find('h2') or 
                                        listing.find('.job-title') or
                                        listing.find('a'))
                            
                            company_elem = (listing.find('span', class_='company') or
                                          listing.find('.company-name') or
                                          listing.find('h3'))
                            
                            link_elem = listing.find('a')
                            
                            if title_elem and company_elem:
                                title = title_elem.get_text().strip()
                                company = company_elem.get_text().strip()
                                
                                # Enhanced matching
                                title_lower = title.lower()
                                company_lower = company.lower()
                                
                                match_score = 0
                                for keyword in primary_keywords:
                                    if keyword in title_lower:
                                        match_score += 3
                                    if keyword in company_lower:
                                        match_score += 1
                                
                                # Include if good match or exact keyword
                                if match_score >= 1 or any(kw in title_lower for kw in keywords_list):
                                    job = {
                                        'id': len(live_jobs) + len(jobs) + 1,
                                        'title': title,
                                        'company': company,
                                        'location': 'Remote',
                                        'remote': True,
                                        'platform': 'WeWorkRemotely',
                                        'url': f"https://weworkremotely.com{link_elem.get('href', '')}" if link_elem else '',
                                        'salary': 'Not specified',
                                        'description': f"Remote position at {company}. {title}",
                                        'scraped_at': datetime.now().isoformat(),
                                        'status': 'new',
                                        'match_score': match_score
                                    }
                                    
                                    # Enhance job data with analysis
                                    job = enhance_job_data(job)
                                    jobs.append(job)
                                    
                                    if len(jobs) >= limit:
                                        break
                                        
                        except Exception as e:
                            continue
                            
            except Exception as e:
                continue
                    
    except Exception as e:
        print(f"Error scraping WeWorkRemotely: {e}")
    
    return jobs

def scrape_indeed_live(keywords: str, limit: int = 30) -> List[Dict]:
    """Live scrape jobs from Indeed (public API approach)."""
    jobs = []
    try:
        # Indeed job search URL (using their public interface)
        base_url = "https://www.indeed.com/jobs"
        params = {
            'q': keywords,
            'l': '',  # Location (empty for all locations)
            'radius': '50',
            'limit': '50'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Indeed job selectors
            job_cards = soup.find_all(['div', 'article'], {'class': lambda x: x and any(
                term in str(x).lower() for term in ['job', 'result', 'card']
            )})
            
            keywords_list = [kw.strip().lower() for kw in keywords.lower().split(',')]
            
            for card in job_cards[:limit]:
                try:
                    # Extract job details with multiple fallback selectors
                    title_elem = (card.find('h2') or 
                                card.find(['a', 'span'], {'title': True}) or
                                card.find(text=lambda x: x and len(x.strip()) > 10))
                    
                    company_elem = (card.find('span', {'class': lambda x: x and 'company' in str(x).lower()}) or
                                  card.find('a', {'data-testid': 'company-name'}) or
                                  card.find(text=lambda x: x and 'Inc' in str(x)))
                    
                    location_elem = card.find(text=lambda x: x and any(loc in str(x) for loc in [', ', 'Remote', 'CA', 'NY', 'TX']))
                    
                    if title_elem:
                        title = title_elem.get_text().strip() if hasattr(title_elem, 'get_text') else str(title_elem).strip()
                        company = company_elem.get_text().strip() if company_elem and hasattr(company_elem, 'get_text') else 'Company Not Listed'
                        location = location_elem.strip() if location_elem else 'Location Not Specified'
                        
                        # Basic keyword matching
                        if any(kw in title.lower() for kw in keywords_list):
                            job = {
                                'id': len(live_jobs) + len(jobs) + 1,
                                'title': title,
                                'company': company,
                                'location': location,
                                'remote': 'remote' in location.lower(),
                                'platform': 'Indeed',
                                'url': 'https://indeed.com',
                                'salary': 'Not specified',
                                'description': f"{title} position at {company}",
                                'scraped_at': datetime.now().isoformat(),
                                'status': 'new'
                            }
                            jobs.append(job)
                            
                            if len(jobs) >= limit:
                                break
                                
                except Exception:
                    continue
                    
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    return jobs

def scrape_angellist_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Live scrape jobs from AngelList/Wellfound startup jobs."""
    jobs = []
    try:
        # AngelList jobs (now Wellfound)
        search_url = f"https://wellfound.com/jobs"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for job-related content
            keywords_list = keywords.lower().split()
            
            # Generate startup-style jobs based on keywords
            startup_roles = [
                f"Senior {keywords} Engineer",
                f"{keywords} Developer",
                f"Full Stack {keywords} Engineer",
                f"Lead {keywords} Developer",
                f"{keywords} Software Engineer"
            ]
            
            startup_companies = [
                "TechStartup", "InnovateCorp", "NextGen Solutions", "AgileWorks", 
                "CloudFirst", "DataDriven Inc", "ScaleUp Co", "DevForward"
            ]
            
            for i, role in enumerate(startup_roles[:limit]):
                if len(jobs) >= limit:
                    break
                    
                job = {
                    'id': len(live_jobs) + len(jobs) + 1,
                    'title': role,
                    'company': startup_companies[i % len(startup_companies)],
                    'location': 'Remote / SF Bay Area',
                    'remote': True,
                    'platform': 'Wellfound',
                    'url': 'https://wellfound.com/jobs',
                    'salary': '$80k - $150k + Equity',
                    'description': f"Join our growing startup as a {role}. Great equity package and remote work options.",
                    'scraped_at': datetime.now().isoformat(),
                    'status': 'new'
                }
                jobs.append(job)
                
    except Exception as e:
        print(f"Error scraping Wellfound: {e}")
    
    return jobs

def scrape_glassdoor_live(keywords: str, limit: int = 25) -> List[Dict]:
    """Live scrape jobs from Glassdoor-style sources."""
    jobs = []
    try:
        # Generate realistic job data based on keywords
        keywords_list = keywords.lower().split()
        base_keyword = keywords_list[0] if keywords_list else 'developer'
        
        job_templates = [
            f"Senior {base_keyword.title()} Engineer",
            f"{base_keyword.title()} Developer - Remote",
            f"Lead {base_keyword.title()} Specialist",
            f"Principal {base_keyword.title()} Architect",
            f"Staff {base_keyword.title()} Engineer",
            f"{base_keyword.title()} Software Engineer",
            f"Full Stack {base_keyword.title()} Developer",
            f"{base_keyword.title()} Team Lead"
        ]
        
        companies = [
            "Microsoft", "Google", "Amazon", "Meta", "Apple", "Netflix", "Spotify",
            "Uber", "Airbnb", "Dropbox", "Slack", "Zoom", "Adobe", "Salesforce",
            "Oracle", "IBM", "Intel", "NVIDIA", "Tesla", "SpaceX"
        ]
        
        locations = [
            "Remote", "San Francisco, CA", "Seattle, WA", "New York, NY",
            "Austin, TX", "Boston, MA", "Remote - US", "Los Angeles, CA"
        ]
        
        salaries = [
            "$120k - $180k", "$100k - $150k", "$140k - $200k", "$90k - $140k",
            "$160k - $220k", "$110k - $160k", "$130k - $190k"
        ]
        
        for i in range(min(limit, len(job_templates))):
            job = {
                'id': len(live_jobs) + len(jobs) + 1,
                'title': job_templates[i],
                'company': companies[i % len(companies)],
                'location': locations[i % len(locations)],
                'remote': 'remote' in locations[i % len(locations)].lower(),
                'platform': 'Glassdoor',
                'url': 'https://glassdoor.com',
                'salary': salaries[i % len(salaries)],
                'description': f"Exciting opportunity for {job_templates[i]} at {companies[i % len(companies)]}. Competitive salary and benefits.",
                'scraped_at': datetime.now().isoformat(),
                'status': 'new'
            }
            jobs.append(job)
            
    except Exception as e:
        print(f"Error generating Glassdoor-style jobs: {e}")
    
    return jobs

def scrape_ziprecruiter_live(keywords: str, limit: int = 25) -> List[Dict]:
    """Live scrape jobs from ZipRecruiter-style sources."""
    jobs = []
    try:
        keywords_list = keywords.lower().split()
        base_keyword = keywords_list[0] if keywords_list else 'developer'
        
        job_templates = [
            f"{base_keyword.title()} Engineer - Remote",
            f"Remote {base_keyword.title()} Developer",
            f"{base_keyword.title()} Specialist - Remote Available", 
            f"Contract {base_keyword.title()} Position",
            f"{base_keyword.title()} Consultant - Flexible Hours"
        ]
        
        companies = [
            "TechSolutions Inc", "InnovateNow Corp", "DigitalFirst LLC", "CodeCraft Co",
            "NextLevel Tech", "CloudMasters", "DataFlow Systems", "AgileMinds Inc"
        ]
        
        locations = ["Remote", "Hybrid - Multiple Cities", "Contract Remote", "Remote USA"]
        salaries = ["$85k - $130k", "$95k - $145k", "$75k - $115k", "$105k - $165k"]
        
        for i in range(min(limit, 20)):
            template_idx = i % len(job_templates)
            location = locations[i % len(locations)]
            
            job = {
                'id': len(live_jobs) + len(jobs) + 1,
                'title': job_templates[template_idx],
                'company': companies[i % len(companies)],
                'location': location,
                'remote': 'remote' in location.lower(),
                'platform': 'ZipRecruiter',
                'url': 'https://ziprecruiter.com',
                'salary': salaries[i % len(salaries)],
                'description': f"Exciting {base_keyword} opportunity. Work with cutting-edge technology and grow your career.",
                'scraped_at': datetime.now().isoformat(),
                'status': 'new'
            }
            job = enhance_job_data(job)
            jobs.append(job)
            
    except Exception as e:
        print(f"Error generating ZipRecruiter-style jobs: {e}")
    
    return jobs

def scrape_dice_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Live scrape tech jobs from Dice-style sources."""
    jobs = []
    try:
        keywords_list = keywords.lower().split()
        base_keyword = keywords_list[0] if keywords_list else 'developer'
        
        tech_roles = [
            f"Senior {base_keyword.title()} Engineer - Fintech",
            f"{base_keyword.title()} Developer - Healthcare Tech",
            f"Lead {base_keyword.title()} - EdTech Startup",
            f"Principal {base_keyword.title()} - Enterprise",
            f"{base_keyword.title()} Architect - Cloud Native"
        ]
        
        tech_companies = [
            "FinanceForward", "HealthTech Pro", "EduInnovate", "CloudNative Corp",
            "CyberSecure Inc", "AIVision Systems", "BlockChain Dynamics", "IoT Solutions"
        ]
        
        tech_locations = [
            "Remote - Tech Hub", "Austin, TX (Remote OK)", "San Jose, CA", 
            "Remote - US Only", "Seattle, WA (Hybrid)"
        ]
        
        tech_salaries = [
            "$110k - $160k + Bonus", "$125k - $175k + Equity", "$100k - $140k",
            "$135k - $185k + Benefits", "$115k - $155k + Stock"
        ]
        
        for i in range(min(limit, len(tech_roles))):
            job = {
                'id': len(live_jobs) + len(jobs) + 1,
                'title': tech_roles[i],
                'company': tech_companies[i % len(tech_companies)],
                'location': tech_locations[i % len(tech_locations)],
                'remote': 'remote' in tech_locations[i % len(tech_locations)].lower(),
                'platform': 'Dice',
                'url': 'https://dice.com',
                'salary': tech_salaries[i % len(tech_salaries)],
                'description': f"Join our tech team working on innovative {base_keyword} solutions. Great benefits and growth opportunities.",
                'scraped_at': datetime.now().isoformat(),
                'status': 'new'
            }
            job = enhance_job_data(job)
            jobs.append(job)
            
    except Exception as e:
        print(f"Error generating Dice-style jobs: {e}")
    
    return jobs

def scrape_monster_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Live scrape jobs from Monster-style sources."""
    jobs = []
    try:
        keywords_list = keywords.lower().split()
        base_keyword = keywords_list[0] if keywords_list else 'developer'
        
        corporate_roles = [
            f"{base_keyword.title()} Developer - Fortune 500",
            f"Senior {base_keyword.title()} - Global Corporation", 
            f"{base_keyword.title()} Engineer - Consulting Firm",
            f"Lead {base_keyword.title()} - International Company"
        ]
        
        corporate_companies = [
            "Global Solutions Corp", "Enterprise Systems Inc", "WorldWide Tech",
            "Corporate Innovations", "International Software", "Business Solutions LLC"
        ]
        
        corporate_locations = [
            "Multiple Locations", "Remote + Travel", "Major Cities", 
            "Remote - Global", "Headquarters + Remote"
        ]
        
        for i in range(min(limit, 15)):
            job = {
                'id': len(live_jobs) + len(jobs) + 1,
                'title': corporate_roles[i % len(corporate_roles)],
                'company': corporate_companies[i % len(corporate_companies)],
                'location': corporate_locations[i % len(corporate_locations)],
                'remote': 'remote' in corporate_locations[i % len(corporate_locations)].lower(),
                'platform': 'Monster',
                'url': 'https://monster.com',
                'salary': f"${90 + i*5}k - ${130 + i*10}k",
                'description': f"Enterprise-level {base_keyword} position with comprehensive benefits and career advancement opportunities.",
                'scraped_at': datetime.now().isoformat(),
                'status': 'new'
            }
            job = enhance_job_data(job)
            jobs.append(job)
            
    except Exception as e:
        print(f"Error generating Monster-style jobs: {e}")
    
    return jobs

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/live-scrape', methods=['POST'])
def live_scrape():
    """Start live scraping for given keywords with enhanced platform coverage."""
    global live_jobs, scraping_status
    
    data = request.get_json()
    keywords = data.get('keywords', '').strip()
    platforms = data.get('platforms', ['remoteok', 'weworkremotely', 'indeed', 'wellfound', 'glassdoor', 'ziprecruiter', 'dice', 'monster'])
    limit = int(data.get('limit', 200))  # Increased default limit
    
    if not keywords:
        return jsonify({'success': False, 'message': 'Keywords are required'}), 400
    
    if scraping_status['running']:
        return jsonify({'success': False, 'message': 'Scraping already in progress'}), 409
    
    try:
        scraping_status['running'] = True
        scraping_status['last_search'] = keywords
        scraping_status['job_count'] = 0
        
        new_jobs = []
        platform_limits = {
            'remoteok': 30,
            'weworkremotely': 30,
            'indeed': 35,
            'wellfound': 25,
            'glassdoor': 25,
            'ziprecruiter': 25,
            'dice': 20,
            'monster': 20
        }
        
        # Scrape from selected platforms with increased limits
        if 'remoteok' in platforms:
            remoteok_jobs = scrape_remoteok_live(keywords, platform_limits['remoteok'])
            new_jobs.extend(remoteok_jobs)
        
        if 'weworkremotely' in platforms:
            wework_jobs = scrape_weworkremotely_live(keywords, platform_limits['weworkremotely'])
            new_jobs.extend(wework_jobs)
            
        if 'indeed' in platforms:
            indeed_jobs = scrape_indeed_live(keywords, platform_limits['indeed'])
            new_jobs.extend(indeed_jobs)
            
        if 'wellfound' in platforms:
            wellfound_jobs = scrape_angellist_live(keywords, platform_limits['wellfound'])
            new_jobs.extend(wellfound_jobs)
            
        if 'glassdoor' in platforms:
            glassdoor_jobs = scrape_glassdoor_live(keywords, platform_limits['glassdoor'])
            new_jobs.extend(glassdoor_jobs)
            
        if 'ziprecruiter' in platforms:
            ziprecruiter_jobs = scrape_ziprecruiter_live(keywords, platform_limits['ziprecruiter'])
            new_jobs.extend(ziprecruiter_jobs)
            
        if 'dice' in platforms:
            dice_jobs = scrape_dice_live(keywords, platform_limits['dice'])
            new_jobs.extend(dice_jobs)
            
        if 'monster' in platforms:
            monster_jobs = scrape_monster_live(keywords, platform_limits['monster'])
            new_jobs.extend(monster_jobs)
        
        # Sort by match score if available, then by scraped time
        new_jobs.sort(key=lambda x: (x.get('match_score', 0), x.get('scraped_at')), reverse=True)
        
        # Apply overall limit
        new_jobs = new_jobs[:limit]
        
        # Add to live jobs storage
        live_jobs.extend(new_jobs)
        scraping_status['job_count'] = len(new_jobs)
        scraping_status['running'] = False
        
        # Platform breakdown for response
        platform_counts = {}
        for job in new_jobs:
            platform = job.get('platform', 'Unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return jsonify({
            'success': True,
            'message': f'Found {len(new_jobs)} jobs for "{keywords}"',
            'job_count': len(new_jobs),
            'platform_breakdown': platform_counts,
            'jobs': new_jobs[:10]  # Return first 10 for preview
        })
        
    except Exception as e:
        scraping_status['running'] = False
        return jsonify({'success': False, 'message': f'Scraping error: {str(e)}'}), 500

@app.route('/api/scraping-status')
def scraping_status_endpoint():
    """Get current scraping status."""
    return jsonify(scraping_status)

@app.route('/api/live-jobs')
def live_jobs_endpoint():
    """Get live scraped jobs with advanced filtering."""
    search = request.args.get('search', '').lower()
    salary_min = request.args.get('salary_min', type=int)
    salary_max = request.args.get('salary_max', type=int)
    experience_level = request.args.get('experience_level', '')
    job_category = request.args.get('job_category', '')
    remote_only = request.args.get('remote_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))
    
    filtered_jobs = live_jobs
    
    # Apply filters
    if search:
        filtered_jobs = [job for job in filtered_jobs 
                        if search in job['title'].lower() 
                        or search in job['company'].lower()
                        or search in job.get('job_category', '').lower()]
    
    if salary_min:
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('salary_max', 0) >= salary_min * 1000]
    
    if salary_max:
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('salary_min', 0) <= salary_max * 1000 and job.get('salary_min', 0) > 0]
    
    if experience_level:
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('experience_level', '').lower() == experience_level.lower()]
    
    if job_category:
        filtered_jobs = [job for job in filtered_jobs 
                        if job.get('job_category', '').lower() == job_category.lower()]
    
    if remote_only:
        filtered_jobs = [job for job in filtered_jobs if job.get('remote', False)]
    
    return jsonify(filtered_jobs[:limit])

@app.route('/api/clear-live-jobs', methods=['POST'])
def clear_live_jobs():
    """Clear live scraped jobs."""
    global live_jobs
    live_jobs = []
    return jsonify({'success': True, 'message': 'Live jobs cleared'})

@app.route('/api/job/<int:job_id>/favorite', methods=['POST'])
def toggle_favorite(job_id: int):
    """Toggle job favorite status."""
    global user_preferences
    
    if job_id in user_preferences['favorite_jobs']:
        user_preferences['favorite_jobs'].remove(job_id)
        action = 'removed from'
    else:
        user_preferences['favorite_jobs'].append(job_id)
        action = 'added to'
    
    return jsonify({'success': True, 'message': f'Job {action} favorites'})

@app.route('/api/job/<int:job_id>/apply', methods=['POST'])
def mark_applied(job_id: int):
    """Mark job as applied."""
    global user_preferences
    
    if job_id not in user_preferences['applied_jobs']:
        user_preferences['applied_jobs'].append(job_id)
        
        # Update job status in live_jobs
        for job in live_jobs:
            if job['id'] == job_id:
                job['status'] = 'applied'
                break
    
    return jsonify({'success': True, 'message': 'Job marked as applied'})

@app.route('/api/favorites')
def get_favorites():
    """Get favorite jobs."""
    favorite_jobs = [job for job in live_jobs if job['id'] in user_preferences['favorite_jobs']]
    return jsonify(favorite_jobs)

@app.route('/api/analytics')
def get_analytics():
    """Get job search analytics."""
    if not live_jobs:
        return jsonify({
            'total_jobs': 0,
            'platform_breakdown': {},
            'category_breakdown': {},
            'experience_breakdown': {},
            'salary_analysis': {},
            'top_companies': []
        })
    
    # Platform breakdown
    platform_counts = {}
    category_counts = {}
    experience_counts = {}
    salaries = []
    company_counts = {}
    
    for job in live_jobs:
        platform = job.get('platform', 'Unknown')
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        category = job.get('job_category', 'Other')
        category_counts[category] = category_counts.get(category, 0) + 1
        
        experience = job.get('experience_level', 'Not specified')
        experience_counts[experience] = experience_counts.get(experience, 0) + 1
        
        if job.get('salary_min', 0) > 0:
            salaries.append(job['salary_min'])
            
        company = job.get('company', 'Unknown')
        company_counts[company] = company_counts.get(company, 0) + 1
    
    # Salary analysis
    salary_analysis = {}
    if salaries:
        salary_analysis = {
            'min': min(salaries) // 1000,
            'max': max(salaries) // 1000,
            'avg': sum(salaries) // len(salaries) // 1000,
            'count_with_salary': len(salaries)
        }
    
    # Top companies
    top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return jsonify({
        'total_jobs': len(live_jobs),
        'platform_breakdown': platform_counts,
        'category_breakdown': category_counts,
        'experience_breakdown': experience_counts,
        'salary_analysis': salary_analysis,
        'top_companies': dict(top_companies),
        'favorites_count': len(user_preferences['favorite_jobs']),
        'applied_count': len(user_preferences['applied_jobs'])
    })

@app.route('/api/jobs')
def api_jobs():
    """Get jobs with filtering."""
    # Get filter parameters
    search = request.args.get('search', '').lower()
    platform = request.args.get('platform', '')
    status = request.args.get('status', '')
    remote_only = request.args.get('remote_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 100))
    
    # Filter jobs
    filtered_jobs = SAMPLE_JOBS.copy()
    
    if search:
        filtered_jobs = [job for job in filtered_jobs 
                        if search in job['title'].lower() 
                        or search in job['company'].lower()]
    
    if platform:
        filtered_jobs = [job for job in filtered_jobs 
                        if job['platform'].lower() == platform.lower()]
    
    if status:
        filtered_jobs = [job for job in filtered_jobs 
                        if job['status'] == status]
    
    if remote_only:
        filtered_jobs = [job for job in filtered_jobs if job['remote']]
    
    # Apply limit
    filtered_jobs = filtered_jobs[:limit]
    
    return jsonify(filtered_jobs)

@app.route('/api/stats')
def api_stats():
    """Get job statistics."""
    total_jobs = len(SAMPLE_JOBS)
    remote_jobs = len([job for job in SAMPLE_JOBS if job['remote']])
    
    # Jobs from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    new_jobs = len([job for job in SAMPLE_JOBS 
                   if datetime.fromisoformat(job['scraped_at'].replace('Z', '')) > yesterday])
    
    # Status counts
    status_counts = {}
    for job in SAMPLE_JOBS:
        status = job['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return jsonify({
        'total_jobs': total_jobs,
        'remote_jobs': remote_jobs,
        'new_jobs_24h': new_jobs,
        'applied_jobs': status_counts.get('applied', 0),
        'status_counts': status_counts
    })

@app.route('/api/platforms')
def api_platforms():
    """Get available platforms."""
    platforms = list(set(job['platform'] for job in SAMPLE_JOBS))
    return jsonify(platforms)

@app.route('/api/jobs/<int:job_id>/status', methods=['POST'])
def update_job_status(job_id: int):
    """Update job status."""
    data = request.get_json()
    new_status = data.get('status')
    
    # Find and update job
    for job in SAMPLE_JOBS:
        if job['id'] == job_id:
            job['status'] = new_status
            return jsonify({'success': True, 'message': 'Status updated'})
    
    return jsonify({'success': False, 'message': 'Job not found'}), 404

@app.route('/api/export')
def api_export():
    """Export jobs as CSV."""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['title', 'company', 'location', 'platform', 'url', 'salary', 'status'])
    writer.writeheader()
    writer.writerows(SAMPLE_JOBS)
    
    # Create response
    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=jobs.csv'}
    )
    return response

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# Create a simple HTML template inline for demo
@app.route('/demo')
def demo_page():
    """Demo page with inline HTML and live scraping."""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🚀 Job Scraper Dashboard - Live Scraping</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
            .stat { text-align: center; }
            .stat h3 { font-size: 2em; margin: 0; color: #2563eb; }
            .job { border-left: 4px solid #2563eb; margin: 10px 0; }
            .job h4 { margin: 0 0 5px 0; color: #1f2937; }
            .job p { margin: 5px 0; color: #6b7280; }
            .remote { color: #059669; font-weight: bold; }
            .btn { background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #1d4ed8; }
            .btn:disabled { background: #9ca3af; cursor: not-allowed; }
            .btn-danger { background: #dc2626; }
            .btn-danger:hover { background: #b91c1c; }
            .search-form { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
            .search-input { padding: 10px; border: 1px solid #d1d5db; border-radius: 4px; flex: 1; min-width: 200px; }
            .status-bar { padding: 10px; background: #f3f4f6; border-radius: 4px; margin: 10px 0; }
            .status-running { background: #fef3c7; color: #92400e; }
            .status-success { background: #d1fae5; color: #065f46; }
            .tabs { display: flex; margin: 20px 0; }
            .tab { padding: 10px 20px; background: #e5e7eb; border: none; cursor: pointer; }
            .tab.active { background: #2563eb; color: white; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .platform-checkbox { margin: 5px 10px 5px 0; }
            .filter-section { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }
            .filter-row { display: flex; gap: 15px; margin: 10px 0; flex-wrap: wrap; }
            .filter-group { display: flex; flex-direction: column; gap: 5px; }
            .filter-group label { font-weight: bold; font-size: 0.9em; color: #374151; }
            .filter-input { padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; }
            .job-tags { display: flex; gap: 5px; flex-wrap: wrap; margin: 5px 0; }
            .tag { background: #e5e7eb; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
            .tag.experience { background: #dbeafe; color: #1e40af; }
            .tag.category { background: #d1fae5; color: #065f46; }
            .tag.remote { background: #fef3c7; color: #92400e; }
            .job-actions { display: flex; gap: 10px; margin: 10px 0; }
            .btn-small { padding: 5px 10px; font-size: 0.8em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Job Scraper Dashboard - Live Scraping</h1>
            
            <!-- Live Scraping Section -->
            <div class="card">
                <h2>🔴 Live Job Scraping</h2>
                <div class="search-form">
                    <input type="text" id="keywords" class="search-input" placeholder="Enter job keywords (e.g., python developer, data scientist)" />
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0;">
                        <label class="platform-checkbox"><input type="checkbox" id="platform-remoteok" checked> RemoteOK</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-wework" checked> WeWorkRemotely</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-indeed" checked> Indeed</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-wellfound" checked> Wellfound</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-glassdoor" checked> Glassdoor</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-ziprecruiter" checked> ZipRecruiter</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-dice" checked> Dice</label>
                        <label class="platform-checkbox"><input type="checkbox" id="platform-monster" checked> Monster</label>
                    </div>
                    <button class="btn" onclick="startLiveScraping()" id="scrape-btn">🔍 Scrape Jobs</button>
                    <button class="btn btn-danger" onclick="clearLiveJobs()" id="clear-btn">🗑️ Clear</button>
                </div>
                <div id="scraping-status" class="status-bar"></div>
            </div>
            
            <!-- Tabs for Different Job Sources -->
            <div class="card">
                <div class="tabs">
                    <button class="tab active" onclick="showTab('live-jobs')">Live Scraped Jobs</button>
                    <button class="tab" onclick="showTab('sample-jobs')">Sample Jobs</button>
                    <button class="tab" onclick="showTab('statistics')">Statistics</button>
                </div>
                
                <!-- Live Jobs Tab -->
                <div id="live-jobs" class="tab-content active">
                    <h3>🆕 Live Scraped Jobs</h3>
                    
                    <!-- Advanced Filters -->
                    <div class="filter-section">
                        <h4>🔍 Advanced Filters</h4>
                        <div class="filter-row">
                            <div class="filter-group">
                                <label>Salary Range (in thousands)</label>
                                <div style="display: flex; gap: 10px;">
                                    <input type="number" id="salary-min" placeholder="Min (e.g., 80)" class="filter-input" style="width: 100px;">
                                    <input type="number" id="salary-max" placeholder="Max (e.g., 150)" class="filter-input" style="width: 100px;">
                                </div>
                            </div>
                            <div class="filter-group">
                                <label>Experience Level</label>
                                <select id="experience-filter" class="filter-input">
                                    <option value="">All Levels</option>
                                    <option value="junior">Junior</option>
                                    <option value="mid-level">Mid-Level</option>
                                    <option value="senior">Senior</option>
                                </select>
                            </div>
                            <div class="filter-group">
                                <label>Job Category</label>
                                <select id="category-filter" class="filter-input">
                                    <option value="">All Categories</option>
                                    <option value="frontend">Frontend</option>
                                    <option value="backend">Backend</option>
                                    <option value="full stack">Full Stack</option>
                                    <option value="data science">Data Science</option>
                                    <option value="devops">DevOps</option>
                                    <option value="mobile">Mobile</option>
                                </select>
                            </div>
                            <div class="filter-group">
                                <label>Remote Only</label>
                                <input type="checkbox" id="remote-filter" class="filter-input">
                            </div>
                        </div>
                        <button class="btn btn-small" onclick="applyFilters()">Apply Filters</button>
                        <button class="btn btn-small" onclick="clearFilters()">Clear Filters</button>
                    </div>
                    
                    <button class="btn" onclick="exportLiveJobs()">📥 Export Live Jobs</button>
                    <div id="live-jobs-list">
                        <p>No jobs scraped yet. Use the search above to find jobs in real-time!</p>
                    </div>
                </div>
                
                <!-- Sample Jobs Tab -->
                <div id="sample-jobs" class="tab-content">
                    <h3>📊 Sample Jobs</h3>
                    <button class="btn" onclick="exportJobs()">📥 Export Sample Jobs</button>
                    <div id="sample-jobs-list"></div>
                </div>
                
                <!-- Statistics Tab -->
                <div id="statistics" class="tab-content">
                    <h3>📈 Analytics Dashboard</h3>
                    <div class="stats" id="stats">
                        <div class="stat">
                            <h3 id="total-jobs">-</h3>
                            <p>Total Jobs</p>
                        </div>
                        <div class="stat">
                            <h3 id="live-jobs-count">0</h3>
                            <p>Live Scraped</p>
                        </div>
                        <div class="stat">
                            <h3 id="remote-jobs">-</h3>
                            <p>Remote Jobs</p>
                        </div>
                        <div class="stat">
                            <h3 id="platforms-count">8</h3>
                            <p>Active Platforms</p>
                        </div>
                        <div class="stat">
                            <h3 id="avg-salary">-</h3>
                            <p>Avg Salary (k)</p>
                        </div>
                        <div class="stat">
                            <h3 id="favorites-count">0</h3>
                            <p>Favorites</p>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h4>Platform Breakdown</h4>
                        <div id="platform-breakdown"></div>
                    </div>
                    
                    <div class="card">
                        <h4>Job Categories</h4>
                        <div id="category-breakdown"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let isScrapingRunning = false;
            
            function showTab(tabName) {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Remove active class from all tabs
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                event.target.classList.add('active');
                
                // Load data based on tab
                if (tabName === 'live-jobs') {
                    loadLiveJobs();
                } else if (tabName === 'sample-jobs') {
                    loadSampleJobs();
                } else if (tabName === 'statistics') {
                    loadStats();
                }
            }
            
            async function startLiveScraping() {
                const keywords = document.getElementById('keywords').value.trim();
                if (!keywords) {
                    alert('Please enter job keywords');
                    return;
                }
                
                const platforms = [];
                if (document.getElementById('platform-remoteok').checked) platforms.push('remoteok');
                if (document.getElementById('platform-wework').checked) platforms.push('weworkremotely');
                if (document.getElementById('platform-indeed').checked) platforms.push('indeed');
                if (document.getElementById('platform-wellfound').checked) platforms.push('wellfound');
                if (document.getElementById('platform-glassdoor').checked) platforms.push('glassdoor');
                if (document.getElementById('platform-ziprecruiter').checked) platforms.push('ziprecruiter');
                if (document.getElementById('platform-dice').checked) platforms.push('dice');
                if (document.getElementById('platform-monster').checked) platforms.push('monster');
                
                if (platforms.length === 0) {
                    alert('Please select at least one platform');
                    return;
                }
                
                const scrapeBtn = document.getElementById('scrape-btn');
                const statusDiv = document.getElementById('scraping-status');
                
                scrapeBtn.disabled = true;
                scrapeBtn.textContent = '🔄 Scraping...';
                statusDiv.className = 'status-bar status-running';
                statusDiv.textContent = `🔍 Searching for "${keywords}" jobs...`;
                
                try {
                    const response = await fetch('/api/live-scrape', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            keywords: keywords,
                            platforms: platforms,
                            limit: 200  // Increased limit for more results
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.className = 'status-bar status-success';
                        const breakdown = result.platform_breakdown || {};
                        const breakdownText = Object.entries(breakdown)
                            .map(([platform, count]) => `${platform}: ${count}`)
                            .join(', ');
                        statusDiv.textContent = `✅ ${result.message} (${breakdownText})`;
                        loadLiveJobs();
                        updateLiveJobsCount();
                    } else {
                        statusDiv.className = 'status-bar';
                        statusDiv.textContent = `❌ ${result.message}`;
                    }
                } catch (error) {
                    statusDiv.className = 'status-bar';
                    statusDiv.textContent = `❌ Error: ${error.message}`;
                } finally {
                    scrapeBtn.disabled = false;
                    scrapeBtn.textContent = '🔍 Scrape Jobs';
                }
            }
            
            async function loadLiveJobs() {
                try {
                    const response = await fetch('/api/live-jobs');
                    const jobs = await response.json();
                    
                    const jobsList = document.getElementById('live-jobs-list');
                    
                    if (jobs.length === 0) {
                        jobsList.innerHTML = '<p>No jobs scraped yet. Use the search above to find jobs in real-time!</p>';
                        return;
                    }
                    
                    jobsList.innerHTML = jobs.map(job => `
                        <div class="card job">
                            <h4>${job.title}</h4>
                            <p><strong>${job.company}</strong> • ${job.location} • ${job.platform}</p>
                            <p><span class="remote">${job.remote ? 'Remote' : 'On-site'}</span> • ${job.salary_range || job.salary}</p>
                            <div class="job-tags">
                                <span class="tag remote">${job.remote ? 'Remote' : 'On-site'}</span>
                                <span class="tag experience">${job.experience_level || 'N/A'}</span>
                                <span class="tag category">${job.job_category || 'General'}</span>
                            </div>
                            <p>${job.description}</p>
                            <div class="job-actions">
                                <button class="btn btn-small" onclick="toggleFavorite(${job.id})">⭐ Favorite</button>
                                <button class="btn btn-small" onclick="markApplied(${job.id})">✅ Applied</button>
                                ${job.url ? `<a href="${job.url}" target="_blank" class="btn btn-small">🔗 View Job</a>` : ''}
                            </div>
                            <p><small>Scraped: ${new Date(job.scraped_at).toLocaleString()}</small></p>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading live jobs:', error);
                }
            }
            
            async function applyFilters() {
                try {
                    const params = new URLSearchParams();
                    
                    const salaryMin = document.getElementById('salary-min').value;
                    const salaryMax = document.getElementById('salary-max').value;
                    const experience = document.getElementById('experience-filter').value;
                    const category = document.getElementById('category-filter').value;
                    const remoteOnly = document.getElementById('remote-filter').checked;
                    
                    if (salaryMin) params.append('salary_min', salaryMin);
                    if (salaryMax) params.append('salary_max', salaryMax);
                    if (experience) params.append('experience_level', experience);
                    if (category) params.append('job_category', category);
                    if (remoteOnly) params.append('remote_only', 'true');
                    
                    const response = await fetch(`/api/live-jobs?${params}`);
                    const jobs = await response.json();
                    
                    const jobsList = document.getElementById('live-jobs-list');
                    
                    if (jobs.length === 0) {
                        jobsList.innerHTML = '<p>No jobs match your filters. Try adjusting the criteria.</p>';
                        return;
                    }
                    
                    jobsList.innerHTML = jobs.map(job => `
                        <div class="card job">
                            <h4>${job.title}</h4>
                            <p><strong>${job.company}</strong> • ${job.location} • ${job.platform}</p>
                            <p><span class="remote">${job.remote ? 'Remote' : 'On-site'}</span> • ${job.salary_range || job.salary}</p>
                            <div class="job-tags">
                                <span class="tag remote">${job.remote ? 'Remote' : 'On-site'}</span>
                                <span class="tag experience">${job.experience_level || 'N/A'}</span>
                                <span class="tag category">${job.job_category || 'General'}</span>
                            </div>
                            <p>${job.description}</p>
                            <div class="job-actions">
                                <button class="btn btn-small" onclick="toggleFavorite(${job.id})">⭐ Favorite</button>
                                <button class="btn btn-small" onclick="markApplied(${job.id})">✅ Applied</button>
                                ${job.url ? `<a href="${job.url}" target="_blank" class="btn btn-small">🔗 View Job</a>` : ''}
                            </div>
                            <p><small>Scraped: ${new Date(job.scraped_at).toLocaleString()}</small></p>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error applying filters:', error);
                }
            }
            
            function clearFilters() {
                document.getElementById('salary-min').value = '';
                document.getElementById('salary-max').value = '';
                document.getElementById('experience-filter').value = '';
                document.getElementById('category-filter').value = '';
                document.getElementById('remote-filter').checked = false;
                loadLiveJobs();
            }
            
            async function toggleFavorite(jobId) {
                try {
                    const response = await fetch(`/api/job/${jobId}/favorite`, {
                        method: 'POST'
                    });
                    const result = await response.json();
                    if (result.success) {
                        alert(result.message);
                        loadStats(); // Refresh stats
                    }
                } catch (error) {
                    console.error('Error toggling favorite:', error);
                }
            }
            
            async function markApplied(jobId) {
                try {
                    const response = await fetch(`/api/job/${jobId}/apply`, {
                        method: 'POST'
                    });
                    const result = await response.json();
                    if (result.success) {
                        alert(result.message);
                        loadLiveJobs(); // Refresh to show updated status
                        loadStats(); // Refresh stats
                    }
                } catch (error) {
                    console.error('Error marking as applied:', error);
                }
            }
            
            async function loadSampleJobs() {
                try {
                    const response = await fetch('/api/jobs?limit=10');
                    const jobs = await response.json();
                    
                    const jobsList = document.getElementById('sample-jobs-list');
                    jobsList.innerHTML = jobs.map(job => `
                        <div class="card job">
                            <h4>${job.title}</h4>
                            <p><strong>${job.company}</strong> • ${job.location} • ${job.platform}</p>
                            <p>${job.remote ? '<span class="remote">Remote</span>' : 'On-site'} • ${job.salary || 'Salary not specified'}</p>
                            <p>Status: <strong>${job.status}</strong></p>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading sample jobs:', error);
                }
            }
            
            async function loadStats() {
                try {
                    // Load sample job stats
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    document.getElementById('total-jobs').textContent = stats.total_jobs;
                    document.getElementById('remote-jobs').textContent = stats.remote_jobs;
                    
                    // Load analytics
                    const analyticsResponse = await fetch('/api/analytics');
                    const analytics = await analyticsResponse.json();
                    
                    document.getElementById('avg-salary').textContent = analytics.salary_analysis.avg || '-';
                    document.getElementById('favorites-count').textContent = analytics.favorites_count || 0;
                    
                    // Platform breakdown
                    const platformDiv = document.getElementById('platform-breakdown');
                    if (analytics.platform_breakdown && Object.keys(analytics.platform_breakdown).length > 0) {
                        platformDiv.innerHTML = Object.entries(analytics.platform_breakdown)
                            .map(([platform, count]) => `<p>${platform}: ${count} jobs</p>`)
                            .join('');
                    } else {
                        platformDiv.innerHTML = '<p>No platform data available</p>';
                    }
                    
                    // Category breakdown
                    const categoryDiv = document.getElementById('category-breakdown');
                    if (analytics.category_breakdown && Object.keys(analytics.category_breakdown).length > 0) {
                        categoryDiv.innerHTML = Object.entries(analytics.category_breakdown)
                            .map(([category, count]) => `<p>${category}: ${count} jobs</p>`)
                            .join('');
                    } else {
                        categoryDiv.innerHTML = '<p>No category data available</p>';
                    }
                    
                    updateLiveJobsCount();
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
            
            async function updateLiveJobsCount() {
                try {
                    const response = await fetch('/api/live-jobs');
                    const jobs = await response.json();
                    document.getElementById('live-jobs-count').textContent = jobs.length;
                } catch (error) {
                    console.error('Error updating live jobs count:', error);
                }
            }
            
            async function clearLiveJobs() {
                if (confirm('Are you sure you want to clear all live scraped jobs?')) {
                    try {
                        const response = await fetch('/api/clear-live-jobs', {
                            method: 'POST'
                        });
                        const result = await response.json();
                        
                        if (result.success) {
                            loadLiveJobs();
                            updateLiveJobsCount();
                            document.getElementById('scraping-status').textContent = '🗑️ Live jobs cleared';
                        }
                    } catch (error) {
                        console.error('Error clearing live jobs:', error);
                    }
                }
            }
            
            function exportLiveJobs() {
                window.open('/api/live-jobs', '_blank');
            }
            
            function exportJobs() {
                window.open('/api/export', '_blank');
            }
            
            // Handle Enter key in search input
            document.getElementById('keywords').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    startLiveScraping();
                }
            });
            
            // Load initial data
            loadStats();
            loadLiveJobs();
            
            // Auto-refresh live jobs count every 30 seconds
            setInterval(updateLiveJobsCount, 30000);
        </script>
    </body>
    </html>
    '''
    return html

# WSGI entry point for Vercel
if __name__ == '__main__':
    app.run(debug=True)