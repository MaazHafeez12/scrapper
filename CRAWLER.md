# Selenium Crawler (MVP)

This headless Chrome crawler complements the HTTP-based crawler and follows the MVP plan:

- Listing page fetch with a short wait for JS (1–3s)
- Extract anchors, normalize, and apply heuristics for job-like links
- Visit top N candidate job pages, wait ~1s, extract fields via fallbacks
- Dedupe by URL, and by title+company+date
- Compute a simple keyword score
- Be polite: robots.txt advisory, per-domain delay, max pages/domain, custom UA

Note: Do not run this in a serverless runtime like Vercel. Use it locally or as a separate worker service.

## Install

```powershell
# From the scrapper folder
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Selenium 4 will attempt to manage ChromeDriver automatically. Ensure Google Chrome is installed.

## Run

```powershell
# Provide URLs directly
python -m crawler.selenium_crawler --urls "https://example.com/jobs, https://another.com/careers" --keywords "python, react"

# Or pass a file with URLs (one per line)
python -m crawler.selenium_crawler --urls .\listing_urls.txt --keywords "python, react"
```

Options:
- `--override-robots`: Crawl even if robots.txt disallows (not recommended)
- `--wait-listing`: Seconds to wait on listing page (default 2.0)
- `--wait-job`: Seconds to wait on job page (default 1.0)
- `--max-candidates`: Top N job-like links per listing (default 15)
- `--per-domain-delay`: Seconds between requests per domain (default 2.0)
- `--max-pages-per-domain`: Cap per-domain pages across listing+job pages (default 30)

## Output and storage

- When a local SQLite DB is available (`business_leads.db`), results are saved into the existing `jobs` table with:
  - `url` (canonical), `title`, `company`, `location`, `date_posted`, `budget`, `description`
  - `source_listing`, `crawled_at`, `lead_score`
- Dedupe uses:
  - First: exact URL match
  - Then: title+company+date match
- Crawl logs are written to `crawl_logs` and visible in `/admin` under "Crawl Logs".

## Integration notes

- The dashboard already has an HTTP crawler suitable for serverless. This Selenium crawler is intended for local runs or a dedicated worker.
- If you want a button in the UI to trigger the Selenium worker, consider exposing a queue endpoint and a small worker service that polls for jobs.
