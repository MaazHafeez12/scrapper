"""Simplified Vercel-compatible web dashboard for job scraper with business intelligence."""
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
from collections import defaultdict
import sys

# Import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import JobDatabase

# Import contact discovery module
try:
    from contact_discovery import contact_discovery
    CONTACT_DISCOVERY_ENABLED = True
except ImportError as e:
    print(f"Contact discovery module not available: {e}")
    CONTACT_DISCOVERY_ENABLED = False
    contact_discovery = None

# Import outreach templates module
try:
    from outreach_templates import outreach_personalizer
    OUTREACH_TEMPLATES_ENABLED = True
except ImportError as e:
    print(f"Outreach templates module not available: {e}")
    OUTREACH_TEMPLATES_ENABLED = False
    outreach_personalizer = None

# Import advanced scraper module
try:
    from advanced_scraper import advanced_scraper
    ADVANCED_SCRAPER_ENABLED = True
except ImportError as e:
    print(f"Advanced scraper module not available: {e}")
    ADVANCED_SCRAPER_ENABLED = False
    advanced_scraper = None

# Import email automation module
try:
    from email_automation import EmailAutomation, EMAIL_SEQUENCE_TEMPLATES
    email_automation = EmailAutomation()
    EMAIL_AUTOMATION_ENABLED = True
except ImportError as e:
    print(f"Email automation module not available: {e}")
    EMAIL_AUTOMATION_ENABLED = False
    email_automation = None

# Import analytics dashboard module
try:
    from analytics_dashboard import AnalyticsDashboard
    analytics = AnalyticsDashboard()
    ANALYTICS_ENABLED = True
except ImportError as e:
    print(f"Analytics dashboard module not available: {e}")
    ANALYTICS_ENABLED = False
    analytics = None

# Import CRM integration module
try:
    from crm_integration import CRMIntegration
    crm = CRMIntegration()
    CRM_ENABLED = True
except ImportError as e:
    print(f"CRM integration module not available: {e}")
    CRM_ENABLED = False
    crm = None

# Import AI features module
try:
    from ai_features import AIFeatures
    ai = AIFeatures()
    AI_ENABLED = True
except ImportError as e:
    print(f"AI features module not available: {e}")
    AI_ENABLED = False
    ai = None

# Import follow-up engine module
try:
    from followup_engine import FollowUpEngine
    followup_engine = FollowUpEngine()
    FOLLOWUP_ENGINE_ENABLED = True
except ImportError as e:
    print(f"Follow-up engine module not available: {e}")
    FOLLOWUP_ENGINE_ENABLED = False
    followup_engine = None

# Import lead enrichment module
try:
    from lead_enrichment import LeadEnrichment
    lead_enrichment = LeadEnrichment()
    LEAD_ENRICHMENT_ENABLED = True
except ImportError as e:
    print(f"Lead enrichment module not available: {e}")
    LEAD_ENRICHMENT_ENABLED = False
    lead_enrichment = None

# Import A/B testing module
try:
    from ab_testing import ABTestingFramework
    ab_testing = ABTestingFramework()
    AB_TESTING_ENABLED = True
except ImportError as e:
    print(f"A/B testing module not available: {e}")
    AB_TESTING_ENABLED = False
    ab_testing = None

# Import reporting engine module
try:
    from reporting_engine import ReportingEngine
    reporting = ReportingEngine()
    REPORTING_ENABLED = True
except ImportError as e:
    print(f"Reporting engine module not available: {e}")
    REPORTING_ENABLED = False
    reporting = None

# Import multi-channel outreach module
try:
    from multichannel_outreach import MultiChannelOutreach
    multichannel = MultiChannelOutreach()
    MULTICHANNEL_ENABLED = True
except ImportError as e:
    print(f"Multi-channel outreach module not available: {e}")
    MULTICHANNEL_ENABLED = False
    multichannel = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-demo-key')

# Initialize database
try:
    db = JobDatabase('business_leads.db')
except Exception as e:
    print(f"Database initialization error: {e}")
    db = None

# Live scraping storage (in-memory for serverless fallback)
live_jobs = []
scraping_status = {'running': False, 'last_search': None, 'job_count': 0}
user_preferences = {'saved_searches': [], 'favorite_jobs': [], 'applied_jobs': []}

# Business Intelligence for Lead Generation (fallback)
business_leads = []

# Simplified Business Intelligence Functions
def extract_company_intelligence(job: Dict) -> Dict:
    """Extract enhanced business intelligence from job posting with advanced scoring."""
    company = job.get('company', '').strip()
    title = job.get('title', '').strip()
    description = job.get('description', '').strip()
    location = job.get('location', '').strip()
    platform = job.get('platform', '').strip()
    
    # Initialize scoring components
    base_score = 0
    scoring_details = {}
    
    # Enhanced company size detection with growth indicators
    company_size = "Unknown"
    company_score = 0
    desc_lower = description.lower()
    company_lower = company.lower()
    
    # Company size scoring
    if any(word in desc_lower for word in ['startup', 'small team', 'growing company', 'early stage']):
        company_size = "Startup"
        company_score = 25  # High potential for new services
        scoring_details['company_size_reason'] = "Startup - high growth potential"
    elif any(word in desc_lower for word in ['enterprise', 'large company', 'fortune', 'global', 'multinational']):
        company_size = "Enterprise"
        company_score = 15  # Established but harder to reach
        scoring_details['company_size_reason'] = "Enterprise - established market"
    elif any(word in desc_lower for word in ['mid-size', 'medium company', 'scale', 'scaling']):
        company_size = "Mid-size"
        company_score = 20  # Good balance
        scoring_details['company_size_reason'] = "Mid-size - good opportunity balance"
    else:
        company_size = "Unknown"
        company_score = 10
        scoring_details['company_size_reason'] = "Unknown size"
    
    # Technology stack complexity scoring
    tech_keywords = [
        ('python', 8), ('javascript', 6), ('react', 7), ('node', 6), ('typescript', 8),
        ('aws', 10), ('azure', 10), ('gcp', 10), ('docker', 9), ('kubernetes', 12),
        ('microservices', 15), ('api', 5), ('graphql', 8), ('mongodb', 6), ('postgresql', 7),
        ('redis', 8), ('elasticsearch', 10), ('kafka', 12), ('spark', 12), ('tensorflow', 15),
        ('machine learning', 18), ('ai', 15), ('blockchain', 20), ('devops', 10), ('cicd', 8)
    ]
    
    technologies = []
    tech_score = 0
    
    for tech, score in tech_keywords:
        if tech in desc_lower or tech in title.lower():
            technologies.append(tech)
            tech_score += score
    
    # Cap technology score at 50
    tech_score = min(tech_score, 50)
    scoring_details['technology_score'] = tech_score
    scoring_details['technologies_found'] = technologies
    
    # Market timing and urgency indicators
    urgency_score = 0
    urgency_indicators = [
        ('urgent', 15), ('immediate', 12), ('asap', 10), ('quickly', 8),
        ('fast-paced', 8), ('rapid', 8), ('growing team', 10), ('expanding', 12),
        ('hiring now', 15), ('immediate start', 15), ('new position', 8)
    ]
    
    for indicator, score in urgency_indicators:
        if indicator in desc_lower:
            urgency_score += score
    
    urgency_score = min(urgency_score, 25)  # Cap at 25
    scoring_details['urgency_score'] = urgency_score
    
    # Platform credibility scoring
    platform_scores = {
        'LinkedIn': 15,    # High credibility
        'Indeed': 10,      # Good volume
        'Glassdoor': 12,   # Company insights
        'RemoteOK': 8,     # Tech-focused
        'WeWorkRemotely': 8,
        'Wellfound': 12,   # Startup focus
        'NoDesk': 6
    }
    platform_score = platform_scores.get(platform, 5)
    scoring_details['platform_score'] = platform_score
    
    # Geographic and remote work scoring
    location_score = 0
    if 'remote' in location.lower() or 'remote' in desc_lower:
        location_score = 15  # Remote-first companies often use tech services
        scoring_details['location_advantage'] = "Remote-first culture"
    elif any(city in location.lower() for city in ['san francisco', 'sf', 'silicon valley', 'seattle', 'new york', 'austin', 'boston']):
        location_score = 12  # Tech hubs
        scoring_details['location_advantage'] = "Tech hub location"
    else:
        location_score = 5
        scoring_details['location_advantage'] = "Standard location"
    
    # Industry and domain scoring
    industry_score = 0
    high_value_industries = [
        ('fintech', 15), ('healthtech', 15), ('edtech', 12), ('blockchain', 18),
        ('ai', 18), ('ml', 18), ('saas', 15), ('cloud', 12), ('cybersecurity', 15),
        ('data', 10), ('analytics', 12), ('automation', 12)
    ]
    
    for industry, score in high_value_industries:
        if industry in desc_lower or industry in company_lower:
            industry_score = max(industry_score, score)  # Take highest match
    
    scoring_details['industry_score'] = industry_score
    
    # Job seniority and decision-making power indicators
    seniority_score = 0
    if any(level in title.lower() for level in ['senior', 'lead', 'principal', 'architect', 'manager', 'director']):
        seniority_score = 8  # Higher-level roles suggest budget authority
        scoring_details['seniority_bonus'] = "Senior-level position"
    elif any(level in title.lower() for level in ['junior', 'entry', 'intern']):
        seniority_score = 2
        scoring_details['seniority_bonus'] = "Entry-level position"
    else:
        seniority_score = 5
        scoring_details['seniority_bonus'] = "Mid-level position"
    
    # Calculate final lead score
    final_score = (
        company_score +      # 25 max
        tech_score +         # 50 max  
        urgency_score +      # 25 max
        platform_score +     # 15 max
        location_score +     # 15 max
        industry_score +     # 18 max
        seniority_score      # 8 max
    )
    
    # Ensure score is between 0-100
    final_score = min(max(final_score, 0), 100)
    
    # Determine contact potential based on score
    if final_score >= 75:
        contact_potential = 'Excellent'
    elif final_score >= 60:
        contact_potential = 'High'
    elif final_score >= 40:
        contact_potential = 'Medium'
    elif final_score >= 25:
        contact_potential = 'Low'
    else:
        contact_potential = 'Very Low'
    
    # Create tech stack summary
    tech_stack = ', '.join(technologies[:5]) if technologies else 'General'
    
    return {
        'company_size': company_size,
        'technologies': technologies,
        'lead_score': final_score,
        'tech_stack': tech_stack,
        'contact_potential': contact_potential,
        'scoring_breakdown': scoring_details,
        'score_components': {
            'company_size': company_score,
            'technology_stack': tech_score,
            'market_urgency': urgency_score,
            'platform_credibility': platform_score,
            'location_advantage': location_score,
            'industry_value': industry_score,
            'seniority_level': seniority_score
        }
    }

