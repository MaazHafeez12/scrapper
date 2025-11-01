"""
Contact Discovery Module for Business Development Platform
Automated finding of decision makers and contact information
"""
import re
import requests
from typing import Dict, List, Optional, Tuple
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import json
import dns.resolver
import whois
from datetime import datetime

class ContactDiscovery:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Email patterns for different roles
        self.decision_maker_patterns = [
            r'(cto|chief.technology.officer)',
            r'(ceo|chief.executive.officer)', 
            r'(engineering.manager|head.of.engineering)',
            r'(technical.director|tech.director)',
            r'(vp.engineering|vice.president.engineering)',
            r'(founder|co.founder)',
            r'(hr.manager|head.of.hr|human.resources)',
            r'(recruiting.manager|talent.acquisition)'
        ]
        
        # Common email formats
        self.email_formats = [
            '{first}.{last}@{domain}',
            '{first}{last}@{domain}',
            '{first_initial}.{last}@{domain}',
            '{first_initial}{last}@{domain}',
            '{first}@{domain}',
            '{last}@{domain}',
            'contact@{domain}',
            'careers@{domain}',
            'jobs@{domain}',
            'hello@{domain}',
            'info@{domain}',
            'recruiting@{domain}'
        ]
    
    def extract_company_domain(self, company_name: str, job_url: str = None) -> Optional[str]:
        """Extract company domain from company name or job URL."""
        try:
            # First try to extract from job URL
            if job_url:
                parsed = urlparse(job_url)
                if parsed.netloc:
                    # Skip job board domains
                    job_boards = ['indeed.com', 'linkedin.com', 'glassdoor.com', 'remoteok.io', 
                                 'weworkremotely.com', 'wellfound.com', 'nodesk.co']
                    if not any(board in parsed.netloc for board in job_boards):
                        return parsed.netloc.replace('www.', '')
            
            # Try to find company website through search patterns
            clean_company = self.clean_company_name(company_name)
            potential_domains = [
                f"{clean_company}.com",
                f"{clean_company}.io",
                f"{clean_company}.co",
                f"{clean_company}.net",
                f"{clean_company}.org"
            ]
            
            for domain in potential_domains:
                if self.verify_domain_exists(domain):
                    return domain
            
            return None
            
        except Exception as e:
            print(f"Error extracting company domain: {e}")
            return None
    
    def clean_company_name(self, company_name: str) -> str:
        """Clean company name for domain generation."""
        # Remove common suffixes and words
        clean = company_name.lower()
        clean = re.sub(r'\b(inc|corp|corporation|llc|ltd|limited|company|co)\b', '', clean)
        clean = re.sub(r'[^a-z0-9]', '', clean)
        return clean.strip()
    
    def verify_domain_exists(self, domain: str) -> bool:
        """Verify if a domain exists and is reachable."""
        try:
            # Quick DNS check
            dns.resolver.resolve(domain, 'A')
            
            # Try to access the website
            response = self.session.get(f"https://{domain}", timeout=10)
            return response.status_code < 400
            
        except Exception:
            return False
    
    def scrape_company_contacts(self, domain: str) -> Dict:
        """Scrape contact information from company website."""
        contacts = {
            'emails': [],
            'linkedin_profiles': [],
            'team_members': [],
            'contact_pages': []
        }
        
        try:
            # Check main pages for contact info
            pages_to_check = [
                '',  # Homepage
                '/about',
                '/team',
                '/contact',
                '/careers',
                '/leadership'
            ]
            
            for page in pages_to_check:
                try:
                    url = f"https://{domain}{page}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract emails
                        emails = self.extract_emails_from_content(response.text)
                        contacts['emails'].extend(emails)
                        
                        # Extract LinkedIn profiles
                        linkedin_profiles = self.extract_linkedin_profiles(soup)
                        contacts['linkedin_profiles'].extend(linkedin_profiles)
                        
                        # Extract team member info
                        team_members = self.extract_team_members(soup)
                        contacts['team_members'].extend(team_members)
                        
                        if page == '/contact':
                            contacts['contact_pages'].append(url)
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    continue
            
            # Deduplicate results
            contacts['emails'] = list(set(contacts['emails']))
            contacts['linkedin_profiles'] = list(set(contacts['linkedin_profiles']))
            
            return contacts
            
        except Exception as e:
            print(f"Error scraping company contacts: {e}")
            return contacts
    
    def extract_emails_from_content(self, content: str) -> List[str]:
        """Extract email addresses from content."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        
        # Filter out common non-personal emails
        filtered_emails = []
        skip_emails = ['support@', 'noreply@', 'no-reply@', 'newsletter@', 'marketing@']
        
        for email in emails:
            if not any(skip in email.lower() for skip in skip_emails):
                filtered_emails.append(email.lower())
        
        return filtered_emails
    
    def extract_linkedin_profiles(self, soup: BeautifulSoup) -> List[str]:
        """Extract LinkedIn profile URLs from page."""
        linkedin_profiles = []
        
        # Find LinkedIn links
        linkedin_links = soup.find_all('a', href=re.compile(r'linkedin\.com/in/'))
        
        for link in linkedin_links:
            href = link.get('href')
            if href:
                # Clean and validate LinkedIn URL
                if 'linkedin.com/in/' in href:
                    linkedin_profiles.append(href)
        
        return linkedin_profiles
    
    def extract_team_members(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team member information from page."""
        team_members = []
        
        # Look for team sections
        team_sections = soup.find_all(['div', 'section'], class_=re.compile(r'team|staff|people|leadership'))
        
        for section in team_sections:
            # Extract names and titles
            names = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for name_elem in names:
                name_text = name_elem.get_text(strip=True)
                if len(name_text.split()) >= 2:  # Likely a full name
                    # Look for title in nearby elements
                    title = self.find_nearby_title(name_elem)
                    
                    team_members.append({
                        'name': name_text,
                        'title': title,
                        'is_decision_maker': self.is_decision_maker(title)
                    })
        
        return team_members
    
    def find_nearby_title(self, name_element) -> str:
        """Find job title near a name element."""
        # Check siblings and parent elements for title
        for sibling in name_element.find_next_siblings():
            text = sibling.get_text(strip=True)
            if any(word in text.lower() for word in ['cto', 'ceo', 'manager', 'director', 'engineer', 'developer']):
                return text
        
        # Check parent element
        parent = name_element.parent
        if parent:
            text = parent.get_text(strip=True)
            lines = text.split('\n')
            for line in lines[1:3]:  # Check next 2 lines
                if any(word in line.lower() for word in ['cto', 'ceo', 'manager', 'director', 'engineer']):
                    return line.strip()
        
        return ""
    
    def is_decision_maker(self, title: str) -> bool:
        """Check if a title indicates decision-making authority."""
        if not title:
            return False
        
        title_lower = title.lower()
        decision_keywords = [
            'cto', 'ceo', 'founder', 'director', 'manager', 'head of', 'vp', 'vice president',
            'chief', 'lead', 'principal', 'senior manager'
        ]
        
        return any(keyword in title_lower for keyword in decision_keywords)
    
    def generate_email_guesses(self, team_members: List[Dict], domain: str) -> List[Dict]:
        """Generate likely email addresses for team members."""
        email_guesses = []
        
        for member in team_members:
            name = member.get('name', '')
            title = member.get('title', '')
            
            if len(name.split()) >= 2:
                first_name = name.split()[0].lower()
                last_name = name.split()[-1].lower()
                first_initial = first_name[0] if first_name else ''
                
                # Generate email possibilities
                possible_emails = [
                    f"{first_name}.{last_name}@{domain}",
                    f"{first_name}{last_name}@{domain}",
                    f"{first_initial}.{last_name}@{domain}",
                    f"{first_initial}{last_name}@{domain}",
                    f"{first_name}@{domain}"
                ]
                
                for email in possible_emails:
                    email_guesses.append({
                        'email': email,
                        'name': name,
                        'title': title,
                        'confidence': self.calculate_email_confidence(email, member),
                        'is_decision_maker': member.get('is_decision_maker', False),
                        'type': 'guessed'
                    })
        
        return email_guesses
    
    def calculate_email_confidence(self, email: str, member: Dict) -> float:
        """Calculate confidence score for email guess."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for decision makers
        if member.get('is_decision_maker', False):
            confidence += 0.3
        
        # Common email format patterns get higher confidence
        if '.' in email.split('@')[0]:  # first.last format
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def verify_email_existence(self, email: str) -> bool:
        """Basic email verification (check domain MX records)."""
        try:
            domain = email.split('@')[1]
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception:
            return False
    
    def discover_contacts(self, company_name: str, job_title: str, job_url: str = None) -> Dict:
        """Main method to discover contacts for a company."""
        results = {
            'company': company_name,
            'domain': None,
            'direct_emails': [],
            'guessed_emails': [],
            'linkedin_profiles': [],
            'decision_makers': [],
            'contact_methods': [],
            'confidence_score': 0
        }
        
        try:
            # Extract company domain
            domain = self.extract_company_domain(company_name, job_url)
            if not domain:
                return results
            
            results['domain'] = domain
            
            # Scrape company website for contacts
            scraped_contacts = self.scrape_company_contacts(domain)
            results['direct_emails'] = scraped_contacts['emails']
            results['linkedin_profiles'] = scraped_contacts['linkedin_profiles']
            
            # Generate email guesses for team members
            email_guesses = self.generate_email_guesses(scraped_contacts['team_members'], domain)
            results['guessed_emails'] = email_guesses
            
            # Identify decision makers
            decision_makers = [member for member in scraped_contacts['team_members'] 
                             if member.get('is_decision_maker', False)]
            results['decision_makers'] = decision_makers
            
            # Add standard contact methods
            results['contact_methods'] = [
                {'method': 'LinkedIn Company Page', 'url': f"https://linkedin.com/company/{self.clean_company_name(company_name)}"},
                {'method': 'Company Website', 'url': f"https://{domain}"},
                {'method': 'Contact Page', 'url': f"https://{domain}/contact"},
                {'method': 'Careers Page', 'url': f"https://{domain}/careers"}
            ]
            
            # Calculate overall confidence score
            confidence = 0
            if results['direct_emails']:
                confidence += 40
            if results['guessed_emails']:
                confidence += 30
            if results['decision_makers']:
                confidence += 20
            if results['linkedin_profiles']:
                confidence += 10
            
            results['confidence_score'] = min(confidence, 100)
            
            return results
            
        except Exception as e:
            print(f"Error in contact discovery: {e}")
            return results

# Singleton instance
contact_discovery = ContactDiscovery()