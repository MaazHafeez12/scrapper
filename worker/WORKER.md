# Scraper Worker (Runbook)

A small Flask service that receives signed crawl/enqueue requests and runs heavy work outside Vercel (crawling, enrichment, scheduled outreach). This runbook covers how to deploy and operate it.

## What the worker must have

- Runtime: Either
  - Node.js + Playwright (recommended for JS-heavy sites), or
  - Python + Selenium/Playwright (current worker code is Python Flask; crawling logic can be added here).
- Headless browser available
  - Playwright bundles browsers; `npx playwright install --with-deps` handles it.
  - Selenium needs a Chromium/Chrome + chromedriver pair.
- Scheduler
  - External cron (systemd timer or crontab), or
  - Internal endpoint + platform scheduler hitting `/worker/outreach-tick` periodically.
- Environment variables configured (see below).

## Endpoints

- POST `/worker/crawl`
  - Verifies `X-Webhook-Signature` (HMAC-SHA256 of raw body) using `WORKER_WEBHOOK_SECRET`.
  - Payload:
    ```json
    {
      "urls": ["https://example.com/jobs"],
      "keywords": ["python", "remote"],
      "maxLinksPerListing": 25,
      "minScore": 0,
      "options": { "respectRobots": true, "snapshots": false }
    }
    ```
  - Returns `202 Accepted`. Either forwards to `BACKEND_CRAWL_URL` (MVP) or performs native crawling when implemented.

- POST or GET `/worker/outreach-tick`
  - Processes due scheduled outreach emails (queued in DB), enforcing per-day and per-domain caps.

- GET `/worker/health`
  - Simple health check endpoint returning `{ ok: true }`.

## Environment variables

Minimum:

- `WORKER_WEBHOOK_SECRET` (aka `WORKER_SECRET`): Shared HMAC secret with Vercel `/api/enqueue`.
- `DATABASE_URL`: Managed Postgres connection used by the worker to read/write jobs/outreach logs.
- Email transport: one of
  - `SENDGRID_API_KEY`, or
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`.

Optional/Advanced:

- `STORAGE_BUCKET_URL` and/or credentials (e.g., `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET`) for snapshots.
- `ENRICHMENT_API_KEY` (aka `ENRICHMENT_KEY`) for contact/domain enrichment providers.
- `OUTREACH_DAILY_CAP` (default 20) and `OUTREACH_PER_DOMAIN_CAP` (default 5).
- `BACKEND_CRAWL_URL` if you proxy to an existing backend crawl endpoint.
- `PORT` (default 8080).

## Deploy options

### Option A: Docker service (recommended)

Use the repo Dockerfile or a slim variant. To run the worker entrypoint, override the command:

```bash
docker build -t scrapper-worker .
docker run -d \
  -p 8080:8080 \
  --restart=always \
  -e WORKER_WEBHOOK_SECRET=... \
  -e DATABASE_URL=... \
  -e SENDGRID_API_KEY=... \
  --name worker scrapper-worker python worker/app.py
```

If using Playwright Node worker instead, base on `mcr.microsoft.com/playwright:focal` and run `npx playwright install --with-deps` during build.

### Option B: systemd (Ubuntu)

1) Install dependencies (Python 3.11+, pip) and project requirements:

```bash
cd /opt/scrapper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Create a systemd unit `/etc/systemd/system/scrapper-worker.service`:

```ini
[Unit]
Description=Scrapper Worker
After=network.target

[Service]
WorkingDirectory=/opt/scrapper
Environment=PYTHONUNBUFFERED=1
Environment=WORKER_WEBHOOK_SECRET=YOUR_SECRET
Environment=DATABASE_URL=postgres://...
Environment=SENDGRID_API_KEY=...
ExecStart=/opt/scrapper/.venv/bin/python worker/app.py
Restart=always
RestartSec=5
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

3) Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable scrapper-worker
sudo systemctl start scrapper-worker
```

### Scheduling (cron)

You can process scheduled emails by calling `/worker/outreach-tick` periodically. On a single host, add a cron:

```bash
*/5 * * * * curl -fsS http://127.0.0.1:8080/worker/outreach-tick > /dev/null
```

If you need authenticated scheduling, keep the worker private and call it via localhost; or expose a separate authenticated scheduler endpoint.

## Operational tasks

1) Install/verify headless browser
   - Playwright: `npx playwright install --with-deps` (Node) or `pip install playwright && playwright install` (Python Playwright).
   - Selenium: ensure `chromium` and `chromedriver` are installed and compatible.

2) Run HTTP listener
   - `python worker/app.py` (Flask) or your Node server if you go with Playwright Node.js.

3) Schedule tasks
   - Use cron or your platform’s scheduler to hit `/worker/outreach-tick`.

4) Monitor logs & health
   - `docker logs -f worker` or `journalctl -u scrapper-worker -f`.
   - Health: `GET /worker/health`.

5) Resource sizing
   - Headless Chromium typically needs ~300–500MB RAM per browser. For small scale, a 512MB–1GB instance is okay; increase CPU/RAM as concurrency grows.

6) Secure the webhook
   - Keep `WORKER_WEBHOOK_SECRET` strong. Vercel’s `/api/enqueue` signs the raw JSON body; the worker verifies it before accepting.
   - Optionally restrict source IPs with a firewall.

## Cloud platforms

- Render/Fly/Cloud Run: use their standard Docker flows. For Playwright, prefer images that include browsers (Managed Playwright). For Python/Selenium, ensure Chromium is available in the image.

## Small scale guidance

A single $5–$10/month VM/container is sufficient for light scraping and scheduled outreach. Start single-process, then scale out by:

- Increasing instance size when CPU/RAM saturates.
- Running multiple workers behind a load balancer (ensure per-domain crawl politeness and de-duplication logic).
- Moving snapshots to object storage (S3/Vercel Blob) and using Postgres for coordination.

## Quick validation checklist

- `GET /worker/health` returns ok.
- Signed `POST /worker/crawl` from Vercel → 202 Accepted.
- `/worker/outreach-tick` processes scheduled rows and respects caps (OUTREACH_DAILY_CAP, OUTREACH_PER_DOMAIN_CAP).
- Logs and restarts configured (Docker restart=always or systemd Restart=always).
