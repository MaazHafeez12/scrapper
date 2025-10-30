# Browser Automation Guide - Selenium & Playwright

## Overview

The Job Scraper Tool now supports **two powerful browser automation engines**:

### 🔵 **Selenium** (Default)
- Industry standard for web automation
- Excellent browser compatibility
- Mature and well-documented
- Auto-installs ChromeDriver via webdriver-manager

### 🟢 **Playwright** (Puppeteer Alternative)
- Modern, fast, and reliable
- Better performance than Selenium
- Advanced anti-detection features
- Cross-browser support (Chromium, Firefox, WebKit)
- Python equivalent of Puppeteer (Node.js)

---

## Installation

### Selenium (Already Installed)
```powershell
pip install -r requirements.txt
```

### Playwright Setup
```powershell
# Install Playwright
pip install playwright

# Install browsers (one-time setup)
python -m playwright install chromium
```

Or install all browsers:
```powershell
python -m playwright install
```

---

## Configuration

Edit `.env` file or `config.py`:

```ini
# Choose your automation engine
USE_SELENIUM=True        # Use Selenium
USE_PLAYWRIGHT=False     # Use Playwright (Puppeteer-like)

# Performance settings
HEADLESS_MODE=True       # Run browser in background
LOAD_IMAGES=False        # Disable images for faster scraping
REQUEST_DELAY=2          # Seconds between requests
```

---

## Enhanced Selenium Features

### Anti-Detection Measures
✅ **Stealth Mode**: Hides automation flags
✅ **User-Agent Spoofing**: Mimics real browsers
✅ **CDP Commands**: Advanced Chrome DevTools Protocol
✅ **Headless Detection Bypass**: Undetectable headless mode

### Smart Waiting
```python
# Wait for specific elements
html = scraper.get_page(url, wait_element=(By.CLASS_NAME, 'job-card'))

# Wait for element to be clickable
scraper.wait_for_element(By.ID, 'submit-button')

# Click with wait
scraper.click_element(By.CSS_SELECTOR, 'button.apply')
```

### Dynamic Content Loading
```python
# Auto-scroll to trigger lazy loading
scraper.scroll_page(scrolls=5)

# Get multiple elements
elements = scraper.get_elements(By.CLASS_NAME, 'job-listing')
```

### Performance Optimizations
- Images disabled by default (faster page loads)
- Popup blocking enabled
- GPU acceleration disabled
- Minimal resource usage

---

## Playwright Features (Puppeteer Alternative)

### Why Playwright?
Playwright is the **Python equivalent of Puppeteer** with these advantages:

✅ **Faster**: 30-50% faster than Selenium
✅ **More Reliable**: Better handling of dynamic content
✅ **Modern**: Built for modern web applications
✅ **Auto-Wait**: Automatically waits for elements
✅ **Network Control**: Intercept and modify requests
✅ **Cross-Browser**: Works with Chrome, Firefox, Safari

### Basic Usage

```python
from scrapers.indeed_playwright import IndeedPlaywrightScraper

scraper = IndeedPlaywrightScraper()
filters = {
    'keywords': 'python developer',
    'remote': True,
    'max_pages': 2
}

jobs = scraper.scrape_jobs(filters)
```

### Advanced Features

```python
# Navigate to page
await scraper.goto_page(url, wait_until='networkidle')

# Wait for selector
await scraper.wait_for_selector('.job-card', timeout=10000)

# Click element
await scraper.click_element('button#apply')

# Type text
await scraper.type_text('input#search', 'software engineer')

# Press keyboard keys
await scraper.press_key('Enter')

# Scroll page
await scraper.scroll_page(scrolls=5)

# Take screenshot
await scraper.screenshot('jobs_page.png')

# Get element text
texts = await scraper.get_elements_text('.job-title')
```

---

## Comparison: Selenium vs Playwright

| Feature | Selenium | Playwright |
|---------|----------|------------|
| **Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Reliability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Setup** | Easy | Requires browser install |
| **Anti-Detection** | Good | Excellent |
| **Documentation** | Excellent | Good |
| **Community** | Huge | Growing |
| **Browser Support** | All | Chromium, Firefox, WebKit |
| **Performance** | Good | Excellent |
| **Auto-Wait** | Manual | Automatic |

---

## Usage Examples

### Example 1: Selenium (Default)
```python
from scrapers.indeed_scraper import IndeedScraper

scraper = IndeedScraper()  # Uses Selenium by default
filters = {'keywords': 'python', 'remote': True}
jobs = scraper.scrape_jobs(filters)
```

### Example 2: Playwright (Puppeteer-like)
```python
from scrapers.indeed_playwright import IndeedPlaywrightScraper

scraper = IndeedPlaywrightScraper()
filters = {'keywords': 'python', 'remote': True}
jobs = scraper.scrape_jobs(filters)  # Async under the hood
```

