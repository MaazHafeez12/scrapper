"""
JOB SCRAPER TOOL - PROJECT OVERVIEW
====================================

A comprehensive, multi-platform job scraper with advanced filtering capabilities.

FEATURES
--------
✅ Multi-Platform Support:
   - Indeed
   - LinkedIn  
   - Glassdoor
   - RemoteOK
   - WeWorkRemotely

✅ Advanced Filters:
   - Keywords search
   - Location filtering
   - Remote jobs only
   - Job type (full-time, part-time, contract, internship)
   - Minimum salary requirements
   - Exclude keywords
   - Company filtering

✅ Smart Processing:
   - Automatic deduplication
   - Results sorting
   - Summary statistics
   - Beautiful console output with Rich library

✅ Export Formats:
   - CSV
   - JSON
   - Excel (XLSX)

PROJECT STRUCTURE
-----------------
Scrapper/
├── main.py                      # Main CLI application
├── config.py                    # Configuration settings
├── filters.py                   # Job filtering logic
├── export.py                    # Data export utilities
├── examples.py                  # Usage examples
├── requirements.txt             # Python dependencies
├── README.md                    # Full documentation
├── QUICKSTART.md               # Quick start guide
├── run.bat                     # Windows launcher script
├── setup.sh                    # Unix setup script
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── scrapers/                  # Scraper modules
│   ├── __init__.py
│   ├── base_scraper.py       # Abstract base class
│   ├── indeed_scraper.py     # Indeed.com scraper
│   ├── linkedin_scraper.py   # LinkedIn scraper
│   ├── glassdoor_scraper.py  # Glassdoor scraper
│   ├── remoteok_scraper.py   # RemoteOK scraper
│   └── weworkremotely_scraper.py  # WeWorkRemotely scraper
└── output/                    # Export directory
    └── README.md

QUICK START
-----------
1. Install dependencies:
   pip install -r requirements.txt

2. Run a search:
   python main.py --keywords "python developer" --remote

3. View results in output/ directory

USAGE EXAMPLES
--------------
# Search for remote Python jobs
python main.py --keywords "python developer" --remote

# Search specific platforms  
python main.py --keywords "data scientist" --platforms indeed linkedin

# Filter by salary
python main.py --keywords "software engineer" --min-salary 100000

# Search with location
python main.py --keywords "web developer" --location "New York"

# Export to multiple formats
python main.py --keywords "devops" --output-format csv json excel

# Advanced filtering
python main.py --keywords "senior developer" --remote --job-type fulltime --min-salary 120000 --exclude "junior intern" --deduplicate

CONFIGURATION
-------------
Edit config.py or create .env file:
- USE_SELENIUM: Use browser automation (default: True)
- HEADLESS_MODE: Run browser hidden (default: True)
- REQUEST_DELAY: Delay between requests in seconds (default: 2)
- MAX_PAGES: Maximum pages per platform (default: 5)

KEY COMPONENTS
--------------
1. Base Scraper (base_scraper.py)
   - Abstract class defining scraper interface
   - Common functionality for all scrapers
   - Selenium and requests support

2. Platform Scrapers
   - Each platform has dedicated scraper
   - Implements parse_job_card() and build_search_url()
   - Handles platform-specific HTML structure

3. Filters (filters.py)
   - JobFilter class with static methods
   - Supports multiple filter criteria
   - Deduplication and sorting

4. Export (export.py)
   - DataExporter class
   - Multiple format support
   - Summary statistics
   - Beautiful table display

5. Main Application (main.py)
   - JobScraperApp class
   - CLI argument parsing
   - Orchestrates scraping and filtering
   - Rich console output

EXTENDING THE TOOL
------------------
To add a new job platform:

1. Create new scraper in scrapers/ directory:
   class NewPlatformScraper(JobScraper):
       def build_search_url(self, filters): ...
       def scrape_jobs(self, filters): ...
       def parse_job_card(self, card): ...

2. Add to scrapers/__init__.py:
   from scrapers.newplatform_scraper import NewPlatformScraper

3. Register in main.py:
   self.scrapers = {
       'newplatform': NewPlatformScraper(),
       ...
   }

4. Update config.py PLATFORMS list

DEPENDENCIES
------------
- requests: HTTP requests
- beautifulsoup4: HTML parsing
- selenium: Browser automation
- pandas: Data manipulation
- python-dotenv: Environment variables
- lxml: XML/HTML parser
- webdriver-manager: ChromeDriver management
- rich: Beautiful console output
- openpyxl: Excel export

NOTES
-----
- Some platforms may block automated scraping
- Use appropriate delays to be respectful
- LinkedIn/Glassdoor have stricter measures
- Results depend on publicly available listings
- For educational purposes only

TROUBLESHOOTING
---------------
1. ChromeDriver issues:
   - Ensure Chrome browser is installed
   - Tool auto-downloads ChromeDriver

2. No results:
   - Use broader search terms
   - Reduce filters
   - Check platform accessibility

3. Slow performance:
   - Reduce --max-pages
   - Use fewer platforms
   - Disable Selenium where possible

AUTHOR
------
Created as a comprehensive job search automation tool.
"""

print(__doc__)