def generate_working_job_url(job: Dict) -> str:
    """Generate working URLs for job postings."""
    company = job.get('company', '').strip()
    platform = job.get('platform', '')
    title = job.get('title', '')
    
    # Clean company name for URL generation
    clean_company = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
    
    # Platform-specific URL generation
    if platform == 'LinkedIn':
        # LinkedIn company pages and job search
        return f"https://www.linkedin.com/jobs/search/?keywords={title.replace(' ', '%20')}&f_C={clean_company}"
    elif platform == 'Indeed':
        # Indeed company search
        return f"https://www.indeed.com/jobs?q={title.replace(' ', '+')}&l=remote"
    elif platform == 'Glassdoor':
        # Glassdoor company page
        return f"https://www.glassdoor.com/Jobs/{company.replace(' ', '-')}-jobs-SRCH_KE0,{len(company)}.htm"
    elif platform == 'RemoteOK':
        return f"https://remoteok.io/remote-{title.replace(' ', '-').lower()}-jobs"
    elif platform == 'WeWorkRemotely':
        return f"https://weworkremotely.com/remote-jobs/search?term={title.replace(' ', '+')}"
    elif platform == 'Wellfound':
        return f"https://wellfound.com/jobs?keywords={title.replace(' ', '%20')}"
    elif platform == 'NoDesk':
        return f"https://nodesk.co/remote-jobs/"
    else:
        # Fallback to Google search for company + careers
        return f"https://www.google.com/search?q={company.replace(' ', '+')}+careers+{title.replace(' ', '+')}"

def enhance_job_data(job: Dict) -> Dict:
    """Enhance job data with business intelligence and save to database."""
    try:
        # Add business intelligence
        business_intel = extract_company_intelligence(job)
        job.update(business_intel)
        
        # Generate working job URL
        working_url = generate_working_job_url(job)
        job['url'] = working_url
        job['original_url'] = job.get('url', '')  # Keep original if it existed
        
        # Add additional job metadata
        job['date_enhanced'] = datetime.now().isoformat()
        job['url_type'] = 'company_search'  # Indicate this is a search-based URL
        
        # Save job to database if available
        if db:
            try:
                # Prepare job data for database
                job_data = {
                    'title': job.get('title', 'Unknown'),
                    'company': job.get('company', 'Unknown'),
                    'location': job.get('location', 'Unknown'),
                    'platform': job.get('platform', 'Unknown'),
                    'url': working_url,
                    'description': job.get('description', ''),
                    'salary_range': job.get('salary_range', ''),
                    'experience_level': job.get('experience_level', ''),
                    'employment_type': job.get('employment_type', ''),
                    'date_posted': job.get('date_posted', datetime.now().strftime('%Y-%m-%d')),
                    'keywords_used': scraping_status.get('last_search', '')
                }
                
                # Generate hash for duplicate detection
                job_hash = f"{job_data['title']}-{job_data['company']}-{job_data['platform']}".lower().strip()
                
                # Save using database method
                if hasattr(db, 'save_job'):
                    db.save_job(job_data)
                else:
                    # Use existing database structure
                    existing_id = db.job_exists(job_hash)
                    if existing_id:
                        db.update_job_last_seen(existing_id)
                    else:
                        db.insert_job(job_data)
                        
            except Exception as e:
                print(f"Error saving job to database: {e}")
        
        # Add to business leads if score is high enough
        if business_intel['lead_score'] >= 40:
            lead = {
                'company': job.get('company', 'Unknown'),
                'title': job.get('title', 'Unknown'),
                'location': job.get('location', 'Unknown'),
                'technologies': business_intel['technologies'],
                'lead_score': business_intel['lead_score'],
                'company_size': business_intel['company_size'],
                'contact_potential': business_intel['contact_potential'],
                'job_url': working_url,
                'platform': job.get('platform', 'Unknown'),
                'date_found': datetime.now().isoformat()
            }
            
            # Save to database if available
            if db and hasattr(db, 'save_business_lead'):
                try:
                    db.save_business_lead(lead)
                except Exception as e:
                    print(f"Error saving business lead to database: {e}")
                    # Fallback to in-memory storage
                    existing = any(l['company'] == lead['company'] and l['title'] == lead['title'] 
                                  for l in business_leads)
                    if not existing:
                        business_leads.append(lead)
            else:
                # Fallback to in-memory storage
                existing = any(l['company'] == lead['company'] and l['title'] == lead['title'] 
                              for l in business_leads)
                if not existing:
                    business_leads.append(lead)
        
        return job
    except Exception as e:
        print(f"Error enhancing job data: {e}")
        return job

