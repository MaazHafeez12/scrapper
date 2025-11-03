# Production Architecture (MVP → Scale)

This repo contains a single-server Flask scraper with SQLite for local MVP. To run reliably in production and fit Vercel, use a split architecture:

- UI + Thin APIs (Vercel):
  - Next.js app for pages (Results, Admin) and SSR/ISR.
  - Thin API routes that only read (jobs/leads) and orchestrate (enqueue crawl); no heavy scraping.
  - Calls external Worker via signed webhook for crawls.
- Scraper Worker (Render/Fly/Cloud Run/VPS):
  - Long-running Python service that executes crawls with requests/BS4 or Playwright/Selenium.
  - Receives signed webhook from Vercel, runs crawl synchronously, writes to database (managed Postgres) and optional blob storage.
- Data plane:
  - Managed Postgres (Supabase/Neon) for jobs, leads, crawl_logs. Use read-only credentials from Vercel API routes.
  - Blob storage (S3/Supabase Storage) for HTML snapshots/attachments (optional).
- Email (optional):
  - SendGrid/Mailgun for alerts and outreach emails.
- Queue (optional):
  - Redis/Cloud Tasks/Upstash for retry and rate smoothing. MVP can go direct to Worker.

## Request Flow

1) User clicks "Crawl" in dashboard → Vercel API `/api/enqueue-crawl` → signed POST to `WORKER_WEBHOOK_URL`.
2) Worker verifies signature and runs crawl (rate-limited) → upserts jobs/leads into Postgres; stores snapshots in object storage if enabled.
3) UI fetches from thin readers (`/api/read-jobs`, `/api/read-leads`) with filters and pagination; CSV export uses the same readers.
4) Admin pages fetch app logs and crawl logs from Worker `/api/admin/*` or expose summaries via a worker endpoint.

## Environment Variables

App (UI/Thin APIs on Vercel):
- WORKER_WEBHOOK_URL: External Worker endpoint (eg. https://worker.example.com/worker/crawl)
- WORKER_WEBHOOK_SECRET: HMAC secret shared with Worker
- CONTACT_EMAIL: Contact email included in User-Agent and /api/policy
- SCRAPER_UA_NAME: Short UA name to identify your app
- SENDGRID_API_KEY, EMAIL_FROM: Optional email sending

Worker:
- WORKER_WEBHOOK_SECRET or WEBHOOK_SECRET: Same value as above to verify HMAC
- BACKEND_CRAWL_URL: If set to the Flask app `/api/crawl-urls`, the Worker proxies crawl to this backend (MVP path). If omitted, implement native crawl.
- DB connection: For production, prefer `DATABASE_URL` for Postgres and SSL mode per host.
- LOG_DIR, CONTACT_EMAIL, SCRAPER_UA_NAME, SMTP_*: Optional logging and alerting

## Migration Path

- Phase 0 (now): Single Flask app + SQLite, synchronous crawling. Included: admin auth, logging, ethics banners, alerts.
- Phase 1: Introduce Worker and use the existing Flask `/api/crawl-urls` as the heavy endpoint. Vercel only calls `/api/enqueue-crawl` → Worker → Flask crawl.
- Phase 2: Move DB to Postgres; switch thin readers to Postgres; keep Flask SQLite for local dev.
- Phase 3: Replace proxying in Worker with native crawling code running outside the Flask app; add Playwright/Selenium worker if needed.
- Phase 4: Add snapshots to blob storage and a small enrichment pipeline.

## Security and Compliance

- HMAC signatures for Worker webhooks (`X-Webhook-Signature`, SHA-256 over raw body).
- Admin routes protected with token/basic auth on both UI and Worker.
- Respect robots.txt and ToS; do not bypass auth/CAPTCHA; include contact email in UA and From.
- Sanitized inputs, clamps on limits, rate-limited fetch helper with per-domain politeness.
