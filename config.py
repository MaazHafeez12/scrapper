"""Configuration settings for the job scraper."""
import os
from dotenv import load_dotenv

load_dotenv()

# Scraping settings
USE_SELENIUM = os.getenv('USE_SELENIUM', 'True').lower() == 'true'
USE_PLAYWRIGHT = os.getenv('USE_PLAYWRIGHT', 'False').lower() == 'true'  # Puppeteer alternative
HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'
REQUEST_DELAY = int(os.getenv('REQUEST_DELAY', '2'))
MAX_PAGES = int(os.getenv('MAX_PAGES', '5'))
LOAD_IMAGES = os.getenv('LOAD_IMAGES', 'False').lower() == 'true'  # Disable for faster scraping

# Stealth/anti-bot settings
USE_STEALTH = os.getenv('USE_STEALTH', 'True').lower() == 'true'
# Options: 'undetected' (undetected-chromedriver) or 'playwright'
STEALTH_BACKEND = os.getenv('STEALTH_BACKEND', 'undetected').strip().lower()

# Network/proxy settings (e.g., http://user:pass@host:port)
PROXY_URL = os.getenv('PROXY_URL', '').strip()

# Optional: Path to Chrome/Chromium binary (leave empty to auto-detect)
BROWSER_BINARY = os.getenv('BROWSER_BINARY', '').strip()

# User credentials (optional, for platforms requiring login)
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', '')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')

# Output settings
OUTPUT_DIR = 'output'
OUTPUT_FORMAT = 'csv'  # csv, json, or both

# Supported platforms
PLATFORMS = [
    'indeed',
    'linkedin',
    'glassdoor',
    'remoteok',
    'weworkremotely',
    'monster',
    'dice',
    'simplyhired',
    'ziprecruiter',
    'angellist'
]

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.16 Safari/537.36'

# Auto-scrape scheduler
AUTO_SCRAPE_ENABLED = os.getenv('AUTO_SCRAPE_ENABLED', 'False').lower() == 'true'
AUTO_SCRAPE_INTERVAL_MINUTES = int(os.getenv('AUTO_SCRAPE_INTERVAL_MINUTES', '120'))  # every 2h by default

# Default search filters for auto-scrape
DEFAULT_KEYWORDS = os.getenv('DEFAULT_KEYWORDS', '')
DEFAULT_LOCATION = os.getenv('DEFAULT_LOCATION', '')
DEFAULT_REMOTE = os.getenv('DEFAULT_REMOTE', 'True').lower() == 'true'
DEFAULT_MAX_PAGES = int(os.getenv('DEFAULT_MAX_PAGES', str(MAX_PAGES)))

# Space/comma separated list of platforms in env; otherwise use PLATFORMS
_env_platforms = os.getenv('DEFAULT_PLATFORMS', '')
if _env_platforms:
    DEFAULT_PLATFORMS = [p.strip().lower() for p in _env_platforms.replace(',', ' ').split() if p.strip()]
else:
    DEFAULT_PLATFORMS = PLATFORMS