# Simplified scraping functions with fallbacks and mock data
def scrape_remoteok_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape RemoteOK for live jobs with fallback to mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        url = f"https://remoteok.io/remote-{quote(keywords)}-jobs"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for RemoteOK
            job_elements = (soup.find_all('tr', class_='job') or 
                          soup.find_all('tr', {'data-href': True}) or
                          soup.find_all('div', class_='job'))
            
            for element in job_elements[:limit]:
                try:
                    # Skip empty or placeholder elements
                    text_content = element.get_text(strip=True)
                    if not text_content or len(text_content) < 10:
                        continue
                    
                    # Try different ways to extract job info
                    title = company = location = url_link = ""
                    
                    # Method 1: Look for specific RemoteOK structure
                    title_elem = (element.find('td', class_='company position company_and_position') or
                                element.find('h2') or 
                                element.find('a', href=True))
                    
                    if title_elem and title_elem.get_text(strip=True):
                        full_text = title_elem.get_text(strip=True)
                        # Try to parse company and title from combined text
                        parts = full_text.split('\n')
                        if len(parts) >= 2:
                            title = parts[0].strip()
                            company = parts[1].strip()
                        else:
                            title = full_text[:50]
                            company = "Remote Company"
                        
                        # Get URL if available
                        link_elem = element.find('a', href=True)
                        if link_elem:
                            url_link = f"https://remoteok.io{link_elem['href']}"
                        
                        job = {
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'platform': 'RemoteOK',
                            'url': url_link,
                            'description': full_text[:200],
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1
                        }
                        jobs.append(enhance_job_data(job))
                        
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping RemoteOK: {e}")
    
    # If no jobs found, add some mock data for demo purposes
    if len(jobs) == 0:
        companies = ['TechCorp Remote', 'StartupXYZ', 'InnovateNow', 'CloudVegas', 'DataSync Inc', 'RemoteFirst Labs', 'NextGen Dev', 'ScaleBuilders']
        roles = [
            f'{keywords.title()} Developer', f'Senior {keywords.title()} Engineer', f'Lead {keywords.title()} Developer',
            f'Full Stack Developer', f'Backend Engineer', f'Frontend Developer', f'DevOps Engineer',
            f'Product Manager', f'Data Analyst', f'UI/UX Designer', f'QA Engineer', f'Sales Engineer'
        ]
        
        mock_jobs = []
        for i in range(min(limit, 15)):  # Generate more jobs
            import random
            company = random.choice(companies)
            role = random.choice(roles)
            
            mock_jobs.append({
                'title': role,
                'company': company,
                'location': 'Remote',
                'platform': 'RemoteOK',
                'description': f'{role} position with modern tech stack at {company}',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': i + 1,
                'salary_range': f'${random.randint(60, 150)}k',
                'experience_level': random.choice(['Entry', 'Mid', 'Senior']),
            })
        
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_indeed_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape Indeed for live jobs with fallback to mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        url = f"https://www.indeed.com/jobs?q={quote(keywords)}&l=remote"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Indeed
            job_elements = (soup.find_all('div', class_='job_seen_beacon') or
                          soup.find_all('div', {'data-jk': True}) or
                          soup.find_all('div', class_='slider_container') or
                          soup.find_all('a', {'data-jk': True}))
            
            for element in job_elements[:limit]:
                try:
                    # Try different ways to extract job info
                    title_elem = (element.find('h2', class_='jobTitle') or
                                element.find('a', {'data-jk': True}) or
                                element.find('span', {'title': True}))
                    
                    company_elem = (element.find('span', class_='companyName') or
                                  element.find('a', {'data-testid': 'company-name'}) or
                                  element.find('div', class_='companyName'))
                    
                    if title_elem and company_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True)
                        
                        # Get URL if available
                        url_link = ""
                        link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
                        if link_elem and link_elem.get('href'):
                            url_link = f"https://www.indeed.com{link_elem['href']}"
                        
                        job = {
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'platform': 'Indeed',
                            'url': url_link,
                            'description': f"{title} at {company}",
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1
                        }
                        jobs.append(enhance_job_data(job))
                        
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    # If no jobs found, add some mock data for demo purposes
    if len(jobs) == 0:
        companies = ['GlobalTech Inc', 'InnovateCorp', 'Enterprise Solutions', 'MegaCorp', 'TechGiant', 'Innovation Labs', 'Digital Dynamics', 'Future Systems']
        roles = [
            f'{keywords.title()} Software Engineer', f'Full Stack {keywords.title()} Developer', f'Senior {keywords.title()} Developer',
            f'Software Engineer', f'Technical Lead', f'Engineering Manager', f'Data Engineer',
            f'Business Analyst', f'Project Manager', f'Product Owner', f'Scrum Master', f'Solutions Architect'
        ]
        
        mock_jobs = []
        for i in range(min(limit, 15)):  # Generate more jobs
            import random
            company = random.choice(companies)
            role = random.choice(roles)
            
            mock_jobs.append({
                'title': role,
                'company': company,
                'location': random.choice(['Remote', 'San Francisco, CA', 'New York, NY', 'Austin, TX']),
                'platform': 'Indeed',
                'description': f'{role} with competitive benefits at {company}',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': i + 1,
                'salary_range': f'${random.randint(70, 180)}k',
                'experience_level': random.choice(['Entry', 'Mid', 'Senior']),
            })
        
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_weworkremotely_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape WeWorkRemotely with fallback to mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        url = f"https://weworkremotely.com/remote-jobs/search?utf8=%E2%9C%93&term={quote(keywords)}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = soup.find_all('li', class_='feature')[:limit]
            
            for element in job_elements:
                try:
                    title_elem = element.find('span', class_='title')
                    company_elem = element.find('span', class_='company')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': 'Remote',
                            'platform': 'WeWorkRemotely',
                            'url': f"https://weworkremotely.com{element.find('a')['href']}" if element.find('a') else '',
                            'description': title_elem.get_text(strip=True),
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1
                        }
                        jobs.append(enhance_job_data(job))
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping WeWorkRemotely: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = [
            {
                'title': f'Remote {keywords.title()} Developer',
                'company': 'RemoteTech Solutions',
                'location': 'Remote',
                'platform': 'WeWorkRemotely',
                'url': 'https://weworkremotely.com',
                'description': f'Remote-first {keywords} developer opportunity',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': 1
            }
        ]
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_glassdoor_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape Glassdoor for live jobs."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={quote(keywords)}&locT=N&locId=11047&jobType=fulltime"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = soup.find_all('div', class_='react-job-listing')[:limit]
            
            for element in job_elements:
                try:
                    title_elem = element.find('a', attrs={'data-test': 'job-title'})
                    company_elem = element.find('span', attrs={'data-test': 'employer-name'})
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': 'Remote',
                            'platform': 'Glassdoor',
                            'url': f"https://www.glassdoor.com{title_elem['href']}" if title_elem.get('href') else '',
                            'description': title_elem.get_text(strip=True),
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1
                        }
                        jobs.append(enhance_job_data(job))
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping Glassdoor: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = [
            {
                'title': f'{keywords.title()} Engineer',
                'company': 'TechGlobal Corp',
                'location': 'Remote',
                'platform': 'Glassdoor',
                'url': 'https://www.glassdoor.com',
                'description': f'{keywords.title()} engineer at established tech company',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': 1
            }
        ]
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_angellist_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape AngelList/Wellfound for live jobs."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try both old AngelList and new Wellfound
        for base_url in ['https://angel.co', 'https://wellfound.com']:
            try:
                url = f"{base_url}/jobs?keywords={quote(keywords)}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_elements = soup.find_all('div', class_='startup-job-listing')[:limit//2]
                    
                    for element in job_elements:
                        try:
                            title_elem = element.find('h4') or element.find('h3')
                            company_elem = element.find('span', class_='startup-name')
                            
                            if title_elem and company_elem:
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True),
                                    'location': 'Remote',
                                    'platform': 'Wellfound',
                                    'url': f"{base_url}{element.find('a')['href']}" if element.find('a') else '',
                                    'description': title_elem.get_text(strip=True),
                                    'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                    'id': len(jobs) + 1
                                }
                                jobs.append(enhance_job_data(job))
                        except Exception as e:
                            continue
                break  # Exit loop if successful
            except Exception as e:
                continue
                    
    except Exception as e:
        print(f"Error scraping AngelList/Wellfound: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = [
            {
                'title': f'{keywords.title()} Developer',
                'company': 'StartupHub',
                'location': 'Remote',
                'platform': 'Wellfound',
                'url': 'https://wellfound.com',
                'description': f'{keywords.title()} developer at high-growth startup',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': 1
            }
        ]
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_nodesk_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape NoDesk for live remote jobs."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://nodesk.co/remote-jobs/"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = soup.find_all('div', class_='job-board-single')[:limit]
            
            for element in job_elements:
                try:
                    title_elem = element.find('h3') or element.find('h2')
                    company_elem = element.find('span', class_='company') or element.find('div', class_='company')
                    
                    if title_elem and company_elem:
                        title_text = title_elem.get_text(strip=True)
                        company_text = company_elem.get_text(strip=True)
                        
                        # Filter by keywords
                        if any(keyword.lower() in title_text.lower() for keyword in keywords.split()):
                            job = {
                                'title': title_text,
                                'company': company_text,
                                'location': 'Remote',
                                'platform': 'NoDesk',
                                'url': element.find('a')['href'] if element.find('a') else '',
                                'description': title_text,
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': len(jobs) + 1
                            }
                            jobs.append(enhance_job_data(job))
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping NoDesk: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = [
            {
                'title': f'Remote {keywords.title()} Specialist',
                'company': 'DistributedTeam',
                'location': 'Remote',
                'platform': 'NoDesk',
                'url': 'https://nodesk.co',
                'description': f'Remote-only {keywords} specialist opportunity',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': 1
            }
        ]
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_linkedin_live(keywords: str, limit: int = 30) -> List[Dict]:
    """Scrape LinkedIn for live jobs with comprehensive mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # LinkedIn is heavily protected, so we'll use comprehensive mock data
        # that represents real LinkedIn job opportunities
        pass  # LinkedIn requires authentication for scraping
        
    except Exception as e:
        print(f"Error scraping LinkedIn: {e}")
    
    # Comprehensive LinkedIn-style mock data covering multiple fields
    linkedin_companies = [
        'Microsoft', 'Google', 'Amazon', 'Meta', 'Apple', 'Netflix', 'Uber', 'Airbnb',
        'Salesforce', 'Oracle', 'IBM', 'Intel', 'Adobe', 'Tesla', 'SpaceX',
        'Goldman Sachs', 'JPMorgan Chase', 'Bank of America', 'Morgan Stanley',
        'McKinsey & Company', 'BCG', 'Bain & Company', 'Deloitte', 'PwC', 'EY', 'KPMG',
        'Johnson & Johnson', 'Pfizer', 'Merck', 'Novartis', 'Bristol Myers Squibb',
        'Stripe', 'Coinbase', 'Robinhood', 'Square', 'Plaid', 'Figma', 'Notion',
        'Zoom', 'Slack', 'Dropbox', 'Atlassian', 'ServiceNow', 'Snowflake',
        'TechCorp Solutions', 'InnovateNow', 'DataDriven Inc', 'CloudFirst Ltd',
        'AI Ventures', 'ScaleUp Technologies', 'NextGen Solutions', 'FutureTech Labs'
    ]
    
    job_roles = [
        f'{keywords.title()} Developer', f'Senior {keywords.title()} Engineer', 
        f'{keywords.title()} Software Engineer', f'Lead {keywords.title()} Developer',
        f'Full Stack {keywords.title()} Developer', f'{keywords.title()} Architect',
        f'Principal {keywords.title()} Engineer', f'{keywords.title()} Team Lead',
        f'Data Scientist', f'Machine Learning Engineer', f'AI Engineer',
        f'DevOps Engineer', f'Cloud Engineer', f'Security Engineer',
        f'Product Manager', f'Technical Product Manager', f'Engineering Manager',
        f'UI/UX Designer', f'Product Designer', f'Frontend Engineer',
        f'Backend Engineer', f'Mobile Developer', f'QA Engineer',
        f'Business Analyst', f'Data Analyst', f'Marketing Manager',
        f'Sales Engineer', f'Customer Success Manager', f'Account Executive',
        f'Operations Manager', f'HR Business Partner', f'Recruiter',
        f'Finance Analyst', f'Investment Analyst', f'Consultant',
        f'Research Scientist', f'Biotech Engineer', f'Pharmaceutical Researcher'
    ]
    
    locations = [
        'Remote', 'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX',
        'Boston, MA', 'Los Angeles, CA', 'Chicago, IL', 'Denver, CO', 'Atlanta, GA',
        'Remote - US', 'Remote - Global', 'Hybrid - SF Bay Area', 'Hybrid - NYC'
    ]
    
    # Generate diverse LinkedIn-style jobs
    import random
    for i in range(min(limit, 30)):
        company = random.choice(linkedin_companies)
        role = random.choice(job_roles)
        location = random.choice(locations)
        
        # Create realistic job descriptions
        tech_stacks = ['React', 'Node.js', 'Python', 'AWS', 'Docker', 'Kubernetes', 'TypeScript', 'GraphQL']
        benefits = ['Health Insurance', 'Stock Options', '401k Matching', 'Remote Work', 'Learning Budget']
        
        job = {
            'title': role,
            'company': company,
            'location': location,
            'platform': 'LinkedIn',
            'description': f'{role} at {company}. Technologies: {", ".join(random.sample(tech_stacks, 3))}. Benefits: {", ".join(random.sample(benefits, 2))}.',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'id': len(jobs) + 1,
            'salary_range': f'${random.randint(80, 200)}k - ${random.randint(200, 350)}k',
            'experience_level': random.choice(['Entry', 'Mid', 'Senior', 'Lead']),
            'employment_type': random.choice(['Full-time', 'Contract', 'Part-time'])
        }
        jobs.append(enhance_job_data(job))
    
    return jobs

# Flask Routes
@app.route('/')
def dashboard():
    """Main dashboard."""
    return demo()

@app.route('/api/live-scrape', methods=['POST'])
def live_scrape():
    """Live scraping endpoint with advanced real-time scraping and database integration."""
    global live_jobs, scraping_status
    
    data = request.get_json()
    keywords = data.get('keywords', 'python developer')
    platforms = data.get('platforms', ['linkedin', 'remoteok', 'indeed', 'weworkremotely', 'glassdoor', 'wellfound', 'nodesk'])
    use_advanced = data.get('use_advanced_scraper', True)  # Enable by default
    
    scraping_status['running'] = True
    scraping_status['last_search'] = keywords
    scraping_status['job_count'] = 0
    
    live_jobs.clear()
    
    try:
        total_leads_before = len(business_leads) if not db else 0
        
        # Try advanced scraper first if available
        if use_advanced and ADVANCED_SCRAPER_ENABLED and advanced_scraper:
            print("🚀 Using advanced real-time scraper...")
            scrape_results = advanced_scraper.scrape_all_platforms(keywords)
            
            # Process and enhance jobs from advanced scraper
            for job in scrape_results['all_jobs']:
                enhanced_job = enhance_job_data(job)
                live_jobs.append(enhanced_job)
            
            scraping_status['scraper_type'] = 'advanced'
            scraping_status['real_time_data'] = True
            
        else:
            # Fallback to original scraping method
            print("📊 Using standard scraper...")
            for platform in platforms:
                if platform == 'linkedin':
                    platform_jobs = scrape_linkedin_live(keywords, 30)
                    live_jobs.extend(platform_jobs)
                elif platform == 'remoteok':
                    platform_jobs = scrape_remoteok_live(keywords, 25)
                    live_jobs.extend(platform_jobs)
                elif platform == 'indeed':
                    platform_jobs = scrape_indeed_live(keywords, 25)
                    live_jobs.extend(platform_jobs)
                elif platform == 'weworkremotely':
                    platform_jobs = scrape_weworkremotely_live(keywords, 20)
                    live_jobs.extend(platform_jobs)
                elif platform == 'glassdoor':
                    platform_jobs = scrape_glassdoor_live(keywords, 20)
                    live_jobs.extend(platform_jobs)
                elif platform == 'wellfound':
                    platform_jobs = scrape_angellist_live(keywords, 20)
                    live_jobs.extend(platform_jobs)
                elif platform == 'nodesk':
                    platform_jobs = scrape_nodesk_live(keywords, 15)
                    live_jobs.extend(platform_jobs)
                
                time.sleep(1)  # Rate limiting
            
            scraping_status['scraper_type'] = 'standard'
            scraping_status['real_time_data'] = False
        
        scraping_status['job_count'] = len(live_jobs)
        
        # Save search history to database
        if db and hasattr(db, 'save_search_history'):
            try:
                total_leads_after = len(business_leads) if not db else 0
                if hasattr(db, 'get_business_leads'):
                    db_leads = db.get_business_leads(limit=1000)
                    total_leads_after = len(db_leads)
                
                leads_generated = max(0, total_leads_after - total_leads_before)
                db.save_search_history(keywords, platforms, len(live_jobs), leads_generated)
            except Exception as e:
                print(f"Error saving search history: {e}")
        
    except Exception as e:
        print(f"Error in live scraping: {e}")
    finally:
        scraping_status['running'] = False
    
    return jsonify({
        'success': True,
        'jobs_found': len(live_jobs),
        'platforms_scraped': platforms,
        'database_enabled': db is not None,
        'scraper_type': scraping_status.get('scraper_type', 'standard'),
        'real_time_data': scraping_status.get('real_time_data', False)
    })

@app.route('/api/scraping-status')
def scraping_status_endpoint():
    """Get current scraping status."""
    return jsonify(scraping_status)

@app.route('/api/refresh-jobs', methods=['POST'])
def refresh_jobs():
    """Manually refresh job data with real-time scraping."""
    if not ADVANCED_SCRAPER_ENABLED or not advanced_scraper:
        return jsonify({
            'success': False,
            'error': 'Advanced scraper not available',
            'fallback': 'Use /api/live-scrape endpoint'
        }), 503
    
    data = request.get_json()
    keywords = data.get('keywords', 'python developer')
    
    try:
        print(f"🔄 Refreshing jobs for: {keywords}")
        results = advanced_scraper.scrape_all_platforms(keywords)
        
        # Process and enhance jobs
        refreshed_jobs = []
        for job in results['all_jobs']:
            enhanced = enhance_job_data(job)
            refreshed_jobs.append(enhanced)
            
            # Update live_jobs list
            live_jobs.append(enhanced)
        
        return jsonify({
            'success': True,
            'jobs_refreshed': len(refreshed_jobs),
            'total_jobs': len(live_jobs),
            'platform_stats': {
                'linkedin': len(results.get('linkedin', [])),
                'indeed': len(results.get('indeed', [])),
                'remoteok': len(results.get('remoteok', [])),
                'weworkremotely': len(results.get('weworkremotely', []))
            },
            'real_time': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/live-jobs')
def live_jobs_endpoint():
    """Get live scraped jobs with database integration."""
    search = request.args.get('search', '').lower()
    limit = int(request.args.get('limit', 50))
    
    # Try to get jobs from database first
    if db and hasattr(db, 'get_jobs'):
        try:
            db_jobs = db.get_jobs(limit=limit, search=search if search else None)
            if db_jobs:
                # Convert database jobs to the expected format
                formatted_jobs = []
                for job in db_jobs:
                    # Add business intelligence if not present
                    if 'lead_score' not in job:
                        enhanced_job = enhance_job_data(job)
                        formatted_jobs.append(enhanced_job)
                    else:
                        formatted_jobs.append(job)
                return jsonify(formatted_jobs)
        except Exception as e:
            print(f"Error getting jobs from database: {e}")
    
    # Fallback to in-memory storage
    filtered_jobs = live_jobs
    
    if search:
        filtered_jobs = [
            job for job in live_jobs
            if search in job.get('title', '').lower() or 
               search in job.get('company', '').lower() or
               search in job.get('description', '').lower()
        ]
    
    return jsonify(filtered_jobs[:limit])

@app.route('/api/business-leads')
def business_leads_endpoint():
    """Get business leads for lead generation with database integration."""
    min_score = int(request.args.get('min_score', 40))
    limit = int(request.args.get('limit', 50))
    
    # Try to get leads from database first
    if db and hasattr(db, 'get_business_leads'):
        try:
            db_leads = db.get_business_leads(limit=limit, min_score=min_score)
            if db_leads:
                high_value_leads = len([l for l in db_leads if l.get('lead_score', 0) >= 70])
                platforms_tracked = list(set(l.get('platform', 'Unknown') for l in db_leads))
                
                return jsonify({
                    'leads': db_leads,
                    'total_leads': len(db_leads),
                    'high_value_leads': high_value_leads,
                    'platforms_tracked': platforms_tracked,
                    'database_enabled': True
                })
        except Exception as e:
            print(f"Error getting business leads from database: {e}")
    
    # Fallback to in-memory storage
    filtered_leads = [l for l in business_leads if l.get('lead_score', 0) >= min_score]
    limited_leads = filtered_leads[-limit:] if len(filtered_leads) > limit else filtered_leads
    
    return jsonify({
        'leads': limited_leads,
        'total_leads': len(business_leads),
        'high_value_leads': len([l for l in business_leads if l.get('lead_score', 0) >= 70]),
        'platforms_tracked': list(set(l.get('platform', 'Unknown') for l in business_leads)),
        'database_enabled': False
    })

@app.route('/api/generate-outreach', methods=['POST'])
def generate_outreach():
    """Generate personalized outreach templates for a lead."""
    if not OUTREACH_TEMPLATES_ENABLED:
        return jsonify({
            'success': False,
            'message': 'Outreach templates module not available'
        })
    
    data = request.get_json()
    
    # Lead data
    lead_data = {
        'company': data.get('company'),
        'title': data.get('job_title'),
        'contact_name': data.get('contact_name', 'there'),
        'contact_title': data.get('contact_title', ''),
        'company_size': data.get('company_size', 'Growing'),
        'tech_stack': data.get('tech_stack', 'modern technologies'),
        'platform': data.get('platform', 'LinkedIn'),
        'lead_score': data.get('lead_score', 50)
    }
    
    # Sender data (you can make this configurable)
    sender_data = {
        'name': data.get('sender_name', 'Alex Johnson'),
        'title': data.get('sender_title', 'Business Development Director'),
        'company': data.get('sender_company', 'TechScale Solutions'),
        'email': data.get('sender_email', 'alex@techscale.com'),
        'phone': data.get('sender_phone', '+1 (555) 123-4567')
    }
    
    try:
        # Generate complete outreach sequence
        sequence = outreach_personalizer.get_outreach_sequence(lead_data, sender_data)
        
        # Get template recommendations
        recommendations = outreach_personalizer.get_template_recommendations(lead_data)
        
        return jsonify({
            'success': True,
            'outreach_sequence': sequence,
            'recommendations': recommendations,
            'total_templates': len(sequence),
            'lead_data_quality': lead_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating outreach templates: {str(e)}'
        })

@app.route('/api/discover-contacts', methods=['POST'])
def discover_contacts():
    """Discover contact information for a company."""
    if not CONTACT_DISCOVERY_ENABLED:
        return jsonify({
            'success': False,
            'message': 'Contact discovery module not available'
        })
    
    data = request.get_json()
    company_name = data.get('company_name')
    job_title = data.get('job_title', '')
    job_url = data.get('job_url', '')
    
    if not company_name:
        return jsonify({
            'success': False,
            'message': 'Company name is required'
        })
    
    try:
        # Discover contacts
        contact_results = contact_discovery.discover_contacts(company_name, job_title, job_url)
        
        # Save contact information to database if available
        if db and contact_results.get('confidence_score', 0) > 0:
            try:
                # Find corresponding job in database
                jobs = db.search_jobs(keywords=job_title, limit=100)
                matching_job = next((job for job in jobs if job.get('company', '').lower() == company_name.lower()), None)
                
                if matching_job:
                    # Save contacts to job record
                    all_emails = contact_results.get('direct_emails', []) + [
                        guess['email'] for guess in contact_results.get('guessed_emails', [])
                    ]
                    
                    contact_sources = {}
                    for email in contact_results.get('direct_emails', []):
                        contact_sources[email] = {'source': 'website_scrape', 'verified': True, 'type': 'extracted'}
                    
                    for guess in contact_results.get('guessed_emails', []):
                        email = guess['email']
                        contact_sources[email] = {
                            'source': 'name_pattern', 
                            'verified': False, 
                            'type': 'guessed',
                            'confidence': guess.get('confidence', 0.5)
                        }
                    
                    if hasattr(db, 'save_job_contacts'):
                        db.save_job_contacts(
                            matching_job['id'], 
                            all_emails, 
                            contact_sources, 
                            contact_results.get('domain')
                        )
                        
            except Exception as e:
                print(f"Error saving contact info to database: {e}")
        
        return jsonify({
            'success': True,
            'contacts': contact_results,
            'database_saved': db is not None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error discovering contacts: {str(e)}'
        })

@app.route('/api/lead-analysis/<company>')
def lead_analysis(company):
    """Get detailed lead analysis and scoring breakdown."""
    # Try to get lead from database first
    if db and hasattr(db, 'get_business_leads'):
        try:
            leads = db.get_business_leads(limit=1000)
            matching_lead = next((lead for lead in leads if lead.get('company', '').lower() == company.lower()), None)
            
            if matching_lead:
                return jsonify({
                    'success': True,
                    'lead': matching_lead,
                    'analysis_available': True
                })
        except Exception as e:
            print(f"Error getting lead analysis from database: {e}")
    
    # Fallback to in-memory search
    matching_lead = next((lead for lead in business_leads if lead.get('company', '').lower() == company.lower()), None)
    
    if matching_lead:
        return jsonify({
            'success': True,
            'lead': matching_lead,
            'analysis_available': False
        })
    
    return jsonify({
        'success': False,
        'message': 'Lead not found'
    })

@app.route('/api/stats')
def stats():
    """Get dashboard statistics with database integration."""
    # Try to get stats from database first
    if db and hasattr(db, 'get_stats'):
        try:
            db_stats = db.get_stats()
            if db_stats:
                return jsonify({
                    'total_jobs': db_stats.get('total_jobs', 0),
                    'total_leads': db_stats.get('total_leads', 0),
                    'high_value_leads': db_stats.get('high_value_leads', 0),
                    'platforms_active': 7,
                    'last_search': scraping_status.get('last_search', 'None'),
                    'search_status': 'Running' if scraping_status.get('running') else 'Ready',
                    'database_enabled': True,
                    'recent_searches': db_stats.get('recent_searches', 0),
                    'top_platforms': db_stats.get('top_platforms', [])
                })
        except Exception as e:
            print(f"Error getting stats from database: {e}")
    
    # Fallback to in-memory statistics
    return jsonify({
        'total_jobs': len(live_jobs),
        'total_leads': len(business_leads),
        'high_value_leads': len([l for l in business_leads if l.get('lead_score', 0) >= 70]),
        'platforms_active': 7,
        'last_search': scraping_status.get('last_search', 'None'),
        'search_status': 'Running' if scraping_status.get('running') else 'Ready',
        'database_enabled': False
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/demo')
def demo():
    """Demo page with embedded HTML."""
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Business Development Platform - Lead Generation</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem 0; text-align: center; }
            .container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }
            .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem; }
            .card { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
            .search-form { margin-bottom: 2rem; }
            .form-group { margin-bottom: 1rem; }
            .form-control { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; }
            .btn { padding: 0.75rem 2rem; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }
            .btn:hover { background: #5a67d8; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
            .stat-card { background: white; padding: 1.5rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
            .stat-number { font-size: 2rem; font-weight: bold; color: #667eea; }
            .job-card { background: white; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
            .job-title { font-size: 1.25rem; font-weight: bold; color: #2d3748; margin-bottom: 0.5rem; }
            .job-company { font-size: 1rem; color: #667eea; margin-bottom: 0.5rem; }
            .job-meta { display: flex; gap: 1rem; margin-bottom: 1rem; }
            .meta-item { background: #f7fafc; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; }
            .job-actions { margin-top: 1rem; display: flex; gap: 1rem; }
            .btn-apply { background: #48bb78; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-apply:hover { background: #38a169; }
            .btn-view { background: #4299e1; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-view:hover { background: #3182ce; }
            .btn-contact { background: #ed8936; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-contact:hover { background: #dd6b20; }
            .job-url { color: #4299e1; text-decoration: none; font-size: 0.875rem; }
            .job-url:hover { text-decoration: underline; }
            .lead-score { padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: bold; }
            .score-high { background: #c6f6d5; color: #22543d; }
            .score-medium { background: #fed7d7; color: #742a2a; }
            .score-low { background: #e2e8f0; color: #4a5568; }
            .status { margin-top: 1rem; padding: 1rem; background: #f7fafc; border-radius: 8px; text-align: center; }
            .hidden { display: none; }
            .score-excellent { background: #9ae6b4; color: #1a202c; }
            .score-breakdown { font-size: 0.75rem; margin-top: 0.5rem; }
            .score-breakdown details { margin-top: 0.25rem; }
            .score-breakdown summary { cursor: pointer; color: #667eea; font-weight: 500; }
            .btn-view-job { background: #38a169; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-view-job:hover { background: #2f855a; }
            .btn-outreach { background: #9f7aea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-outreach:hover { background: #805ad5; }
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
            .modal-content { background: white; margin: 2% auto; padding: 2rem; width: 90%; max-width: 800px; border-radius: 12px; max-height: 90vh; overflow-y: auto; }
            .close { float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
            .outreach-template { background: #f8fafc; padding: 1rem; margin: 1rem 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .template-header { font-weight: bold; color: #667eea; margin-bottom: 0.5rem; }
            .template-subject { font-weight: 600; margin-bottom: 0.5rem; background: #e2e8f0; padding: 0.5rem; border-radius: 4px; }
            .template-body { white-space: pre-wrap; font-family: monospace; font-size: 0.875rem; line-height: 1.4; }
            .copy-template { background: #48bb78; color: white; padding: 0.25rem 0.75rem; border: none; border-radius: 4px; cursor: pointer; margin-top: 0.5rem; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>🚀 Business Development Platform</h1>
                <p>Lead Generation Through Job Market Intelligence</p>
            </div>
        </div>

        <div class="container">
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalJobs">0</div>
                    <div>Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalLeads">0</div>
                    <div>Business Leads</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="highValueLeads">0</div>
                    <div>High-Value Leads</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="platformsActive">7</div>
                    <div>Platforms Active</div>
                </div>
            </div>

            <div class="dashboard">
                <div class="card">
                    <h2>🎯 Lead Generation Search</h2>
                    <div class="search-form">
                        <div class="form-group">
                            <input type="text" id="keywords" class="form-control" placeholder="Enter technology keywords (e.g., python developer, react engineer)" value="python developer">
                        </div>
                        <button onclick="startLiveScraping()" class="btn">🔍 Find Business Opportunities</button>
                    </div>
                    <div id="scrapingStatus" class="status hidden">
                        <div>🔄 Scanning job market for opportunities...</div>
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Business Intelligence</h2>
                    <div id="businessLeads">
                        <p>Start a search to identify potential clients and business opportunities.</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>💼 Market Opportunities</h2>
                <div id="liveJobs">
                    <p>No active search. Click "Find Business Opportunities" to discover companies hiring for tech roles.</p>
                </div>
            </div>
        </div>

        <!-- Outreach Templates Modal -->
        <div id="outreachModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeOutreachModal()">&times;</span>
                <h2>📧 Professional Outreach Templates</h2>
                <div id="outreachContent">
                    <p>Generating personalized outreach sequence...</p>
                </div>
            </div>
        </div>

        <script>
            let searchInterval;

            async function startLiveScraping() {
                const keywords = document.getElementById('keywords').value;
                const statusDiv = document.getElementById('scrapingStatus');
                
                if (!keywords.trim()) {
                    alert('Please enter keywords to search for business opportunities');
                    return;
                }

                statusDiv.classList.remove('hidden');
                
                try {
                    const response = await fetch('/api/live-scrape', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            keywords: keywords,
                            platforms: ['linkedin', 'remoteok', 'indeed', 'weworkremotely', 'glassdoor', 'wellfound', 'nodesk']
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.innerHTML = `✅ Found ${result.jobs_found} opportunities across ${result.platforms_scraped.length} platforms`;
                        setTimeout(() => {
                            statusDiv.classList.add('hidden');
                            loadLiveJobs();
                            loadBusinessLeads();
                            loadStats();
                        }, 2000);
                    } else {
                        statusDiv.innerHTML = '❌ Search failed. Please try again.';
                    }
                } catch (error) {
                    statusDiv.innerHTML = '❌ Error occurred. Please try again.';
                    console.error('Search error:', error);
                }
            }

            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    document.getElementById('totalJobs').textContent = stats.total_jobs;
                    document.getElementById('totalLeads').textContent = stats.total_leads;
                    document.getElementById('highValueLeads').textContent = stats.high_value_leads;
                    document.getElementById('platformsActive').textContent = stats.platforms_active;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }

            async function loadLiveJobs() {
                try {
                    const response = await fetch('/api/live-jobs');
                    const jobs = await response.json();
                    
                    const container = document.getElementById('liveJobs');
                    
                    if (jobs.length === 0) {
                        container.innerHTML = '<p>No opportunities found. Try different keywords.</p>';
                        return;
                    }
                    
                    container.innerHTML = jobs.map(job => `
                        <div class="job-card">
                            <div class="job-title">${job.title}</div>
                            <div class="job-company">${job.company}</div>
                            <div class="job-meta">
                                <span class="meta-item">📍 ${job.location}</span>
                                <span class="meta-item">🏢 ${job.platform}</span>
                                <span class="meta-item">💼 ${job.company_size || 'Unknown'}</span>
                                <span class="lead-score ${getScoreClass(job.lead_score)}">
                                    Score: ${job.lead_score || 0}%
                                </span>
                            </div>
                            <div class="meta-item">🛠️ ${job.tech_stack || 'General'}</div>
                            ${job.salary_range ? `<div class="meta-item">💰 ${job.salary_range}</div>` : ''}
                            <div class="job-actions">
                                <button class="btn-view" onclick="researchCompany('${job.company}', '${job.title}')">� Research Company</button>
                                <button class="btn-contact" onclick="contactCompany('${job.company}', '${job.title}')">� Get Contact Info</button>
                                <button class="btn-apply" onclick="saveAsLead('${job.company}', '${job.title}', ${job.lead_score})">⭐ Save Lead</button>
                            </div>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading jobs:', error);
                }
            }

            async function loadBusinessLeads() {
                try {
                    const response = await fetch('/api/business-leads');
                    const data = await response.json();
                    
                    const container = document.getElementById('businessLeads');
                    
                    if (data.leads.length === 0) {
                        container.innerHTML = '<p>No qualified leads yet. Start searching to identify potential clients.</p>';
                        return;
                    }
                    
                    container.innerHTML = `
                        <div style="margin-bottom: 1rem;">
                            <strong>Qualified Leads: ${data.total_leads}</strong> | 
                            <strong>High-Value: ${data.high_value_leads}</strong>
                        </div>
                        ${data.leads.slice(-10).map(lead => `
                            <div class="job-card">
                                <div class="job-title">${lead.title}</div>
                                <div class="job-company">🏢 ${lead.company}</div>
                                <div class="job-meta">
                                    <span class="meta-item">📍 ${lead.location}</span>
                                    <span class="meta-item">💼 ${lead.company_size}</span>
                                    <span class="lead-score ${getScoreClass(lead.lead_score)}">
                                        ${lead.contact_potential} Value (${lead.lead_score}%)
                                    </span>
                                </div>
                                <div class="meta-item">🛠️ ${lead.technologies.join(', ') || 'General Tech'}</div>
                                <div class="job-actions">
                                    <button class="btn-view" onclick="researchCompany('${lead.company}', '${lead.title}')">� Research Company</button>
                                    <button class="btn-contact" onclick="contactCompany('${lead.company}', '${lead.title}')">📧 Business Contact</button>
                                    <button class="btn-apply" onclick="saveAsLead('${lead.company}', '${lead.title}', ${lead.lead_score})">⭐ Save Lead</button>
                                </div>
                            </div>
                        `).join('')}
                    `;
                } catch (error) {
                    console.error('Error loading business leads:', error);
                }
            }

            function getScoreClass(score) {
                if (score >= 85) return 'score-excellent';
                if (score >= 70) return 'score-high';
                if (score >= 40) return 'score-medium';
                return 'score-low';
            }

            // Business development functions with contact discovery
            async function researchCompany(company, jobTitle) {
                const researchSteps = `🔍 COMPANY RESEARCH: ${company}

QUICK RESEARCH CHECKLIST:
✅ Company Website: Search "${company} official website"
✅ LinkedIn Page: Search "${company}" on LinkedIn
✅ Recent News: Google "${company} news 2024"
✅ Funding/Growth: Check "${company} funding" or "Series A/B"
✅ Tech Stack: Look for "${company} technology stack" or engineering blog
✅ Hiring Scale: Count recent job postings on their careers page

BUSINESS OPPORTUNITY ASSESSMENT:
• Position: ${jobTitle}
• Why they're a lead: Actively hiring for tech roles
• Your angle: They need tech talent = potential for your services
• Best approach: Offer to augment their ${jobTitle} search

NEXT STEPS:
1. Visit their company website
2. Find their "Careers" or "About" page
3. Look for contact information or leadership team
4. Check their LinkedIn company page for employees
5. Identify decision makers (CTO, Head of Engineering, HR)`;

                // Copy research plan to clipboard
                try {
                    await navigator.clipboard.writeText(researchSteps);
                    alert(`🔍 Research plan for ${company} copied to clipboard!
                    
The research checklist will help you:
• Understand their business model
• Identify key decision makers  
• Find the best contact approach
• Position your services effectively

Start with their website and LinkedIn page.`);
                } catch (err) {
                    alert(`Research ${company} for ${jobTitle}:
                    
1. Google: "${company} official website"
2. LinkedIn: Search "${company}" 
3. Check their careers page
4. Look for engineering team contacts
5. Identify decision makers (CTO, Engineering Manager)`);
                }
            }

            async function contactCompany(company, jobTitle) {
                // Show loading state
                const button = event.target;
                const originalText = button.textContent;
                button.textContent = '🔍 Finding Contacts...';
                button.disabled = true;

                try {
                    // Try automated contact discovery first
                    const response = await fetch('/api/discover-contacts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            company_name: company,
                            job_title: jobTitle
                        })
                    });

                    const result = await response.json();

                    if (result.success && result.contacts) {
                        const contacts = result.contacts;
                        let contactInfo = `📧 AUTOMATED CONTACT DISCOVERY: ${company}

🎯 FOUND CONTACT INFORMATION:
${contacts.domain ? `🌐 Company Website: https://${contacts.domain}` : ''}
${contacts.confidence_score ? `✅ Discovery Confidence: ${contacts.confidence_score}%` : ''}

`;

                        // Add direct emails if found
                        if (contacts.direct_emails && contacts.direct_emails.length > 0) {
                            contactInfo += `📧 VERIFIED EMAIL ADDRESSES:
${contacts.direct_emails.map(email => `• ${email}`).join('\\n')}

`;
                        }

                        // Add email guesses for decision makers
                        if (contacts.guessed_emails && contacts.guessed_emails.length > 0) {
                            const decisionMakerEmails = contacts.guessed_emails
                                .filter(guess => guess.is_decision_maker)
                                .sort((a, b) => b.confidence - a.confidence);

                            if (decisionMakerEmails.length > 0) {
                                contactInfo += `👨‍💼 DECISION MAKER CONTACTS (Likely):
${decisionMakerEmails.slice(0, 5).map(guess => 
    `• ${guess.email} (${guess.name}, ${guess.title}) - ${Math.round(guess.confidence * 100)}% confidence`
                                ).join('\\n')}

`;
                            }
                        }

                        // Add LinkedIn profiles
                        if (contacts.linkedin_profiles && contacts.linkedin_profiles.length > 0) {
                            contactInfo += `🔗 LINKEDIN PROFILES:
${contacts.linkedin_profiles.slice(0, 3).map(profile => `• ${profile}`).join('\\n')}

`;
                        }

                        contactInfo += `📋 OUTREACH STRATEGY:
1. Start with verified emails (highest success rate)
2. Connect with decision makers on LinkedIn first
3. Use warm introduction through mutual connections
4. Mention their ${jobTitle} hiring as conversation starter

💡 PROFESSIONAL MESSAGE TEMPLATE:
"Hi [Name],

I noticed ${company} is actively hiring for ${jobTitle} roles. As a tech solutions partner, we help companies like yours scale engineering teams faster with dedicated developers and project-based technical expertise.

Instead of just filling positions, we offer:
• Immediate technical capacity
• Specialized skill sets for specific projects
• Flexible engagement models

Would you be open to a brief conversation about how we could support ${company}'s technology initiatives?

Best regards,
[Your Name]"`;

                        // Copy to clipboard
                        await navigator.clipboard.writeText(contactInfo);
                        alert(`📧 Automated contact discovery complete for ${company}!

Found:
• ${contacts.direct_emails ? contacts.direct_emails.length : 0} verified emails
• ${contacts.guessed_emails ? contacts.guessed_emails.length : 0} contact guesses
• ${contacts.linkedin_profiles ? contacts.linkedin_profiles.length : 0} LinkedIn profiles
• ${contacts.decision_makers ? contacts.decision_makers.length : 0} decision makers

Full contact strategy copied to clipboard!`);
                    } else {
                        throw new Error('Automated discovery failed');
                    }

                } catch (error) {
                    console.error('Contact discovery error:', error);
                    
                    // Fallback to manual strategy
                    const manualContactInfo = `📧 CONTACT STRATEGY: ${company}

STEP 1: FIND DECISION MAKERS
• Search LinkedIn: "${company}" + "CTO" or "Head of Engineering"
• Check company website for leadership team
• Look for "Engineering" or "Technology" team members
• Find recent ${jobTitle} job posting authors

STEP 2: CONTACT METHODS
🔸 LinkedIn: Best for initial outreach
🔸 Company Email: info@[company].com or careers@[company].com  
🔸 Contact Forms: Usually on company website
🔸 Twitter/X: Many CTOs are active on Twitter

STEP 3: OUTREACH MESSAGE TEMPLATE
Subject: Partnership Opportunity - Tech Talent Solutions

Hi [Name],

I noticed ${company} is actively hiring for ${jobTitle} roles. As a tech service startup, we specialize in providing skilled developers and technical solutions that could complement your growing team.

Instead of just filling positions, we offer:
• Dedicated development teams
• Project-based technical solutions  
• Flexible scaling for your engineering needs

Would you be open to a brief conversation about how we could support ${company}'s technology initiatives?

Best regards,
[Your Name]
[Your Company]

STEP 4: FOLLOW-UP PLAN
• Initial contact via LinkedIn
• Follow up via email after 1 week
• Provide case studies or portfolio
• Offer free consultation or pilot project`;

                    try {
                        await navigator.clipboard.writeText(manualContactInfo);
                        alert(`📧 Manual contact strategy for ${company} copied!
                        
This includes:
✅ How to find decision makers
✅ Best contact methods
✅ Professional outreach template
✅ Follow-up strategy

Start with LinkedIn to find their CTO or Engineering Manager.`);
                    } catch (err) {
                        alert(`Contact ${company} about ${jobTitle}:
                        
1. Find their CTO/Engineering Manager on LinkedIn
2. Send professional connection request
3. Mention their ${jobTitle} hiring
4. Offer tech services as partnership
5. Follow up with portfolio/case studies`);
                    }
                } finally {
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                }
            }

            function saveAsLead(company, jobTitle, leadScore) {
                const leadData = {
                    company: company,
                    position: jobTitle,
                    score: leadScore,
                    date: new Date().toLocaleDateString(),
                    status: 'New Lead'
                };

                // Store in localStorage for now (in real app, would send to backend)
                let savedLeads = JSON.parse(localStorage.getItem('businessLeads') || '[]');
                savedLeads.push(leadData);
                localStorage.setItem('businessLeads', JSON.stringify(savedLeads));

                alert(`⭐ ${company} saved as a business lead!
                
Lead Score: ${leadScore}%
Position: ${jobTitle}
Status: Ready for outreach

Tip: They're actively hiring, making this an ideal time to propose your tech services.`);
            }

            // Outreach Template Functions
            async function generateOutreach(company, jobTitle, companySize, techStack, leadScore) {
                document.getElementById('outreachModal').style.display = 'block';
                document.getElementById('outreachContent').innerHTML = '<p>🔄 Generating personalized outreach sequence...</p>';

                try {
                    const response = await fetch('/api/generate-outreach', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            company: company,
                            job_title: jobTitle,
                            company_size: companySize || 'Growing',
                            tech_stack: techStack || 'modern technologies',
                            lead_score: leadScore || 50,
                            platform: 'LinkedIn'
                        })
                    });

                    const result = await response.json();

                    if (result.success) {
                        displayOutreachSequence(result.outreach_sequence, result.recommendations, company);
                    } else {
                        throw new Error(result.message || 'Failed to generate outreach');
                    }

                } catch (error) {
                    console.error('Outreach generation error:', error);
                    document.getElementById('outreachContent').innerHTML = `
                        <p>❌ Error generating outreach templates. Falling back to manual templates...</p>
                        <div class="outreach-template">
                            <div class="template-header">📧 Manual Outreach Template</div>
                            <div class="template-subject">Partnership Opportunity - ${company} Technology Initiatives</div>
                            <div class="template-body">Hi there,

I noticed ${company} is actively hiring for ${jobTitle} roles, which suggests exciting growth in your technology team.

I'm reaching out because we specialize in providing dedicated development teams and technical solutions that complement in-house engineering efforts.

Would you be open to a brief conversation about how we could support ${company}'s technology initiatives?

Best regards,
[Your Name]</div>
                            <button class="copy-template" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋 Copy Template</button>
                        </div>
                    `;
                }
            }

            function displayOutreachSequence(sequence, recommendations, company) {
                let html = `
                    <div style="margin-bottom: 1rem;">
                        <h3>🎯 Outreach Strategy for ${company}</h3>
                        <p><strong>Total Templates:</strong> ${sequence.length} | <strong>Sequence Duration:</strong> ~2 months</p>
                    </div>
                `;

                if (recommendations && recommendations.length > 0) {
                    html += `
                        <div style="background: #e6fffa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                            <h4>💡 Strategy Recommendations:</h4>
                            ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </div>
                    `;
                }

                sequence.forEach((template, index) => {
                    const typeEmoji = {
                        'initial': '🎯',
                        'follow_up': '🔄',
                        'value_add': '💎',
                        'final': '🏁'
                    };

                    html += `
                        <div class="outreach-template">
                            <div class="template-header">
                                ${typeEmoji[template.template_type] || '📧'} ${template.template_name}
                                <span style="float: right; font-size: 0.875rem; color: #666;">
                                    ${index === 0 ? 'Send Now' : `Send in ${template.follow_up_days} days`}
                                </span>
                            </div>
                            <div class="template-subject">Subject: ${template.subject}</div>
                            <div class="template-body">${template.body}</div>
                            <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #666;">
                                <strong>Personalization Score:</strong> ${template.personalization_score}% | 
                                <strong>Follow-up Date:</strong> ${template.follow_up_date}
                            </div>
                            <button class="copy-template" onclick="copyTemplate('${template.subject}', \`${template.body.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)">📋 Copy Template</button>
                        </div>
                    `;
                });

                html += `
                    <div style="margin-top: 2rem; padding: 1rem; background: #f0f9ff; border-radius: 8px;">
                        <h4>📊 Outreach Best Practices:</h4>
                        <ul>
                            <li>Send initial email on Tuesday-Thursday, 9-11 AM</li>
                            <li>Follow up consistently but not aggressively</li>
                            <li>Always provide value in each touchpoint</li>
                            <li>Personalize based on company news and updates</li>
                            <li>Track responses and adjust strategy accordingly</li>
                        </ul>
                    </div>
                `;

                document.getElementById('outreachContent').innerHTML = html;
            }

            function copyTemplate(subject, body) {
                const fullTemplate = `Subject: ${subject}

${body}`;
                
                copyToClipboard(fullTemplate);
                alert('📧 Template copied to clipboard! Ready to paste into your email client.');
            }

            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(() => {
                    console.log('Text copied to clipboard');
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                });
            }

            function closeOutreachModal() {
                document.getElementById('outreachModal').style.display = 'none';
            }

            // Close modal when clicking outside
            window.onclick = function(event) {
                const modal = document.getElementById('outreachModal');
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            }

            // Load initial data
            loadStats();
            
            // Handle Enter key
            document.getElementById('keywords').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    startLiveScraping();
                }
            });
        </script>
    </body>
    </html>
    '''
    return html

# ===== EMAIL AUTOMATION ENDPOINTS =====

@app.route('/api/email/send', methods=['POST'])
def send_email():
    """Send email via Gmail or Outlook."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    provider = data.get('provider', 'gmail').lower()  # gmail or outlook
    
    required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 
                      'recipient_email', 'subject', 'body']
    
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    if provider == 'gmail':
        result = email_automation.send_email_gmail(
            smtp_server=data['smtp_server'],
            smtp_port=data['smtp_port'],
            sender_email=data['sender_email'],
            sender_password=data['sender_password'],
            recipient_email=data['recipient_email'],
            subject=data['subject'],
            body=data['body'],
            is_html=data.get('is_html', True)
        )
    elif provider == 'outlook':
        result = email_automation.send_email_outlook(
            smtp_server=data['smtp_server'],
            smtp_port=data['smtp_port'],
            sender_email=data['sender_email'],
            sender_password=data['sender_password'],
            recipient_email=data['recipient_email'],
            subject=data['subject'],
            body=data['body'],
            is_html=data.get('is_html', True)
        )
    else:
        return jsonify({
            'success': False,
            'error': f'Unsupported provider: {provider}. Use "gmail" or "outlook"'
        }), 400
    
    return jsonify(result)

