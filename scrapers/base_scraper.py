"""Base scraper class for all job platforms."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import config


class JobScraper(ABC):
    """Abstract base class for job scrapers."""
    
    def __init__(self, use_selenium: bool = config.USE_SELENIUM):
        """Initialize the scraper.
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript-heavy sites
        """
        self.use_selenium = use_selenium
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
        # Configure proxy for requests if provided
        if getattr(config, 'PROXY_URL', ''):
            try:
                self.session.proxies.update({'http': config.PROXY_URL, 'https': config.PROXY_URL})
            except Exception:
                pass
        
    def setup_driver(self):
        """Set up Selenium WebDriver with enhanced options."""
        if not self.driver:
            chrome_options = Options()
            
            # Headless mode
            if config.HEADLESS_MODE:
                chrome_options.add_argument('--headless=new')  # New headless mode
            
            # Performance and stability options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Anti-detection measures
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f'user-agent={config.USER_AGENT}')
            
            # Proxy support
            if getattr(config, 'PROXY_URL', ''):
                chrome_options.add_argument(f'--proxy-server={config.PROXY_URL}')
            
            # Optional Chrome/Chromium binary
            if getattr(config, 'BROWSER_BINARY', ''):
                try:
                    chrome_options.binary_location = config.BROWSER_BINARY
                except Exception:
                    pass
            
            # Preferences
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2 if not config.LOAD_IMAGES else 1,
                    'notifications': 2,
                    'geolocation': 2,
                }
            }
            if not config.LOAD_IMAGES:
                prefs['profile.managed_default_content_settings.images'] = 2
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Initialize driver with optional stealth (undetected-chromedriver)
            driver_initialized = False
            if getattr(config, 'USE_STEALTH', True) and getattr(config, 'STEALTH_BACKEND', 'undetected') == 'undetected':
                try:
                    import undetected_chromedriver as uc
                    self.driver = uc.Chrome(options=chrome_options)
                    driver_initialized = True
                except Exception as e:
                    print(f"[stealth] undetected-chromedriver failed: {e}. Falling back to standard ChromeDriver.")
            
            if not driver_initialized:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                driver_initialized = True
            
            # Additional anti-detection (best-effort)
            try:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": config.USER_AGENT
                })
            except Exception:
                pass
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception:
                pass
            
    def close_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            
    def get_page(self, url: str, wait_element: tuple = None, wait_time: int = 10) -> Optional[str]:
        """Get page content using requests or Selenium.
        
        Args:
            url: URL to fetch
            wait_element: Tuple of (By.XXX, 'selector') to wait for before returning
            wait_time: Maximum time to wait for element
            
        Returns:
            Page HTML content or None if failed
        """
        try:
            if self.use_selenium:
                self.setup_driver()
                self.driver.get(url)
                
                # Wait for specific element if provided
                if wait_element:
                    try:
                        WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_element_located(wait_element)
                        )
                    except TimeoutException:
                        print(f"Timeout waiting for element {wait_element} on {url}")
                else:
                    time.sleep(2)  # Default wait for page to load
                    
                # Scroll to load dynamic content
                self.scroll_page()
                
                return self.driver.page_source
            else:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    def scroll_page(self, scrolls: int = 3):
        """Scroll page to load dynamic content.
        
        Args:
            scrolls: Number of times to scroll
        """
        if not self.driver:
            return
            
        try:
            for _ in range(scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
        except Exception as e:
            print(f"Error scrolling page: {e}")
            
    def wait_for_element(self, by: By, selector: str, timeout: int = 10):
        """Wait for element to be present.
        
        Args:
            by: Selenium By selector type
            selector: Element selector
            timeout: Maximum wait time
            
        Returns:
            WebElement or None
        """
        if not self.driver:
            return None
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            return None
            
    def click_element(self, by: By, selector: str, timeout: int = 10) -> bool:
        """Click an element.
        
        Args:
            by: Selenium By selector type
            selector: Element selector
            timeout: Maximum wait time
            
        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            element.click()
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Error clicking element {selector}: {e}")
            return False
            
    def get_elements(self, by: By, selector: str):
        """Get multiple elements.
        
        Args:
            by: Selenium By selector type
            selector: Element selector
            
        Returns:
            List of WebElements
        """
        if not self.driver:
            return []
            
        try:
            return self.driver.find_elements(by, selector)
        except Exception:
            return []
            
    def delay(self):
        """Add delay between requests to be polite."""
        time.sleep(config.REQUEST_DELAY)
        
    @abstractmethod
    def build_search_url(self, filters: Dict) -> str:
        """Build search URL based on filters.
        
        Args:
            filters: Dictionary containing search filters
            
        Returns:
            Complete search URL
        """
        pass
        
    @abstractmethod
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Scrape jobs from the platform.
        
        Args:
            filters: Dictionary containing search filters
            
        Returns:
            List of job dictionaries
        """
        pass
        
    @abstractmethod
    def parse_job_card(self, card) -> Optional[Dict]:
        """Parse a single job card/listing.
        
        Args:
            card: BeautifulSoup element or Selenium element
            
        Returns:
            Dictionary with job details or None if parsing failed
        """
        pass
        
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
        
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close_driver()
