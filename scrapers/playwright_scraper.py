"""Playwright-based scraper for advanced browser automation (Puppeteer alternative)."""
from abc import abstractmethod
from typing import List, Dict, Optional
import asyncio
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
try:
    # Optional stealth plugin
    from playwright_stealth import stealth_async
except Exception:
    stealth_async = None
import config


class PlaywrightScraper:
    """Base class for scrapers using Playwright (Puppeteer alternative for Python)."""
    
    def __init__(self, headless: bool = config.HEADLESS_MODE):
        """Initialize Playwright scraper.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def setup_browser(self):
        """Set up Playwright browser with advanced options."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            
        # Launch Chromium (similar to Puppeteer)
        launch_kwargs = {
            'headless': self.headless,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-blink-features=AutomationControlled'
            ]
        }
        if getattr(config, 'PROXY_URL', ''):
            launch_kwargs['proxy'] = { 'server': config.PROXY_URL }
        self.browser = await self.playwright.chromium.launch(**launch_kwargs)
        
        # Create browser context with custom settings
        context_kwargs = dict(
            viewport={'width': 1920, 'height': 1080},
            user_agent=config.USER_AGENT,
            ignore_https_errors=True,
            java_script_enabled=True
        )
        context = await self.browser.new_context(**context_kwargs)
        
        # Create new page
        self.page = await context.new_page()
        
        # Anti-detection measures
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        # Apply Playwright stealth if available and enabled
        if getattr(config, 'USE_STEALTH', True) and getattr(config, 'STEALTH_BACKEND', 'undetected') == 'playwright' and stealth_async:
            try:
                await stealth_async(self.page)
            except Exception as e:
                print(f"[stealth] playwright-stealth failed: {e}")
        
    async def close_browser(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
            
        if self.browser:
            await self.browser.close()
            
        if self.playwright:
            await self.playwright.stop()
            
    async def goto_page(self, url: str, wait_until: str = 'networkidle') -> bool:
        """Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation succeeded
                       ('load', 'domcontentloaded', 'networkidle')
            
        Returns:
            True if navigation succeeded, False otherwise
        """
        try:
            if not self.page:
                await self.setup_browser()
                
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return False
            
    async def get_html(self) -> str:
        """Get current page HTML content.
        
        Returns:
            Page HTML as string
        """
        if not self.page:
            return ""
            
        return await self.page.content()
        
    async def wait_for_selector(self, selector: str, timeout: int = 10000):
        """Wait for element to appear.
        
        Args:
            selector: CSS selector
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Element handle or None
        """
        if not self.page:
            return None
            
        try:
            return await self.page.wait_for_selector(selector, timeout=timeout)
        except PlaywrightTimeout:
            return None
            
    async def click_element(self, selector: str) -> bool:
        """Click an element.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            if not self.page:
                return False
                
            await self.page.click(selector)
            return True
        except Exception as e:
            print(f"Error clicking {selector}: {e}")
            return False
            
    async def scroll_page(self, scrolls: int = 3):
        """Scroll page to load dynamic content.
        
        Args:
            scrolls: Number of times to scroll
        """
        if not self.page:
            return
            
        for _ in range(scrolls):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)
            
    async def get_elements_text(self, selector: str) -> List[str]:
        """Get text content of all matching elements.
        
        Args:
            selector: CSS selector
            
        Returns:
            List of text contents
        """
        if not self.page:
            return []
            
        try:
            elements = await self.page.query_selector_all(selector)
            texts = []
            for elem in elements:
                text = await elem.inner_text()
                texts.append(text)
            return texts
        except Exception:
            return []
            
    async def screenshot(self, path: str = 'screenshot.png'):
        """Take a screenshot of current page.
        
        Args:
            path: File path to save screenshot
        """
        if not self.page:
            return
            
        await self.page.screenshot(path=path)
        
    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into an input field.
        
        Args:
            selector: CSS selector for input field
            text: Text to type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.page:
                return False
                
            await self.page.fill(selector, text)
            return True
        except Exception as e:
            print(f"Error typing into {selector}: {e}")
            return False
            
    async def press_key(self, key: str) -> bool:
        """Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Escape')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.page:
                return False
                
            await self.page.keyboard.press(key)
            return True
        except Exception as e:
            print(f"Error pressing key {key}: {e}")
            return False
            
    @abstractmethod
    async def scrape_jobs_async(self, filters: Dict) -> List[Dict]:
        """Scrape jobs asynchronously.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        pass
        
    def scrape_jobs(self, filters: Dict) -> List[Dict]:
        """Synchronous wrapper for async scraping.
        
        Args:
            filters: Search filters
            
        Returns:
            List of job dictionaries
        """
        return asyncio.run(self.scrape_jobs_async(filters))
        
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if self.browser:
                asyncio.run(self.close_browser())
        except:
            pass