@app.route('/api/email/sequence/create', methods=['POST'])
def create_sequence():
    """Create automated email sequence."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    
    if 'sequence_name' not in data or 'emails' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: sequence_name, emails'
        }), 400
    
    result = email_automation.create_email_sequence(
        sequence_name=data['sequence_name'],
        emails=data['emails']
    )
    
    return jsonify(result)

@app.route('/api/email/sequence/start', methods=['POST'])
def start_sequence():
    """Start email sequence for a recipient."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    
    if 'sequence_id' not in data or 'recipient_email' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: sequence_id, recipient_email'
        }), 400
    
    result = email_automation.start_email_sequence(
        sequence_id=data['sequence_id'],
        recipient_email=data['recipient_email'],
        personalization=data.get('personalization', {})
    )
    
    return jsonify(result)

@app.route('/api/email/responses', methods=['POST'])
def check_responses():
    """Check for email responses."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    
    required_fields = ['imap_server', 'email_address', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    result = email_automation.check_email_responses(
        imap_server=data['imap_server'],
        email_address=data['email_address'],
        password=data['password'],
        since_date=data.get('since_date')
    )
    
    return jsonify(result)

@app.route('/api/email/stats', methods=['GET'])
def email_stats():
    """Get email campaign statistics."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    stats = email_automation.get_email_stats()
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/email/templates', methods=['GET'])
def email_templates():
    """Get pre-configured email sequence templates."""
    if not EMAIL_AUTOMATION_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    return jsonify({
        'success': True,
        'templates': EMAIL_SEQUENCE_TEMPLATES
    })

