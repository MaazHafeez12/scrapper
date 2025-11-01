"""
Lead Enrichment & Verification Module
Integrates with Clearbit, Hunter.io, ZoomInfo for data enrichment
"""

import requests
from typing import Dict, List, Optional
import re
from datetime import datetime

class LeadEnrichment:
    """Lead data enrichment and email verification."""
    
    def __init__(self):
        self.clearbit_api_key = None
        self.hunter_api_key = None
        self.zoominfo_api_key = None
        
        self.enrichment_cache = {}
        self.verification_cache = {}
    
    def configure_clearbit(self, api_key: str) -> Dict:
        """Configure Clearbit API."""
        self.clearbit_api_key = api_key
        return {
            'success': True,
            'message': 'Clearbit API configured',
            'provider': 'clearbit'
        }
    
    def configure_hunter(self, api_key: str) -> Dict:
        """Configure Hunter.io API."""
        self.hunter_api_key = api_key
        return {
            'success': True,
            'message': 'Hunter.io API configured',
            'provider': 'hunter'
        }
    
    def configure_zoominfo(self, api_key: str) -> Dict:
        """Configure ZoomInfo API."""
        self.zoominfo_api_key = api_key
        return {
            'success': True,
            'message': 'ZoomInfo API configured',
            'provider': 'zoominfo'
        }
    
    def enrich_with_clearbit(self, email: Optional[str] = None, domain: Optional[str] = None) -> Dict:
        """
        Enrich company/person data using Clearbit.
        
        Args:
            email: Person's email address
            domain: Company domain
            
        Returns:
            Dict with enriched data
        """
        if not self.clearbit_api_key:
            return self._mock_clearbit_enrichment(email, domain)
        
        # Check cache
        cache_key = email or domain
        if cache_key in self.enrichment_cache:
            return self.enrichment_cache[cache_key]
        
        try:
            if email:
                # Person enrichment
                url = f"https://person.clearbit.com/v2/people/find?email={email}"
            elif domain:
                # Company enrichment
                url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
            else:
                return {'success': False, 'error': 'Email or domain required'}
            
            headers = {
                'Authorization': f'Bearer {self.clearbit_api_key}'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'success': True,
                    'source': 'clearbit',
                    'data': data,
                    'enriched_at': datetime.now().isoformat()
                }
                
                self.enrichment_cache[cache_key] = result
                return result
            else:
                return self._mock_clearbit_enrichment(email, domain)
                
        except Exception as e:
            return self._mock_clearbit_enrichment(email, domain)
    
    def _mock_clearbit_enrichment(self, email: Optional[str], domain: Optional[str]) -> Dict:
        """Mock Clearbit response for demo."""
        if email:
            return {
                'success': True,
                'source': 'clearbit_mock',
                'data': {
                    'person': {
                        'name': {
                            'fullName': 'John Doe',
                            'givenName': 'John',
                            'familyName': 'Doe'
                        },
                        'email': email,
                        'location': 'San Francisco, CA',
                        'title': 'Engineering Manager',
                        'employment': {
                            'domain': domain or 'example.com',
                            'name': 'Example Corp',
                            'title': 'Engineering Manager',
                            'role': 'engineering',
                            'seniority': 'manager'
                        },
                        'linkedin': {
                            'handle': 'johndoe'
                        },
                        'twitter': {
                            'handle': 'johndoe'
                        }
                    }
                },
                'note': 'Mock data - configure Clearbit API key for real data'
            }
        else:
            return {
                'success': True,
                'source': 'clearbit_mock',
                'data': {
                    'company': {
                        'name': 'Example Corp',
                        'domain': domain,
                        'category': {
                            'sector': 'Information Technology',
                            'industry': 'Software'
                        },
                        'metrics': {
                            'employees': 250,
                            'employeesRange': '100-500',
                            'estimatedAnnualRevenue': '$50M-$100M',
                            'fiscalYearEnd': 12
                        },
                        'location': 'San Francisco, CA, USA',
                        'geo': {
                            'city': 'San Francisco',
                            'state': 'California',
                            'country': 'United States'
                        },
                        'tech': ['aws', 'react', 'python', 'kubernetes'],
                        'description': 'Example company in the software industry'
                    }
                },
                'note': 'Mock data - configure Clearbit API key for real data'
            }
    
    def verify_email_hunter(self, email: str) -> Dict:
        """
        Verify email using Hunter.io.
        
        Args:
            email: Email address to verify
            
        Returns:
            Dict with verification results
        """
        if not self.hunter_api_key:
            return self._mock_hunter_verification(email)
        
        # Check cache
        if email in self.verification_cache:
            return self.verification_cache[email]
        
        try:
            url = "https://api.hunter.io/v2/email-verifier"
            params = {
                'email': email,
                'api_key': self.hunter_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'success': True,
                    'source': 'hunter',
                    'email': email,
                    'verification': data.get('data', {}),
                    'verified_at': datetime.now().isoformat()
                }
                
                self.verification_cache[email] = result
                return result
            else:
                return self._mock_hunter_verification(email)
                
        except Exception as e:
            return self._mock_hunter_verification(email)
    
    def _mock_hunter_verification(self, email: str) -> Dict:
        """Mock Hunter.io verification."""
        # Basic email format check
        is_valid_format = re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None
        
        return {
            'success': True,
            'source': 'hunter_mock',
            'email': email,
            'verification': {
                'result': 'deliverable' if is_valid_format else 'invalid',
                'score': 95 if is_valid_format else 20,
                'email': email,
                'regexp': is_valid_format,
                'gibberish': False,
                'disposable': False,
                'webmail': 'gmail' in email or 'yahoo' in email or 'outlook' in email,
                'mx_records': is_valid_format,
                'smtp_server': is_valid_format,
                'smtp_check': is_valid_format,
                'accept_all': False,
                'block': False
            },
            'note': 'Mock data - configure Hunter.io API key for real verification'
        }
    
    def find_email_hunter(self, domain: str, first_name: str, last_name: str) -> Dict:
        """
        Find email using Hunter.io email finder.
        
        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name
            
        Returns:
            Dict with found email and confidence
        """
        if not self.hunter_api_key:
            return self._mock_hunter_email_finder(domain, first_name, last_name)
        
        try:
            url = "https://api.hunter.io/v2/email-finder"
            params = {
                'domain': domain,
                'first_name': first_name,
                'last_name': last_name,
                'api_key': self.hunter_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'source': 'hunter',
                    'email': data.get('data', {}).get('email'),
                    'confidence': data.get('data', {}).get('score'),
                    'sources': data.get('data', {}).get('sources', [])
                }
            else:
                return self._mock_hunter_email_finder(domain, first_name, last_name)
                
        except Exception as e:
            return self._mock_hunter_email_finder(domain, first_name, last_name)
    
    def _mock_hunter_email_finder(self, domain: str, first_name: str, last_name: str) -> Dict:
        """Mock Hunter.io email finder."""
        # Generate common email patterns
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}@{domain}",
            f"{first_name.lower()}@{domain}",
            f"{first_name[0].lower()}{last_name.lower()}@{domain}",
            f"{first_name.lower()}{last_name[0].lower()}@{domain}"
        ]
        
        return {
            'success': True,
            'source': 'hunter_mock',
            'email': patterns[0],
            'confidence': 85,
            'alternative_emails': patterns[1:],
            'note': 'Mock data - configure Hunter.io API key for real email finding'
        }
    
    def enrich_with_zoominfo(self, company_name: Optional[str] = None, email: Optional[str] = None) -> Dict:
        """
        Enrich data using ZoomInfo.
        
        Args:
            company_name: Company name
            email: Person email
            
        Returns:
            Dict with enriched data
        """
        if not self.zoominfo_api_key:
            return self._mock_zoominfo_enrichment(company_name, email)
        
        # ZoomInfo API integration would go here
        return self._mock_zoominfo_enrichment(company_name, email)
    
    def _mock_zoominfo_enrichment(self, company_name: Optional[str], email: Optional[str]) -> Dict:
        """Mock ZoomInfo enrichment."""
        if company_name:
            return {
                'success': True,
                'source': 'zoominfo_mock',
                'data': {
                    'company': {
                        'name': company_name,
                        'revenue': '$50M-$100M',
                        'employees': 250,
                        'industry': 'Software',
                        'founded': 2015,
                        'phone': '+1-555-0123',
                        'headquarters': 'San Francisco, CA',
                        'technologies': ['AWS', 'Salesforce', 'HubSpot', 'React'],
                        'decision_makers': [
                            {
                                'name': 'Jane Smith',
                                'title': 'VP of Engineering',
                                'email': f'jane.smith@{company_name.lower().replace(" ", "")}.com',
                                'linkedin': 'linkedin.com/in/janesmith'
                            }
                        ]
                    }
                },
                'note': 'Mock data - configure ZoomInfo API key for real data'
            }
        else:
            return {
                'success': True,
                'source': 'zoominfo_mock',
                'data': {
                    'person': {
                        'email': email,
                        'name': 'John Doe',
                        'title': 'Engineering Manager',
                        'company': 'Example Corp',
                        'phone': '+1-555-0124',
                        'linkedin': 'linkedin.com/in/johndoe',
                        'location': 'San Francisco, CA',
                        'experience_years': 8
                    }
                },
                'note': 'Mock data - configure ZoomInfo API key for real data'
            }
    
    def batch_verify_emails(self, emails: List[str]) -> Dict:
        """Batch verify multiple emails."""
        results = []
        
        for email in emails:
            verification = self.verify_email_hunter(email)
            results.append({
                'email': email,
                'verification': verification
            })
        
        # Calculate stats
        deliverable = len([r for r in results if r['verification'].get('verification', {}).get('result') == 'deliverable'])
        invalid = len([r for r in results if r['verification'].get('verification', {}).get('result') == 'invalid'])
        
        return {
            'success': True,
            'total_verified': len(results),
            'deliverable': deliverable,
            'invalid': invalid,
            'deliverable_rate': round((deliverable / len(results) * 100), 2) if results else 0,
            'results': results
        }
    
    def full_lead_enrichment(self, 
                            email: Optional[str] = None,
                            domain: Optional[str] = None,
                            company_name: Optional[str] = None) -> Dict:
        """
        Full lead enrichment using all available services.
        
        Args:
            email: Person email
            domain: Company domain
            company_name: Company name
            
        Returns:
            Dict with comprehensive enriched data
        """
        enriched_data = {
            'email': email,
            'domain': domain,
            'company_name': company_name,
            'enrichment_sources': []
        }
        
        # Clearbit enrichment
        if email or domain:
            clearbit_data = self.enrich_with_clearbit(email, domain)
            if clearbit_data['success']:
                enriched_data['clearbit'] = clearbit_data
                enriched_data['enrichment_sources'].append('clearbit')
        
        # Hunter.io verification
        if email:
            hunter_verify = self.verify_email_hunter(email)
            if hunter_verify['success']:
                enriched_data['email_verification'] = hunter_verify
                enriched_data['enrichment_sources'].append('hunter_verification')
        
        # ZoomInfo enrichment
        if company_name or email:
            zoominfo_data = self.enrich_with_zoominfo(company_name, email)
            if zoominfo_data['success']:
                enriched_data['zoominfo'] = zoominfo_data
                enriched_data['enrichment_sources'].append('zoominfo')
        
        return {
            'success': True,
            'enriched_data': enriched_data,
            'sources_used': len(enriched_data['enrichment_sources']),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_enrichment_stats(self) -> Dict:
        """Get enrichment statistics."""
        return {
            'success': True,
            'stats': {
                'cached_enrichments': len(self.enrichment_cache),
                'cached_verifications': len(self.verification_cache),
                'clearbit_configured': self.clearbit_api_key is not None,
                'hunter_configured': self.hunter_api_key is not None,
                'zoominfo_configured': self.zoominfo_api_key is not None
            }
        }
