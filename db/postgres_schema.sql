-- Postgres schema for Scrapper MVP (UI on Vercel + External Worker)
-- Tables: jobs, leads, outreach_logs, templates, crawl_logs
-- Conventions:
-- - Timestamps are timestamptz (UTC)
-- - Text fields are lowercased for search where practical
-- - jsonb used for flexible enrichment payloads / variables
-- - Use a text primary key for jobs.id (canonical URL hash) for deterministic dedupe

CREATE EXTENSION IF NOT EXISTS pg_trgm; -- optional (fast ILIKE/search)

-- =====================
-- jobs
-- =====================
-- id: canonical URL hash (sha256 hex) or any deterministic hash
-- posted_at: the date/time the job was posted (if known)
-- score: computed lead score (0-100)
-- snapshot_url: blob/object storage URL for HTML snapshot

CREATE TABLE IF NOT EXISTS jobs (
    id              text PRIMARY KEY,         -- canonical URL hash (deterministic)
    url             text NOT NULL,            -- canonical URL
    title           text NOT NULL,
    company         text,
    location        text,
    posted_at       timestamptz,              -- NULL if unknown
    budget          text,                     -- freeform budget/salary text
    description     text,
    source_listing  text,                     -- listing page URL discovered from
    snapshot_url    text,                     -- blob storage URL for HTML snapshot
    crawled_at      timestamptz,              -- when we crawled the job page
    score           integer,                  -- 0..100
    platform        text,                     -- optional normalized platform label
    extra           jsonb DEFAULT '{}'::jsonb,-- optional enrichment payload
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- Speed up dedupe and queries
CREATE UNIQUE INDEX IF NOT EXISTS ux_jobs_url ON jobs (url);
CREATE INDEX IF NOT EXISTS ix_jobs_company_title ON jobs (lower(company), lower(title));
CREATE INDEX IF NOT EXISTS ix_jobs_posted_at ON jobs (posted_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS ix_jobs_source_listing ON jobs (source_listing);
CREATE INDEX IF NOT EXISTS ix_jobs_score ON jobs (score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS ix_jobs_title_trgm ON jobs USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_jobs_company_trgm ON jobs USING gin (company gin_trgm_ops);

-- =====================
-- leads
-- =====================
-- A lead is derived from a job (1..N). Emails may be verified or guessed.

CREATE TABLE IF NOT EXISTS leads (
    id                  bigserial PRIMARY KEY,
    job_id              text REFERENCES jobs(id) ON DELETE CASCADE,
    company_name        text,
    contact_name        text,
    email               text,                  -- chosen primary email (if any)
    email_type          text,                  -- 'verified' | 'guessed' | NULL
    email_confidence    smallint,              -- 0..100
    phone               text,
    linkedin_url        text,
    contact_page_url    text,
    enrichment_status   text,                  -- pending|complete|failed
    enrichment_payload  jsonb,                 -- raw details from enrichment step(s)
    score               integer,               -- 0..100 (lead score)
    status              text,                  -- New|In Progress|Contacted|Qualified|Unqualified
    last_contacted_at   timestamptz,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_leads_job_id ON leads (job_id);
CREATE INDEX IF NOT EXISTS ix_leads_score ON leads (score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (status);
CREATE INDEX IF NOT EXISTS ix_leads_email ON leads (lower(email));

-- =====================
-- templates
-- =====================
-- Store outreach templates and variable hints

CREATE TABLE IF NOT EXISTS templates (
    id          bigserial PRIMARY KEY,
    name        text UNIQUE NOT NULL,
    subject     text NOT NULL,
    body        text NOT NULL,
    variables   jsonb DEFAULT '[]'::jsonb, -- e.g., ["company","title","tech_stack"]
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- =====================
-- outreach_logs
-- =====================
-- Tracks outreach events related to a lead

CREATE TABLE IF NOT EXISTS outreach_logs (
    id                bigserial PRIMARY KEY,
    lead_id           bigint REFERENCES leads(id) ON DELETE CASCADE,
    channel           text,                  -- email|slack|discord|phone|linkedin
    template_id       bigint REFERENCES templates(id),
    message_preview   text,
    sent_at           timestamptz,
    delivered         boolean,
    response_summary  text,
    status            text,                  -- queued|sent|failed|responded
    metadata          jsonb,                 -- provider message id, error codes, etc
    created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_outreach_lead ON outreach_logs (lead_id);
CREATE INDEX IF NOT EXISTS ix_outreach_sent_at ON outreach_logs (sent_at DESC NULLS LAST);

-- =====================
-- crawl_logs
-- =====================
-- Per-listing crawl bookkeeping

CREATE TABLE IF NOT EXISTS crawl_logs (
    id           bigserial PRIMARY KEY,
    listing_url  text NOT NULL,
    domain       text,
    start_time   timestamptz,
    end_time     timestamptz,
    status       text,           -- ok|error
    num_found    integer,
    errors       text,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_crawl_logs_time ON crawl_logs (coalesce(end_time, start_time) DESC);
CREATE INDEX IF NOT EXISTS ix_crawl_logs_domain ON crawl_logs (domain);
