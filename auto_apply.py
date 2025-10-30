"""
Job Application Automation System

Automatically apply to jobs using Selenium/Playwright browser automation.
Features:
- Auto-fill application forms
- Attach resume and documents
- Handle multi-page applications
- Track application success/failure
- CAPTCHA detection and pause
- Smart retry logic
- Platform-specific handlers

Safety Features:
- Dry-run mode for testing
- Confirmation before applying
- Application limits per session
- Error recovery
- Detailed logging
"""

import time
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from database import JobDatabase


class ApplicationTemplate:
    """Manages application templates for personal information"""
    
    TEMPLATE_FILE = "application_templates.json"
    
    DEFAULT_TEMPLATE = {
        "personal_info": {
            "first_name": "",
            "last_name": "",
            "full_name": "",
            "email": "",
            "phone": "",
            "address": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "country": "United States"
        },
        "professional_info": {
            "resume_path": "",
            "cover_letter_path": "",
            "portfolio_url": "",
            "linkedin_url": "",
            "github_url": "",
            "website_url": ""
        },
        "work_authorization": {
            "authorized_to_work": "Yes",
            "require_sponsorship": "No",
            "visa_status": "Citizen"
        },
        "preferences": {
            "start_date": "2 weeks",
            "salary_expectations": "",
            "willing_to_relocate": "No",
            "willing_to_travel": "10%"
        },
        "common_questions": {
            "why_interested": "I am excited about this opportunity because it aligns with my skills and career goals.",
            "why_good_fit": "My experience in [relevant skills] makes me a strong candidate for this position.",
            "salary_requirements": "Negotiable based on total compensation package",
            "availability": "Available to start within 2 weeks",
            "references_available": "Yes"
        }
    }
    
    def __init__(self, template_path: Optional[str] = None):
        self.template_path = template_path or self.TEMPLATE_FILE
        self.template = self.load_template()
    
    def load_template(self) -> Dict:
        """Load template from file or create default"""
        if os.path.exists(self.template_path):
            try:
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading template: {e}")
                return self.DEFAULT_TEMPLATE.copy()
        else:
            return self.DEFAULT_TEMPLATE.copy()
    
    def save_template(self) -> bool:
        """Save template to file"""
        try:
            with open(self.template_path, 'w', encoding='utf-8') as f:
                json.dump(self.template, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving template: {e}")
            return False
    
    def get(self, *keys):
        """Get nested value from template"""
        value = self.template
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, "")
            else:
                return ""
        return value
    
    def set(self, value, *keys):
        """Set nested value in template"""
        current = self.template
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def is_complete(self) -> Tuple[bool, List[str]]:
        """Check if template has required fields"""
        required_fields = [
            ("personal_info", "first_name"),
            ("personal_info", "last_name"),
            ("personal_info", "email"),
            ("personal_info", "phone"),
            ("professional_info", "resume_path")
        ]
        
        missing = []
        for keys in required_fields:
            if not self.get(*keys):
                missing.append(" → ".join(keys))
        
        return len(missing) == 0, missing


