# Manual QA Plan (MVP)

This plan validates the crawler and dashboards end-to-end with a focus on accuracy (extraction success) and safety (no crashes, resilient errors).

## Scope
- Crawl by pasted listing URLs (static and JS-heavy) and verify extraction into Results view and CSV export.
- Validate dedupe (URL canonical and title+company+date fallback) prevents duplicates on repeat runs.
- Measure extraction success rate and false positives over a small but diverse set of sources.

## Environments
- Local dev: single process Flask or Gunicorn `-w 1`.
- Staging/Prod: same build with Nginx reverse proxy; DB_PATH pointing to a writable directory.

## Test data (10 diverse targets)
1. Static HTML job board page (e.g., WWR category page).
2. Another static board (e.g., Arbeitnow category/list JSON or HTML entry page).
3. RSS-based feed (e.g., NoDesk RSS).
4. A company careers listing page (static server-rendered) with multiple links.
5. A marketplace listing page (e.g., Upwork-like; static sample page if available).
6. JS-heavy board (Remotive or a sample site) driven by client-side rendering.
7. A listing with query parameters in job links (tests canonical dedupe).
8. A listing containing mixed links (non-job links, anchor links, relative links).
9. A listing with inconsistent HTML structure (tests parse robustness).
10. A listing with repeated jobs across pages (tests title+company+date dedupe on re-run).

Note: For JS-heavy sites in the MVP, rely on the HTTP crawler where content is server-delivered. For pure client-rendered content, use the Selenium worker locally and keep the server endpoint disabled.

## Steps
1. Dashboard sanity
   - Open `/dashboard` and submit a live scrape with `remote_only` on; confirm multiple platforms in breakdown.
2. Admin endpoints
   - Use admin token to fetch `/api/admin/summary` and `/api/admin/crawl-logs`; confirm no errors.
3. Crawl runs
   - POST `/api/crawl-urls` with 2–3 URLs at a time; set `max_links_per_listing` to 10.
   - Verify 2xx response, and that `created+updated` matches expectations.
   - Re-run the same crawl and confirm `updated` increases and `created` does not (URL or title+company+date dedupe).
4. Results view
   - Visit `/results` and filter by source domain, toggle `has budget`, apply `min score` (e.g., 50) and sort by score desc.
   - Verify counts and sample rows contain expected fields (Title, Company, Location, URL, Posted At, Crawled At, Score).
5. CSV export
   - `/api/export-jobs?crawled_only=1&min_score=50` and download; open CSV and verify columns and row counts match the filter.
6. Error handling
   - Include one invalid/404 listing URL and confirm the run completes; crawl logs record an error entry.
7. Selenium worker (local only)
   - Run `python -m crawler.selenium_crawler --keywords 'python, remote' --max-pages 1` and confirm rows are inserted with `source_listing` and `crawled_at`.

## Metrics to capture
- Extraction success rate: jobs found / attempted links per source.
- False positives: count of non-job pages captured (should be minimal; spot-check by URL patterns and titles).
- Dedupe effectiveness: repeat crawl `created` should be ~0 while `updated` increments.
- Performance: time to crawl 2–3 listings with `max_links_per_listing=10` on a single small VM.

## Acceptance
- Runs complete without crashes, errors are logged.
- Results visible in `/results` with filter/sort working, and export usable.
- Dedupe works across crawls.
- Score filter and sorting impact results as expected.

## Additional acceptance (Vercel + Worker + Outreach)

- App deployed on Vercel triggers the external Worker and shows new results:
   - POST `/api/enqueue` accepts listing URLs and keywords; Worker receives HMAC-signed request and writes jobs to DB; UI reflects new jobs/leads.
- Dedupe prevents the same URL from repeating across crawls (canonical URL hash and title+company+date signature).
- Extraction quality: at least 50% of a 10-site test sample produces both a title and a description (measured on static sample pages and/or live sites where permitted).
- Outreach send flow works:
   - From the Leads UI, sending email via `/api/send` (or `/api/outreach/send`) records an entry in `outreach_logs` with metadata (to_email, subject, status, transport).
   - Provider webhooks (SendGrid/Mailgun) update delivery/open/bounce status.