@app.route('/api/email/track/open', methods=['POST'])
def track_email_open():
    """Track email open."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    if 'email_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing email_id'
        }), 400
    
    result = email_automation.mark_email_opened(data['email_id'])
    return jsonify(result)

@app.route('/api/email/track/reply', methods=['POST'])
def track_email_reply():
    """Track email reply."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    if 'email_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing email_id'
        }), 400
    
    result = email_automation.mark_email_replied(data['email_id'])
    return jsonify(result)

# ===== ANALYTICS DASHBOARD ENDPOINTS =====

@app.route('/api/analytics/conversion/track', methods=['POST'])
def track_conversion():
    """Track conversion funnel event."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    data = request.get_json()
    
    if 'event_type' not in data or 'lead_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: event_type, lead_id'
        }), 400
    
    result = analytics.track_conversion_event(
        event_type=data['event_type'],
        lead_id=data['lead_id'],
        details=data.get('details', {})
    )
    
    return jsonify(result)

@app.route('/api/analytics/conversion/funnel', methods=['GET'])
def get_funnel():
    """Get conversion funnel statistics."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    funnel = analytics.get_conversion_funnel(start_dt, end_dt)
    
    return jsonify({
        'success': True,
        'funnel': funnel
    })

@app.route('/api/analytics/cost/track', methods=['POST'])
def track_cost():
    """Track cost data."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    data = request.get_json()
    
    required = ['platform', 'amount', 'cost_type']
    if not all(field in data for field in required):
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {required}'
        }), 400
    
    result = analytics.track_cost(
        platform=data['platform'],
        amount=data['amount'],
        cost_type=data['cost_type'],
        description=data.get('description')
    )
    
    return jsonify(result)

@app.route('/api/analytics/revenue/track', methods=['POST'])
def track_revenue():
    """Track revenue data."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    data = request.get_json()
    
    required = ['lead_id', 'amount', 'platform']
    if not all(field in data for field in required):
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {required}'
        }), 400
    
    result = analytics.track_revenue(
        lead_id=data['lead_id'],
        amount=data['amount'],
        platform=data['platform'],
        description=data.get('description')
    )
    
    return jsonify(result)

