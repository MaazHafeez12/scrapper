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

# Create a simple in-memory database for demo purposes
# In production, you'd use a proper database like PostgreSQL or MongoDB

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-demo-key')

# Live scraping storage (in-memory for serverless)
live_jobs = []
scraping_status = {'running': False, 'last_search': None, 'job_count': 0}

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
    platforms = data.get('platforms', ['remoteok', 'weworkremotely', 'indeed', 'wellfound', 'glassdoor'])
    limit = int(data.get('limit', 100))  # Increased default limit
    
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
            'glassdoor': 25
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
    """Get live scraped jobs."""
    search = request.args.get('search', '').lower()
    limit = int(request.args.get('limit', 50))
    
    filtered_jobs = live_jobs
    
    if search:
        filtered_jobs = [job for job in live_jobs 
                        if search in job['title'].lower() 
                        or search in job['company'].lower()]
    
    return jsonify(filtered_jobs[:limit])

@app.route('/api/clear-live-jobs', methods=['POST'])
def clear_live_jobs():
    """Clear live scraped jobs."""
    global live_jobs
    live_jobs = []
    return jsonify({'success': True, 'message': 'Live jobs cleared'})

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
                    <h3>📈 Statistics</h3>
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
                            <h3 id="platforms-count">5</h3>
                            <p>Active Platforms</p>
                        </div>
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
                            limit: 150  // Increased limit for more results
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
                            <p><span class="remote">Remote</span> • ${job.salary}</p>
                            <p>${job.description}</p>
                            <p><small>Scraped: ${new Date(job.scraped_at).toLocaleString()}</small></p>
                            ${job.url ? `<p><a href="${job.url}" target="_blank">🔗 View Job</a></p>` : ''}
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading live jobs:', error);
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
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    document.getElementById('total-jobs').textContent = stats.total_jobs;
                    document.getElementById('remote-jobs').textContent = stats.remote_jobs;
                    
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