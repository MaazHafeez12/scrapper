# Postgres schema

This directory contains a production-ready Postgres schema for Scrapper when you move beyond the local SQLite MVP.

- jobs: canonical job postings (id is a deterministic hash of the canonical URL)
- leads: contacts and guesses derived from jobs (email type/confidence + enrichment payload)
- templates: outreach templates with variables
- outreach_logs: messages sent and responses per lead
- crawl_logs: per-listing crawl bookkeeping

See `postgres_schema.sql` for full DDL including indexes.

## Mapping from current SQLite

The current SQLite `jobs` table maps to Postgres `jobs` as follows:
- jobs.id (pg) ⇄ canonical URL hash (compute where you insert)
- jobs.url (pg) ⇄ jobs.url (sqlite)
- jobs.title/company/location/description (pg) ⇄ same fields in sqlite
- jobs.posted_at (pg) ⇄ sqlite.date_posted (string). Convert to timestamptz.
- jobs.source_listing/crawled_at/score (pg) ⇄ sqlite.source_listing/crawled_at/lead_score
- jobs.snapshot_url (pg): new field for blob/object storage URL
- jobs.platform/extra (pg): maps to sqlite.platform; `extra` is new jsonb for enrichment

SQLite’s `business_leads` maps to Postgres `leads` with richer fields:
- leads.email_type: 'verified'|'guessed'
- leads.email_confidence: 0..100
- leads.enrichment_payload: jsonb per-lead details

`crawl_logs` exists in both; Postgres version has timestamptz and proper indexes.

## Usage

- Apply this schema to your Postgres database (Supabase/Neon/etc.):

```sql
\i db/postgres_schema.sql
```

- Point your Worker at Postgres via `DATABASE_URL` and insert rows per table. For snapshots, write HTML to blob storage and store the URL in `jobs.snapshot_url`.

## Notes

- Indexes include trigram for title/company to keep flexible search snappy.
- If you prefer UUIDs, replace `jobs.id text` with `uuid DEFAULT gen_random_uuid()` and keep the canonical hash in a separate column with a unique index.
- For strict dedupe, keep `UNIQUE (url)` and optionally a unique index on `(lower(title), lower(company), posted_at)` if your data source quality is high.