@app.route('/api/analytics/roi', methods=['GET'])
def get_roi_metrics():
    """Get ROI metrics and calculations."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    roi = analytics.get_roi_metrics(start_dt, end_dt)
    
    return jsonify({
        'success': True,
        'roi_metrics': roi
    })

@app.route('/api/analytics/platforms', methods=['GET'])
def get_platform_performance():
    """Get platform performance comparison."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    performance = analytics.get_platform_performance(start_dt, end_dt)
    
    return jsonify({
        'success': True,
        'performance': performance
    })

@app.route('/api/analytics/timeseries', methods=['GET'])
def get_timeseries():
    """Get time-series analysis."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    granularity = request.args.get('granularity', 'daily')
    days = int(request.args.get('days', 30))
    
    timeseries = analytics.get_time_series_analysis(granularity, days)
    
    return jsonify({
        'success': True,
        'timeseries': timeseries
    })

# ===== CRM INTEGRATION ENDPOINTS =====

@app.route('/api/crm/configure/salesforce', methods=['POST'])
def configure_salesforce():
    """Configure Salesforce connection."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    required = ['instance_url', 'access_token']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = crm.configure_salesforce(
        instance_url=data['instance_url'],
        access_token=data['access_token'],
        api_version=data.get('api_version', 'v57.0')
    )
    return jsonify(result)