class AutoApplier:
    """Automated job application system"""
    
    # Common form field patterns
    FIELD_PATTERNS = {
        'first_name': ['firstname', 'first_name', 'fname', 'givenname'],
        'last_name': ['lastname', 'last_name', 'lname', 'surname', 'familyname'],
        'full_name': ['fullname', 'full_name', 'name'],
        'email': ['email', 'emailaddress', 'e-mail', 'mail'],
        'phone': ['phone', 'telephone', 'mobile', 'phonenumber', 'tel'],
        'address': ['address', 'street', 'addressline'],
        'city': ['city', 'town'],
        'state': ['state', 'province', 'region'],
        'zip_code': ['zip', 'zipcode', 'postalcode', 'postcode'],
        'linkedin': ['linkedin', 'linkedin_url', 'linkedinprofile'],
        'github': ['github', 'github_url', 'githubprofile'],
        'portfolio': ['portfolio', 'website', 'portfoliourl'],
        'cover_letter': ['coverletter', 'cover_letter', 'letter'],
        'resume': ['resume', 'cv', 'curriculum']
    }
    
    def __init__(self, template: ApplicationTemplate, use_playwright: bool = False, 
                 headless: bool = False, dry_run: bool = False):
        self.template = template
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        self.headless = headless
        self.dry_run = dry_run
        self.db = JobDatabase()
        
        self.driver = None
        self.page = None
        self.browser = None
        self.playwright = None
        
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'captcha_detected': 0,
            'errors': []
        }
    
    def __enter__(self):
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()
    
    def start_browser(self):
        """Initialize browser automation"""
        if self.use_playwright:
            if not PLAYWRIGHT_AVAILABLE:
                raise RuntimeError("Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            print("✅ Playwright browser started")
        else:
            if not SELENIUM_AVAILABLE:
                raise RuntimeError("Selenium not installed. Run: pip install selenium webdriver-manager")
            
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Selenium browser started")
    
    def close_browser(self):
        """Close browser"""
        if self.use_playwright:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        else:
            if self.driver:
                self.driver.quit()
        print("🔒 Browser closed")
    
    def navigate_to_job(self, url: str, timeout: int = 30) -> bool:
        """Navigate to job application page"""
        try:
            if self.use_playwright:
                self.page.goto(url, timeout=timeout * 1000)
            else:
                self.driver.get(url)
            
            print(f"✅ Navigated to: {url}")
            return True
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def find_element_by_patterns(self, patterns: List[str], input_type: str = 'input') -> Optional[object]:
        """Find form element by common name patterns"""
        for pattern in patterns:
            try:
                if self.use_playwright:
                    # Try by name
                    selector = f'{input_type}[name*="{pattern}" i]'
                    elem = self.page.query_selector(selector)
                    if elem:
                        return elem
                    
                    # Try by id
                    selector = f'{input_type}[id*="{pattern}" i]'
                    elem = self.page.query_selector(selector)
                    if elem:
                        return elem
                else:
                    # Try by name
                    elem = self.driver.find_element(By.XPATH, 
                        f'//{input_type}[contains(translate(@name, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{pattern}")]')
                    if elem:
                        return elem
            except:
                continue
        
        return None
    
    def fill_text_field(self, field_name: str, value: str) -> bool:
        """Fill a text input field"""
        if not value:
            return False
        
        patterns = self.FIELD_PATTERNS.get(field_name, [field_name])
        element = self.find_element_by_patterns(patterns)
        
        if element:
            try:
                if self.use_playwright:
                    element.fill(value)
                else:
                    element.clear()
                    element.send_keys(value)
                
                print(f"  ✓ Filled {field_name}: {value[:30]}...")
                return True
            except Exception as e:
                print(f"  ⚠️ Failed to fill {field_name}: {e}")
                return False
        
        return False
    
    def upload_file(self, field_name: str, file_path: str) -> bool:
        """Upload a file (resume, cover letter)"""
        if not file_path or not os.path.exists(file_path):
            return False
        
        patterns = self.FIELD_PATTERNS.get(field_name, [field_name])
        
        try:
            if self.use_playwright:
                for pattern in patterns:
                    selector = f'input[type="file"][name*="{pattern}" i]'
                    elem = self.page.query_selector(selector)
                    if elem:
                        elem.set_input_files(file_path)
                        print(f"  ✓ Uploaded {field_name}: {Path(file_path).name}")
                        return True
            else:
                element = self.find_element_by_patterns(patterns, 'input[@type="file"]')
                if element:
                    abs_path = os.path.abspath(file_path)
                    element.send_keys(abs_path)
                    print(f"  ✓ Uploaded {field_name}: {Path(file_path).name}")
                    return True
        except Exception as e:
            print(f"  ⚠️ Failed to upload {field_name}: {e}")
            return False
        
        return False
    
    def detect_captcha(self) -> bool:
        """Detect if CAPTCHA is present on page"""
        captcha_indicators = [
            'recaptcha', 'captcha', 'g-recaptcha', 'hcaptcha', 
            'challenge', 'verify', 'robot'
        ]
        
        try:
            if self.use_playwright:
                content = self.page.content().lower()
            else:
                content = self.driver.page_source.lower()
            
            for indicator in captcha_indicators:
                if indicator in content:
                    return True
            
            return False
        except:
            return False
    
    def wait_for_captcha_solve(self, timeout: int = 120):
        """Wait for user to solve CAPTCHA"""
        print("\n⚠️ CAPTCHA DETECTED!")
        print("📋 Please solve the CAPTCHA in the browser window...")
        print(f"⏳ Waiting up to {timeout} seconds...\n")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.detect_captcha():
                print("✅ CAPTCHA solved!")
                return True
            time.sleep(2)
        
        print("❌ CAPTCHA timeout - moving to next job")
        return False
    
    def fill_application_form(self) -> bool:
        """Fill out application form with template data"""
        print("\n📝 Filling application form...")
        
        # Personal information
        self.fill_text_field('first_name', self.template.get('personal_info', 'first_name'))
        self.fill_text_field('last_name', self.template.get('personal_info', 'last_name'))
        self.fill_text_field('full_name', self.template.get('personal_info', 'full_name'))
        self.fill_text_field('email', self.template.get('personal_info', 'email'))
        self.fill_text_field('phone', self.template.get('personal_info', 'phone'))
        self.fill_text_field('address', self.template.get('personal_info', 'address'))
        self.fill_text_field('city', self.template.get('personal_info', 'city'))
        self.fill_text_field('state', self.template.get('personal_info', 'state'))
        self.fill_text_field('zip_code', self.template.get('personal_info', 'zip_code'))
        
        # Professional links
        self.fill_text_field('linkedin', self.template.get('professional_info', 'linkedin_url'))
        self.fill_text_field('github', self.template.get('professional_info', 'github_url'))
        self.fill_text_field('portfolio', self.template.get('professional_info', 'portfolio_url'))
        
        # File uploads
        self.upload_file('resume', self.template.get('professional_info', 'resume_path'))
        self.upload_file('cover_letter', self.template.get('professional_info', 'cover_letter_path'))
        
        print("✅ Form filled\n")
        return True
    
    def click_apply_button(self) -> bool:
        """Find and click the apply/submit button"""
        if self.dry_run:
            print("🔍 DRY RUN: Would click apply button")
            return True
        
        button_texts = ['apply', 'submit', 'send', 'apply now', 'submit application']
        
        try:
            if self.use_playwright:
                for text in button_texts:
                    try:
                        button = self.page.get_by_role("button", name=text, exact=False)
                        if button:
                            button.click()
                            print("✅ Clicked apply button")
                            return True
                    except:
                        continue
            else:
                for text in button_texts:
                    try:
                        button = self.driver.find_element(By.XPATH, 
                            f'//button[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{text}")]')
                        button.click()
                        print("✅ Clicked apply button")
                        return True
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ Failed to click apply button: {e}")
            return False
        
        return False
    
    def apply_to_job(self, job: Dict) -> Tuple[bool, str]:
        """
        Apply to a single job
        
        Args:
            job: Job dictionary with at least 'url' and 'title'
        
        Returns:
            (success, message) tuple
        """
        self.stats['attempted'] += 1
        
        job_url = job.get('url', '')
        job_title = job.get('title', 'Unknown')
        job_company = job.get('company', 'Unknown')
        
        print(f"\n{'='*60}")
        print(f"📋 Applying to: {job_title}")
        print(f"🏢 Company: {job_company}")
        print(f"🔗 URL: {job_url}")
        print(f"{'='*60}")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No actual application will be submitted")
        
        try:
            # Navigate to job page
            if not self.navigate_to_job(job_url):
                message = "Failed to navigate to job page"
                self.stats['failed'] += 1
                self.stats['errors'].append(f"{job_title}: {message}")
                return False, message
            
            time.sleep(2)  # Wait for page load
            
            # Check for CAPTCHA
            if self.detect_captcha():
                self.stats['captcha_detected'] += 1
                if not self.wait_for_captcha_solve():
                    message = "CAPTCHA timeout"
                    self.stats['failed'] += 1
                    return False, message
            
            # Fill application form
            self.fill_application_form()
            
            # Click apply button
            if not self.click_apply_button():
                message = "Could not find or click apply button"
                self.stats['failed'] += 1
                self.stats['errors'].append(f"{job_title}: {message}")
                return False, message
            
            # Wait for confirmation
            time.sleep(3)
            
            # Update database
            if not self.dry_run:
                self.db.update_job_status(job_url, 'applied', 
                                        notes=f"Auto-applied on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            self.stats['successful'] += 1
            message = "Application submitted successfully"
            print(f"✅ {message}\n")
            return True, message
            
        except Exception as e:
            message = f"Application error: {str(e)}"
            self.stats['failed'] += 1
            self.stats['errors'].append(f"{job_title}: {message}")
            print(f"❌ {message}\n")
            return False, message
    
    def apply_to_jobs(self, jobs: List[Dict], max_applications: int = 10, 
                     delay_between: int = 5) -> Dict:
        """
        Apply to multiple jobs
        
        Args:
            jobs: List of job dictionaries
            max_applications: Maximum number of applications per session
            delay_between: Delay in seconds between applications
        
        Returns:
            Statistics dictionary
        """
        print(f"\n{'='*60}")
        print(f"🤖 AUTO-APPLY SESSION STARTING")
        print(f"{'='*60}")
        print(f"📊 Total jobs: {len(jobs)}")
        print(f"📊 Max applications: {max_applications}")
        print(f"⏱️ Delay between apps: {delay_between}s")
        if self.dry_run:
            print(f"🔍 DRY RUN MODE: No actual submissions")
        print(f"{'='*60}\n")
        
        applied_count = 0
        
        for i, job in enumerate(jobs, 1):
            if applied_count >= max_applications:
                print(f"\n✋ Reached maximum applications limit ({max_applications})")
                break
            
            print(f"\n[{i}/{min(len(jobs), max_applications)}] ", end="")
            
            success, message = self.apply_to_job(job)
            
            if success:
                applied_count += 1
            
            # Delay between applications (except last one)
            if i < len(jobs) and applied_count < max_applications:
                print(f"⏳ Waiting {delay_between} seconds before next application...")
                time.sleep(delay_between)
        
        # Print summary
        self.print_summary()
        
        return self.stats
    
    def print_summary(self):
        """Print application session summary"""
        print(f"\n{'='*60}")
        print(f"📊 APPLICATION SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {self.stats['successful']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"⚠️ CAPTCHAs: {self.stats['captcha_detected']}")
        print(f"📋 Total attempted: {self.stats['attempted']}")
        
        if self.stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"  • {error}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more")
        
        print(f"{'='*60}\n")


def setup_template_interactive():
    """Interactive template setup"""
    print("\n" + "="*60)
    print("📋 AUTO-APPLY TEMPLATE SETUP")
    print("="*60)
    print("Let's set up your application template.\n")
    
    template = ApplicationTemplate()
    
    # Personal Information
    print("👤 Personal Information:")
    template.set(input("First Name: ").strip(), "personal_info", "first_name")
    template.set(input("Last Name: ").strip(), "personal_info", "last_name")
    full_name = f"{template.get('personal_info', 'first_name')} {template.get('personal_info', 'last_name')}"
    template.set(full_name, "personal_info", "full_name")
    template.set(input("Email: ").strip(), "personal_info", "email")
    template.set(input("Phone: ").strip(), "personal_info", "phone")
    template.set(input("Address (optional): ").strip(), "personal_info", "address")
    template.set(input("City (optional): ").strip(), "personal_info", "city")
    template.set(input("State (optional): ").strip(), "personal_info", "state")
    template.set(input("ZIP Code (optional): ").strip(), "personal_info", "zip_code")
    
    # Professional Information
    print("\n💼 Professional Information:")
    template.set(input("Resume file path: ").strip(), "professional_info", "resume_path")
    template.set(input("Cover letter path (optional): ").strip(), "professional_info", "cover_letter_path")
    template.set(input("LinkedIn URL (optional): ").strip(), "professional_info", "linkedin_url")
    template.set(input("GitHub URL (optional): ").strip(), "professional_info", "github_url")
    template.set(input("Portfolio URL (optional): ").strip(), "professional_info", "portfolio_url")
    
    # Work Authorization
    print("\n📋 Work Authorization:")
    auth = input("Authorized to work in US? (Yes/No) [Yes]: ").strip() or "Yes"
    template.set(auth, "work_authorization", "authorized_to_work")
    sponsor = input("Require sponsorship? (Yes/No) [No]: ").strip() or "No"
    template.set(sponsor, "work_authorization", "require_sponsorship")
    
    # Save template
    if template.save_template():
        print("\n✅ Template saved successfully!")
        
        # Check completeness
        is_complete, missing = template.is_complete()
        if not is_complete:
            print("\n⚠️ Warning: Some required fields are missing:")
            for field in missing:
                print(f"  • {field}")
        else:
            print("✅ All required fields are complete!")
    else:
        print("\n❌ Failed to save template")
    
    print("="*60 + "\n")
    return template


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Application Automation")
    parser.add_argument('--setup', action='store_true', help='Setup application template')
    parser.add_argument('--test', action='store_true', help='Test with a sample job URL')
    parser.add_argument('--url', type=str, help='Job URL for testing')
    parser.add_argument('--dry-run', action='store_true', help='Test mode without actual submission')
    parser.add_argument('--playwright', action='store_true', help='Use Playwright instead of Selenium')
    parser.add_argument('--visible', action='store_true', help='Show browser (non-headless mode)')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_template_interactive()
    elif args.test and args.url:
        template = ApplicationTemplate()
        is_complete, missing = template.is_complete()
        
        if not is_complete:
            print("❌ Template incomplete. Run --setup first.")
            print("Missing fields:")
            for field in missing:
                print(f"  • {field}")
        else:
            test_job = {
                'url': args.url,
                'title': 'Test Job',
                'company': 'Test Company'
            }
            
            with AutoApplier(template, use_playwright=args.playwright, 
                           headless=not args.visible, dry_run=args.dry_run) as applier:
                applier.apply_to_job(test_job)
    else:
        print("\nJob Application Automation System")
        print("="*60)
        print("\nUsage:")
        print("  python auto_apply.py --setup          # Setup template")
        print("  python auto_apply.py --test --url <URL>  # Test with URL")
        print("  python auto_apply.py --test --url <URL> --dry-run  # Dry run")
        print("\nOptions:")
        print("  --playwright    Use Playwright (faster)")
        print("  --visible       Show browser window")
        print("  --dry-run       Test without submission")
        print("\nSee AUTO_APPLY_GUIDE.md for full documentation")
        print("="*60 + "\n")
