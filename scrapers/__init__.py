"""Initialize scrapers module."""
from scrapers.indeed_scraper import IndeedScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.remoteok_scraper import RemoteOKScraper
from scrapers.weworkremotely_scraper import WeWorkRemotelyScraper
from scrapers.glassdoor_scraper import GlassdoorScraper
from scrapers.monster_scraper import MonsterScraper
from scrapers.dice_scraper import DiceScraper
from scrapers.simplyhired_scraper import SimplyHiredScraper
from scrapers.ziprecruiter_scraper import ZipRecruiterScraper
from scrapers.angellist_scraper import AngelListScraper

__all__ = [
    'IndeedScraper',
    'LinkedInScraper',
    'RemoteOKScraper',
    'WeWorkRemotelyScraper',
    'GlassdoorScraper',
    'MonsterScraper',
    'DiceScraper',
    'SimplyHiredScraper',
    'ZipRecruiterScraper',
    'AngelListScraper',
]

# Optional Playwright variant for Glassdoor (used conditionally)
try:
    from scrapers.glassdoor_playwright import GlassdoorPlaywrightScraper
    __all__.append('GlassdoorPlaywrightScraper')
except Exception:
    GlassdoorPlaywrightScraper = None