@app.route('/api/crm/configure/hubspot', methods=['POST'])
def configure_hubspot():
    """Configure HubSpot connection."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = crm.configure_hubspot(api_key=data['api_key'])
    return jsonify(result)

@app.route('/api/crm/configure/pipedrive', methods=['POST'])
def configure_pipedrive():
    """Configure Pipedrive connection."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    required = ['api_token', 'company_domain']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = crm.configure_pipedrive(
        api_token=data['api_token'],
        company_domain=data['company_domain']
    )
    return jsonify(result)

@app.route('/api/crm/salesforce/lead', methods=['POST'])
def create_salesforce_lead():
    """Create lead in Salesforce."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.salesforce_create_lead(data)
    return jsonify(result)

@app.route('/api/crm/salesforce/lead/<lead_id>', methods=['PATCH'])
def update_salesforce_lead(lead_id):
    """Update lead in Salesforce."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.salesforce_update_lead(lead_id, data)
    return jsonify(result)

@app.route('/api/crm/salesforce/leads', methods=['GET'])
def get_salesforce_leads():
    """Get leads from Salesforce."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    filters = request.args.to_dict()
    result = crm.salesforce_get_leads(filters if filters else None)
    return jsonify(result)

@app.route('/api/crm/hubspot/contact', methods=['POST'])
def create_hubspot_contact():
    """Create contact in HubSpot."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.hubspot_create_contact(data)
    return jsonify(result)

@app.route('/api/crm/hubspot/deal', methods=['POST'])
def create_hubspot_deal():
    """Create deal in HubSpot."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.hubspot_create_deal(data)
    return jsonify(result)

@app.route('/api/crm/hubspot/contacts', methods=['GET'])
def get_hubspot_contacts():
    """Get contacts from HubSpot."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    limit = int(request.args.get('limit', 100))
    result = crm.hubspot_get_contacts(limit)
    return jsonify(result)

@app.route('/api/crm/pipedrive/person', methods=['POST'])
def create_pipedrive_person():
    """Create person in Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.pipedrive_create_person(data)
    return jsonify(result)

@app.route('/api/crm/pipedrive/deal', methods=['POST'])
def create_pipedrive_deal():
    """Create deal in Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.pipedrive_create_deal(data)
    return jsonify(result)

@app.route('/api/crm/pipedrive/deal/<int:deal_id>', methods=['PUT'])
def update_pipedrive_deal(deal_id):
    """Update deal in Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.pipedrive_update_deal(deal_id, data)
    return jsonify(result)

@app.route('/api/crm/pipedrive/deals', methods=['GET'])
def get_pipedrive_deals():
    """Get deals from Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    status = request.args.get('status', 'all_not_deleted')
    result = crm.pipedrive_get_deals(status)
    return jsonify(result)

@app.route('/api/crm/sync', methods=['POST'])
def sync_to_crm():
    """Universal sync to any CRM."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    required = ['crm_type', 'record_type', 'data']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = crm.sync_to_crm(
        crm_type=data['crm_type'],
        record_type=data['record_type'],
        data=data['data']
    )
    return jsonify(result)

@app.route('/api/crm/bulk-sync', methods=['POST'])
def bulk_sync():
    """Bulk sync multiple records to CRM."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    if 'crm_type' not in data or 'records' not in data:
        return jsonify({'success': False, 'error': 'Missing: crm_type, records'}), 400
    
    result = crm.bulk_sync(
        crm_type=data['crm_type'],
        records=data['records']
    )
    return jsonify(result)

@app.route('/api/crm/sync-log', methods=['GET'])
def get_sync_log():
    """Get CRM sync activity log."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    result = crm.get_sync_log(limit)
    return jsonify(result)

# ===== AI-POWERED FEATURES ENDPOINTS =====

@app.route('/api/ai/analyze-job', methods=['POST'])
def analyze_job():
    """AI-powered job description analysis."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    if 'description' not in data:
        return jsonify({'success': False, 'error': 'Missing: description'}), 400
    
    analysis = ai.analyze_job_description(
        job_description=data['description'],
        job_title=data.get('title', '')
    )
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })

@app.route('/api/ai/batch-analyze', methods=['POST'])
def batch_analyze():
    """Batch analyze multiple jobs."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    if 'jobs' not in data:
        return jsonify({'success': False, 'error': 'Missing: jobs'}), 400
    
    result = ai.batch_analyze_jobs(data['jobs'])
    return jsonify(result)

@app.route('/api/ai/ml-score', methods=['POST'])
def ml_score():
    """ML-enhanced lead scoring."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    required = ['lead_data', 'job_analysis']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    scoring = ai.ml_enhanced_lead_scoring(
        lead_data=data['lead_data'],
        job_analysis=data['job_analysis']
    )
    
    return jsonify({
        'success': True,
        'scoring': scoring
    })

@app.route('/api/ai/predict-response', methods=['POST'])
def predict_response():
    """Predict response likelihood."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    required = ['lead_data', 'outreach_history']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    prediction = ai.predict_response_likelihood(
        lead_data=data['lead_data'],
        outreach_history=data['outreach_history']
    )
    
    return jsonify({
        'success': True,
        'prediction': prediction
    })

@app.route('/api/ai/features-status', methods=['GET'])
def ai_features_status():
    """Get AI features availability status."""
    return jsonify({
        'success': True,
        'ai_enabled': AI_ENABLED,
        'features': {
            'job_analysis': AI_ENABLED,
            'ml_scoring': AI_ENABLED,
            'response_prediction': AI_ENABLED,
            'batch_processing': AI_ENABLED
        },
        'capabilities': {
            'nlp_job_analysis': 'Extract skills, seniority, tech stack, requirements',
            'ml_lead_scoring': 'Enhanced scoring with feature analysis and confidence',
            'response_prediction': 'Predict response likelihood and best contact time',
            'batch_analysis': 'Analyze multiple jobs efficiently'
        }
    })

# ===== AUTOMATED FOLLOW-UP ENGINE ENDPOINTS =====

@app.route('/api/followup/create-sequence', methods=['POST'])
def create_followup_sequence():
    """Create automated follow-up sequence."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['lead_id', 'initial_email_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.create_follow_up_sequence(
        lead_id=data['lead_id'],
        initial_email_id=data['initial_email_id'],
        rule_type=data.get('rule_type', 'no_response')
    )
    
    return jsonify(result)

@app.route('/api/followup/engagement', methods=['POST'])
def update_followup_engagement():
    """Update follow-up based on engagement."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['lead_id', 'engagement_type']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.update_on_engagement(
        lead_id=data['lead_id'],
        engagement_type=data['engagement_type'],
        sequence_id=data.get('sequence_id')
    )
    
    return jsonify(result)

@app.route('/api/followup/due', methods=['GET'])
def get_due_followups():
    """Get follow-ups due soon."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    hours_ahead = int(request.args.get('hours_ahead', 24))
    result = followup_engine.get_due_followups(hours_ahead)
    
    return jsonify(result)

@app.route('/api/followup/mark-sent/<followup_id>', methods=['POST'])
def mark_followup_sent(followup_id):
    """Mark follow-up as sent."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    result = followup_engine.mark_followup_sent(followup_id)
    return jsonify(result)

@app.route('/api/followup/cancel-sequence/<sequence_id>', methods=['POST'])
def cancel_followup_sequence(sequence_id):
    """Cancel follow-up sequence."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json() or {}
    result = followup_engine.cancel_sequence(
        sequence_id=sequence_id,
        reason=data.get('reason', 'Manual cancellation')
    )
    
    return jsonify(result)

@app.route('/api/followup/engagement-stats/<lead_id>', methods=['GET'])
def get_engagement_stats(lead_id):
    """Get engagement statistics for lead."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    result = followup_engine.get_engagement_stats(lead_id)
    return jsonify(result)

@app.route('/api/followup/optimize-timing', methods=['POST'])
def optimize_followup_timing():
    """ML-based timing optimization."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['lead_data', 'historical_data']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.optimize_timing_ml(
        lead_data=data['lead_data'],
        historical_data=data['historical_data']
    )
    
    return jsonify(result)

@app.route('/api/followup/sequences', methods=['GET'])
def get_all_followup_sequences():
    """Get all follow-up sequences."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    status = request.args.get('status')
    result = followup_engine.get_all_sequences(status)
    
    return jsonify(result)

@app.route('/api/followup/performance', methods=['GET'])
def get_followup_performance():
    """Get follow-up performance metrics."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    result = followup_engine.get_performance_metrics()
    return jsonify(result)

@app.route('/api/followup/custom-rule', methods=['POST'])
def create_custom_followup_rule():
    """Create custom follow-up rule."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['rule_name', 'intervals', 'max_attempts']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.custom_rule(
        rule_name=data['rule_name'],
        intervals=data['intervals'],
        max_attempts=data['max_attempts'],
        stop_on_response=data.get('stop_on_response', True)
    )
    
    return jsonify(result)

# ===== LEAD ENRICHMENT & VERIFICATION ENDPOINTS =====

@app.route('/api/enrichment/configure/clearbit', methods=['POST'])
def configure_clearbit_api():
    """Configure Clearbit API."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = lead_enrichment.configure_clearbit(data['api_key'])
    return jsonify(result)

