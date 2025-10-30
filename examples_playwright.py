"""Examples using Playwright (Puppeteer alternative for Python)."""
import asyncio
from scrapers.indeed_playwright import IndeedPlaywrightScraper
from export import DataExporter


async def example_playwright_basic():
    """Example: Basic job search with Playwright."""
    print("Example 1: Playwright - Remote Python Jobs")
    print("=" * 60)
    
    scraper = IndeedPlaywrightScraper()
    filters = {
        'keywords': 'python developer',
        'remote': True,
        'max_pages': 1
    }
    
    # This runs async under the hood but returns synchronously
    jobs = scraper.scrape_jobs(filters)
    
    print(f"Found {len(jobs)} jobs using Playwright")
    
    if jobs:
        exporter = DataExporter()
        exporter.export_to_csv(jobs, 'playwright_jobs_example.csv')
        exporter.display_jobs(jobs, limit=5)


async def example_playwright_advanced():
    """Example: Advanced Playwright usage with custom actions."""
    print("\nExample 2: Advanced Playwright - Custom Navigation")
    print("=" * 60)
    
    scraper = IndeedPlaywrightScraper()
    
    try:
        # Setup browser
        await scraper.setup_browser()
        
        # Navigate to Indeed
        print("Navigating to Indeed...")
        await scraper.goto_page('https://www.indeed.com')
        
        # Wait for search box
        search_box = await scraper.wait_for_selector('input[name="q"]', timeout=10000)
        if search_box:
            print("Search box found!")
            
        # Type search query
        await scraper.type_text('input[name="q"]', 'software engineer')
        await scraper.type_text('input[name="l"]', 'Remote')
        
        # Press Enter to search
        await scraper.press_key('Enter')
        
        # Wait for results to load
        await asyncio.sleep(3)
        await scraper.wait_for_selector('.job_seen_beacon', timeout=10000)
        
        # Scroll to load more jobs
        print("Scrolling to load jobs...")
        await scraper.scroll_page(scrolls=3)
        
        # Take a screenshot
        print("Taking screenshot...")
        await scraper.screenshot('output/indeed_search_results.png')
        
        # Get page HTML
        html = await scraper.get_html()
        
        # Parse jobs (simplified)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        print(f"Found {len(job_cards)} job cards")
        
        # Get job titles
        job_titles = await scraper.get_elements_text('h2.jobTitle')
        print(f"\nFirst 5 job titles:")
        for i, title in enumerate(job_titles[:5], 1):
            print(f"{i}. {title}")
            
    finally:
        # Always close browser
        await scraper.close_browser()


async def example_playwright_screenshot():
    """Example: Take screenshots of job search results."""
    print("\nExample 3: Screenshot Job Search Pages")
    print("=" * 60)
    
    scraper = IndeedPlaywrightScraper()
    
    try:
        await scraper.setup_browser()
        
        searches = [
            ('python developer', 'Remote'),
            ('data scientist', 'New York'),
            ('web developer', 'San Francisco')
        ]
        
        for i, (job_title, location) in enumerate(searches, 1):
            print(f"Searching: {job_title} in {location}")
            
            # Build URL
            from urllib.parse import quote
            url = f"https://www.indeed.com/jobs?q={quote(job_title)}&l={quote(location)}"
            
            # Navigate
            await scraper.goto_page(url)
            
            # Wait for jobs to load
            await scraper.wait_for_selector('.job_seen_beacon', timeout=10000)
            await asyncio.sleep(2)
            
            # Take screenshot
            filename = f'output/indeed_{job_title.replace(" ", "_")}_{i}.png'
            await scraper.screenshot(filename)
            print(f"Screenshot saved: {filename}")
            
    finally:
        await scraper.close_browser()


async def example_compare_selenium_playwright():
    """Example: Compare Selenium vs Playwright performance."""
    print("\nExample 4: Performance Comparison")
    print("=" * 60)
    
    import time
    
    filters = {
        'keywords': 'software engineer',
        'remote': True,
        'max_pages': 1
    }
    
    # Test Playwright
    print("\n--- Testing Playwright ---")
    start = time.time()
    
    playwright_scraper = IndeedPlaywrightScraper()
    playwright_jobs = playwright_scraper.scrape_jobs(filters)
    
    playwright_time = time.time() - start
    print(f"Playwright: Found {len(playwright_jobs)} jobs in {playwright_time:.2f} seconds")
    
    # Test Selenium
    print("\n--- Testing Selenium ---")
    start = time.time()
    
    from scrapers.indeed_scraper import IndeedScraper
    selenium_scraper = IndeedScraper()
    selenium_jobs = selenium_scraper.scrape_jobs(filters)
    selenium_scraper.close_driver()
    
    selenium_time = time.time() - start
    print(f"Selenium: Found {len(selenium_jobs)} jobs in {selenium_time:.2f} seconds")
    
    # Compare
    print("\n--- Results ---")
    print(f"Playwright: {playwright_time:.2f}s")
    print(f"Selenium: {selenium_time:.2f}s")
    
    if playwright_time < selenium_time:
        speedup = (selenium_time - playwright_time) / selenium_time * 100
        print(f"Playwright is {speedup:.1f}% faster!")
    else:
        speedup = (playwright_time - selenium_time) / playwright_time * 100
        print(f"Selenium is {speedup:.1f}% faster!")


def run_async_example(example_func):
    """Helper to run async examples."""
    asyncio.run(example_func())


if __name__ == '__main__':
    print("=" * 60)
    print("PLAYWRIGHT EXAMPLES (Puppeteer Alternative)")
    print("=" * 60)
    print()
    
    # Choose which examples to run
    print("Select an example to run:")
    print("1. Basic Playwright scraping")
    print("2. Advanced Playwright features")
    print("3. Screenshot multiple searches")
    print("4. Compare Selenium vs Playwright")
    print("5. Run all examples")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        run_async_example(example_playwright_basic)
    elif choice == '2':
        run_async_example(example_playwright_advanced)
    elif choice == '3':
        run_async_example(example_playwright_screenshot)
    elif choice == '4':
        run_async_example(example_compare_selenium_playwright)
    elif choice == '5':
        run_async_example(example_playwright_basic)
        run_async_example(example_playwright_advanced)
        run_async_example(example_playwright_screenshot)
        run_async_example(example_compare_selenium_playwright)
    else:
        print("Invalid choice. Running basic example...")
        run_async_example(example_playwright_basic)
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("Check the 'output' folder for screenshots and CSV files.")
    print("=" * 60)