### Example 3: Custom Selenium Scraping
```python
from scrapers.base_scraper import JobScraper
from selenium.webdriver.common.by import By

scraper = JobScraper(use_selenium=True)
scraper.setup_driver()

# Navigate
scraper.driver.get('https://example.com/jobs')

# Wait for element
scraper.wait_for_element(By.CLASS_NAME, 'job-list')

# Scroll to load more
scraper.scroll_page(scrolls=5)

# Get elements
jobs = scraper.get_elements(By.CSS_SELECTOR, '.job-card')
```

---

## Anti-Detection Features

### Selenium Anti-Detection
```python
# Implemented automatically in base_scraper.py:
- Disable automation flags
- Custom user agent
- CDP command execution
- Navigator.webdriver override
- Headless detection bypass
```

### Playwright Anti-Detection
```python
# Implemented automatically in playwright_scraper.py:
- WebDriver property hiding
- Navigator object modification
- Automatic stealth mode
- Realistic viewport sizes
- Human-like delays
```

---

## Performance Tips

### 1. Disable Image Loading
```python
# In config.py or .env
LOAD_IMAGES=False  # 2-3x faster page loads
```

### 2. Use Headless Mode
```python
HEADLESS_MODE=True  # No GUI overhead
```

### 3. Reduce Wait Times
```python
# Only wait for essential elements
html = scraper.get_page(url, wait_element=(By.CLASS_NAME, 'job-list'))
```

### 4. Limit Pages
```python
filters = {'keywords': 'python', 'max_pages': 2}  # Faster testing
```

### 5. Choose Playwright for Speed
```python
# Playwright is 30-50% faster than Selenium
from scrapers.indeed_playwright import IndeedPlaywrightScraper
```

---

## Troubleshooting

### Selenium Issues

**Problem: ChromeDriver not found**
```powershell
# Solution: Auto-installed via webdriver-manager
# If issues persist, manually download ChromeDriver
```

**Problem: Element not found**
```python
# Solution: Add explicit waits
scraper.wait_for_element(By.CLASS_NAME, 'job-card', timeout=15)
```

**Problem: Stale element reference**
```python
# Solution: Re-find elements after page changes
scraper.scroll_page()
html = scraper.driver.page_source  # Get fresh HTML
```

### Playwright Issues

**Problem: Browser not installed**
```powershell
# Solution: Install browsers
python -m playwright install chromium
```

**Problem: Async errors**
```python
# Solution: Use the synchronous wrapper
jobs = scraper.scrape_jobs(filters)  # Not scrape_jobs_async()
```

**Problem: Timeout errors**
```python
# Solution: Increase timeout
await scraper.wait_for_selector('.job-card', timeout=30000)
```

---

## Best Practices

### 1. Choose the Right Tool
- **Selenium**: For compatibility and stability
- **Playwright**: For speed and modern sites

### 2. Respectful Scraping
```python
# Use delays between requests
REQUEST_DELAY=2  # Minimum 2 seconds

# Limit concurrent requests
# Don't run multiple scrapers simultaneously
```

### 3. Error Handling
```python
try:
    jobs = scraper.scrape_jobs(filters)
except Exception as e:
    print(f"Scraping failed: {e}")
finally:
    scraper.close_driver()  # Always cleanup
```

### 4. Monitor Resource Usage
```python
# Close browser when done
scraper.close_driver()

# Use context managers (future enhancement)
with Scraper() as scraper:
    jobs = scraper.scrape_jobs(filters)
```

---

## Advanced Examples

### Example 1: LinkedIn with Infinite Scroll
```python
from scrapers.linkedin_scraper import LinkedInScraper

scraper = LinkedInScraper()
scraper.setup_driver()

# Scroll multiple times to load all jobs
for _ in range(5):
    scraper.scroll_page()
    time.sleep(1)
    
jobs = scraper.scrape_jobs(filters)
```

### Example 2: Close Glassdoor Popups
```python
from scrapers.glassdoor_scraper import GlassdoorScraper

scraper = GlassdoorScraper()
# Automatically closes popups in scrape_jobs()
jobs = scraper.scrape_jobs(filters)
```

### Example 3: Playwright Screenshot
```python
from scrapers.indeed_playwright import IndeedPlaywrightScraper
import asyncio

async def scrape_with_screenshot():
    scraper = IndeedPlaywrightScraper()
    await scraper.setup_browser()
    await scraper.goto_page('https://indeed.com')
    await scraper.screenshot('indeed_homepage.png')
    await scraper.close_browser()

asyncio.run(scrape_with_screenshot())
```

---

## Summary

✅ **Selenium**: Mature, stable, easy to use
✅ **Playwright**: Fast, modern, Puppeteer alternative
✅ **Anti-Detection**: Both engines have stealth features
✅ **Performance**: Optimized for speed and efficiency
✅ **Flexibility**: Choose the best tool for your needs

**Recommendation**: 
- Start with **Selenium** (default, easier setup)
- Switch to **Playwright** for better performance

---

## Quick Commands

```powershell
# Install Selenium (default)
pip install -r requirements.txt

# Install Playwright
pip install playwright
python -m playwright install chromium

# Test Selenium scraper
python main.py --keywords "python" --platforms indeed --max-pages 1

# Test Playwright scraper (create custom script)
python examples_playwright.py
```

Happy scraping! 🚀