@app.route('/api/enrichment/configure/hunter', methods=['POST'])
def configure_hunter_api():
    """Configure Hunter.io API."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = lead_enrichment.configure_hunter(data['api_key'])
    return jsonify(result)

@app.route('/api/enrichment/configure/zoominfo', methods=['POST'])
def configure_zoominfo_api():
    """Configure ZoomInfo API."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = lead_enrichment.configure_zoominfo(data['api_key'])
    return jsonify(result)

@app.route('/api/enrichment/clearbit', methods=['POST'])
def enrich_clearbit():
    """Enrich using Clearbit."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    result = lead_enrichment.enrich_with_clearbit(
        email=data.get('email'),
        domain=data.get('domain')
    )
    return jsonify(result)

@app.route('/api/enrichment/verify-email', methods=['POST'])
def verify_email():
    """Verify email with Hunter.io."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'email' not in data:
        return jsonify({'success': False, 'error': 'Missing: email'}), 400
    
    result = lead_enrichment.verify_email_hunter(data['email'])
    return jsonify(result)

@app.route('/api/enrichment/find-email', methods=['POST'])
def find_email():
    """Find email with Hunter.io."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    required = ['domain', 'first_name', 'last_name']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = lead_enrichment.find_email_hunter(
        domain=data['domain'],
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    return jsonify(result)

@app.route('/api/enrichment/zoominfo', methods=['POST'])
def enrich_zoominfo():
    """Enrich using ZoomInfo."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    result = lead_enrichment.enrich_with_zoominfo(
        company_name=data.get('company_name'),
        email=data.get('email')
    )
    return jsonify(result)

@app.route('/api/enrichment/batch-verify', methods=['POST'])
def batch_verify_emails():
    """Batch verify emails."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'emails' not in data:
        return jsonify({'success': False, 'error': 'Missing: emails'}), 400
    
    result = lead_enrichment.batch_verify_emails(data['emails'])
    return jsonify(result)

@app.route('/api/enrichment/full', methods=['POST'])
def full_enrichment():
    """Full lead enrichment using all services."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    result = lead_enrichment.full_lead_enrichment(
        email=data.get('email'),
        domain=data.get('domain'),
        company_name=data.get('company_name')
    )
    return jsonify(result)

@app.route('/api/enrichment/stats', methods=['GET'])
def enrichment_stats():
    """Get enrichment statistics."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    result = lead_enrichment.get_enrichment_stats()
    return jsonify(result)

# ===== A/B TESTING FRAMEWORK ENDPOINTS =====

@app.route('/api/ab-test/create', methods=['POST'])
def create_ab_test():
    """Create new A/B test."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    data = request.get_json()
    required = ['test_name', 'test_type', 'variants']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = ab_testing.create_test(
        test_name=data['test_name'],
        test_type=data['test_type'],
        variants=data['variants'],
        traffic_split=data.get('traffic_split'),
        duration_days=data.get('duration_days', 7),
        min_sample_size=data.get('min_sample_size', 100)
    )
    
    return jsonify(result)

@app.route('/api/ab-test/assign', methods=['POST'])
def assign_ab_variant():
    """Assign variant to user."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    data = request.get_json()
    required = ['test_name', 'user_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = ab_testing.assign_variant(
        test_name=data['test_name'],
        user_id=data['user_id']
    )
    
    return jsonify(result)

@app.route('/api/ab-test/track', methods=['POST'])
def track_ab_event():
    """Track A/B test event."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    data = request.get_json()
    required = ['test_name', 'variant_name', 'event_type']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = ab_testing.track_event(
        test_name=data['test_name'],
        variant_name=data['variant_name'],
        event_type=data['event_type']
    )
    
    return jsonify(result)

@app.route('/api/ab-test/results/<test_name>', methods=['GET'])
def get_ab_test_results(test_name):
    """Get A/B test results."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    result = ab_testing.get_test_results(test_name)
    return jsonify(result)

@app.route('/api/ab-test/stop/<test_name>', methods=['POST'])
def stop_ab_test(test_name):
    """Stop A/B test early."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    result = ab_testing.stop_test(test_name)
    return jsonify(result)

@app.route('/api/ab-test/all', methods=['GET'])
def get_all_ab_tests():
    """Get all A/B tests."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    status = request.args.get('status')
    result = ab_testing.get_all_tests(status)
    
    return jsonify(result)

@app.route('/api/ab-test/best-variants', methods=['GET'])
def get_best_ab_variants():
    """Get best performing variants."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    metric = request.args.get('metric', 'conversion_rate')
    result = ab_testing.get_best_performing_variants(metric)
    
    return jsonify(result)

# ===== ADVANCED REPORTING & EXPORTS ENDPOINTS =====

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate comprehensive report."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    required = ['report_type', 'data']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = reporting.generate_report(
        report_type=data['report_type'],
        data=data['data'],
        format=data.get('format', 'json'),
        include_charts=data.get('include_charts', True)
    )
    
    return jsonify(result)

@app.route('/api/reports/schedule', methods=['POST'])
def schedule_report():
    """Schedule recurring report."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    required = ['report_type', 'frequency', 'recipients']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = reporting.schedule_report(
        report_type=data['report_type'],
        frequency=data['frequency'],
        recipients=data['recipients'],
        format=data.get('format', 'pdf'),
        data_source=data.get('data_source')
    )
    
    return jsonify(result)

@app.route('/api/reports/export', methods=['POST'])
def export_data():
    """Export data in various formats."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    if 'data_type' not in data:
        return jsonify({'success': False, 'error': 'Missing: data_type'}), 400
    
    result = reporting.export_data(
        data_type=data['data_type'],
        filters=data.get('filters'),
        format=data.get('format', 'csv'),
        fields=data.get('fields')
    )
    
    return jsonify(result)

@app.route('/api/reports/dashboard', methods=['POST'])
def create_dashboard():
    """Create custom dashboard."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    required = ['dashboard_name', 'widgets']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = reporting.create_custom_dashboard(
        dashboard_name=data['dashboard_name'],
        widgets=data['widgets']
    )
    
    return jsonify(result)

@app.route('/api/reports/scheduled', methods=['GET'])
def get_scheduled_reports():
    """Get scheduled reports."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    status = request.args.get('status')
    result = reporting.get_scheduled_reports(status)
    
    return jsonify(result)

@app.route('/api/reports/export-history', methods=['GET'])
def get_export_history():
    """Get export history."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    result = reporting.get_export_history(limit)
    
    return jsonify(result)

@app.route('/api/reports/templates', methods=['GET'])
def get_report_templates():
    """Get available report templates."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    result = reporting.get_available_templates()
    return jsonify(result)

# ===== MULTI-CHANNEL OUTREACH ENDPOINTS =====

@app.route('/api/multichannel/configure/twilio', methods=['POST'])
def configure_twilio_sms():
    """Configure Twilio for SMS."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['account_sid', 'auth_token', 'phone_number']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.configure_twilio(
        account_sid=data['account_sid'],
        auth_token=data['auth_token'],
        phone_number=data['phone_number']
    )
    return jsonify(result)

@app.route('/api/multichannel/configure/whatsapp', methods=['POST'])
def configure_whatsapp_business():
    """Configure WhatsApp Business API."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['access_token', 'phone_number_id', 'business_account_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.configure_whatsapp(
        access_token=data['access_token'],
        phone_number_id=data['phone_number_id'],
        business_account_id=data['business_account_id']
    )
    return jsonify(result)

@app.route('/api/multichannel/configure/slack', methods=['POST'])
def configure_slack_bot():
    """Configure Slack integration."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['bot_token', 'workspace_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.configure_slack(
        bot_token=data['bot_token'],
        workspace_id=data['workspace_id']
    )
    return jsonify(result)

@app.route('/api/multichannel/sms/send', methods=['POST'])
def send_sms_message():
    """Send SMS message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['to_number', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_sms(
        to_number=data['to_number'],
        message=data['message'],
        lead_id=data.get('lead_id')
    )
    return jsonify(result)

@app.route('/api/multichannel/sms/bulk', methods=['POST'])
def send_bulk_sms():
    """Send bulk SMS messages."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    if 'recipients' not in data:
        return jsonify({'success': False, 'error': 'Missing: recipients'}), 400
    
    result = multichannel.send_sms_bulk(recipients=data['recipients'])
    return jsonify(result)

@app.route('/api/multichannel/whatsapp/send', methods=['POST'])
def send_whatsapp_message():
    """Send WhatsApp message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['to_number', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_whatsapp(
        to_number=data['to_number'],
        message=data['message'],
        lead_id=data.get('lead_id')
    )
    return jsonify(result)

@app.route('/api/multichannel/whatsapp/template', methods=['POST'])
def send_whatsapp_template():
    """Send WhatsApp template message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['to_number', 'template_name', 'parameters']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_whatsapp_template(
        to_number=data['to_number'],
        template_name=data['template_name'],
        parameters=data['parameters']
    )
    return jsonify(result)

@app.route('/api/multichannel/slack/send', methods=['POST'])
def send_slack_message():
    """Send Slack message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['channel', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_slack_message(
        channel=data['channel'],
        message=data['message'],
        lead_id=data.get('lead_id')
    )
    return jsonify(result)

@app.route('/api/multichannel/slack/dm', methods=['POST'])
def send_slack_dm():
    """Send Slack direct message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['user_id', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_slack_dm(
        user_id=data['user_id'],
        message=data['message']
    )
    return jsonify(result)

@app.route('/api/multichannel/campaign/create', methods=['POST'])
def create_multichannel_campaign():
    """Create multi-channel campaign."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['campaign_name', 'channels', 'message_templates', 'recipients']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.create_multichannel_campaign(
        campaign_name=data['campaign_name'],
        channels=data['channels'],
        message_templates=data['message_templates'],
        recipients=data['recipients']
    )
    return jsonify(result)

@app.route('/api/multichannel/send', methods=['POST'])
def send_multichannel_message():
    """Send message across multiple channels."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['recipient', 'channels', 'messages']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_multichannel_message(
        recipient=data['recipient'],
        channels=data['channels'],
        messages=data['messages']
    )
    return jsonify(result)

@app.route('/api/multichannel/stats', methods=['GET'])
def get_multichannel_stats():
    """Get multi-channel statistics."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    result = multichannel.get_channel_stats()
    return jsonify(result)

@app.route('/api/multichannel/history', methods=['GET'])
def get_multichannel_history():
    """Get message history."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    channel = request.args.get('channel')
    lead_id = request.args.get('lead_id')
    limit = int(request.args.get('limit', 50))
    
    result = multichannel.get_message_history(
        channel=channel,
        lead_id=lead_id,
        limit=limit
    )
    return jsonify(result)

@app.route('/api/multichannel/track-reply', methods=['POST'])
def track_multichannel_reply():
    """Track reply to message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['message_id', 'reply_content']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.track_reply(
        message_id=data['message_id'],
        reply_content=data['reply_content']
    )
    return jsonify(result)

@app.route('/api/multichannel/recommend-channel', methods=['POST'])
def recommend_best_channel():
    """Recommend best channel for lead."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    if 'lead_engagement' not in data:
        return jsonify({'success': False, 'error': 'Missing: lead_engagement'}), 400
    
    result = multichannel.get_best_channel_for_lead(
        lead_engagement=data['lead_engagement']
    )
    return jsonify(result)

# WSGI entry point for Vercel
if __name__ == '__main__':
    app.run(debug=True)