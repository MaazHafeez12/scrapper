"""Test Chrome WebDriver setup."""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

def test_chrome_driver():
    """Test ChromeDriver functionality."""
    try:
        # ChromeDriver path
        driver_path = r"C:\Users\Admin\.wdm\drivers\chromedriver\win64\141.0.7390.122\chromedriver-win32\chromedriver.exe"
        
        # Check if file exists
        if not os.path.exists(driver_path):
            print(f"ChromeDriver not found at: {driver_path}")
            return False
            
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Create service
        service = Service(driver_path)
        
        # Create driver
        print("Creating Chrome driver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test navigation
        print("Testing navigation...")
        driver.get("https://httpbin.org/get")
        
        # Get page title
        title = driver.title
        print(f"Page title: {title}")
        
        # Close driver
        driver.quit()
        
        print("✅ Chrome driver test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Chrome driver test failed: {e}")
        return False

if __name__ == "__main__":
    test_chrome_driver()