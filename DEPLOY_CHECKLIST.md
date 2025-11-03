# Deployment Checklist (MVP)

Target: Small VPS (Ubuntu), single worker, SQLite persistence.

## 1) System prep
- Create non-root user for the app (optional but recommended)
- Open firewall for 80/443 and SSH

## 2) Install Chrome/Chromium
- Google Chrome (recommended) or Chromium; verify `--version`

## 3) Python venv and dependencies
- `python3 -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- Optional local Selenium worker: `pip install undetected-chromedriver webdriver-manager`

## 4) Environment
- `SECRET_KEY` (required)
- `DB_PATH=/var/lib/scrapper/jobs.db` (writable dir)
- Admin protection (choose one):
  - `ADMIN_TOKEN=...`
  - or `ADMIN_USER=...` and `ADMIN_PASS=...`
- Keep `ENABLE_SELENIUM=0` in API host (worker separate)

## 5) Gunicorn service
- One worker: `gunicorn -w 1 -b 127.0.0.1:8000 api.index:app`
- Create a systemd unit `scrapper.service` and enable it

## 6) Nginx reverse proxy
- Proxy to `127.0.0.1:8000`, set `proxy_read_timeout 300;`
- Add TLS via certbot (recommended)

## 7) Backups for SQLite
- Nightly copy of DB to `/var/backups/scrapper`, keep 14 days

## 8) Smoke checks
- `GET /api/admin/summary` with admin token
- POST `/api/crawl-urls` small run, then `GET /api/crawl-results`

## 9) Notes
- Synchronous crawl blocks one worker; keep `-w 1`
- For JS-heavy sources, run Selenium worker separately (see `CRAWLER.md`)
