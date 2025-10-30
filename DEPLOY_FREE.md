# Zero-cost ways to share your Job Scraper

This guide shows practical, free ways to let others test your app without paying for hosting.

Important notes:
- Scraping with headless browsers is often blocked on free hosts and may violate their terms or target sites’ ToS. The tunnel option keeps scraping on your machine where it already works.
- SQLite and schedulers also don’t fit most free serverless platforms.

## Option A: Instant public link via Cloudflare Tunnel (recommended)

Pros: Zero setup, free, no account required, works with your current Windows setup and scrapers.
Cons: URL is temporary; it stays up while your terminal is open.

Steps (Windows):
1. Start your app with a public tunnel:
   - Double-click `share_public.bat` (or run it from PowerShell). It will:
     - Start the Flask app on http://127.0.0.1:5000
     - Download `cloudflared.exe` if missing
     - Open a public URL like `https://<random>.trycloudflare.com` and print it in the console
2. Share the printed `trycloudflare.com` URL with testers. When you close the tunnel, the URL stops working.

Optional: If you have a Cloudflare account and a domain, you can create a named tunnel for a stable subdomain. See: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps

## Option B: GitHub Codespaces (free quota)

Pros: Click-and-share a public port; runs in the cloud; OK for light demos.
Cons: Limited free hours; running Playwright/Chrome can be constrained and slower; sleeping when inactive.

Steps:
1. Push your repo to GitHub (private is fine if you add testers as collaborators).
2. Open the repo in GitHub, click Code ➜ Codespaces ➜ Create codespace.
3. In the Codespaces terminal:
   - Create venv and install requirements
   - Run the Flask app (e.g., `python app.py`)
4. Use the “Ports” panel to make port 5000 Public. Share the generated URL.

If you need Playwright in Codespaces, install the browsers first:
```
python -m pip install playwright
python -m playwright install chromium
```

Note: Not all scraping targets will allow cloud IPs; Glassdoor especially may block.

## Option C: Free hosting caveats (Render, Railway, Fly.io)

- They can host the Flask dashboard, but browser-based scrapers (Selenium/Playwright) are unreliable or disallowed on free tiers.
- Schedulers/background jobs typically require a separate paid worker.
- If you only want a read-only dashboard backed by a prebuilt database (no scrapers), these can work. You’d need to:
  - Remove/disable scraping endpoints and scheduler in `app.py`
  - Bundle a snapshot DB (e.g., `output/jobs.db`) into the deploy image
  - Use `gunicorn` to serve Flask and a simple Dockerfile

## Which should I choose?
- Want the fastest, fully functional demo with current scrapers? Use Option A (Cloudflare Tunnel).
- Want a cloud environment with a shareable URL and can accept a more limited demo? Try Option B (Codespaces).

## Quick troubleshooting
- If the public page loads but API calls fail, ensure the app is running on port 5000 and that your tunnel points to `http://localhost:5000`.
- For Cloudflare Tunnel, keep the tunnel terminal open; when it closes, the URL stops working.
- If Glassdoor returns 0 jobs via cloud IPs, provide a residential proxy (`PROXY_URL` in `.env`) and retry using the Playwright stealth backend.
