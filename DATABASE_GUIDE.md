# Database Integration Guide

## Overview

The job scraper now includes a powerful SQLite database that automatically:
- **Tracks all scraped jobs** with deduplication
- **Monitors changes** to job postings over time
- **Records your actions** (applied, interested, rejected, etc.)
- **Maintains search history** for analytics
- **Enables smart filtering** to show only new jobs

## Quick Start

### 1. Basic Scraping with Database (Enabled by Default)

```bash
# Database is enabled by default - just scrape as usual
python main.py "Python Developer" --remote

# Jobs are automatically saved to jobs.db
# Duplicates are detected and updated instead of re-inserted
```

### 2. View Only New Jobs

```bash
# Show only jobs you haven't seen before
python main.py "Data Scientist" --remote --show-new-only

# New jobs from last 48 hours
python main.py "Frontend Developer" --show-new-only --new-since-hours 48
```

### 3. Database Statistics

```bash
# View comprehensive statistics
python main.py --db-stats
```

**Output includes:**
- Total jobs in database
- Remote vs non-remote breakdown
- New jobs in last 24h/7d/30d
- Jobs by status (new, applied, interested, rejected)
- Jobs by platform (Indeed, LinkedIn, etc.)

### 4. Search Saved Jobs

```bash
# Search database instead of scraping
python main.py --search-db "machine learning"

# Search with filters
python main.py --search-db "react" --remote --platforms Indeed LinkedIn

# Export search results
python main.py --search-db "python" --output-format csv json
```

## Database Manager CLI

A dedicated tool for advanced database operations:

### View Statistics

```bash
python db_manager.py stats
```

Shows beautiful formatted tables with:
- Overview panel (total, remote, new jobs)
- Jobs by status table
- Jobs by platform table

### Search Jobs

```bash
# Basic search
python db_manager.py search "senior developer"

# Search with filters
python db_manager.py search "python" --remote --platform Indeed

# Search and export
python db_manager.py search "data analyst" --export csv --display 20
```

### List New Jobs

```bash
# Jobs from last 24 hours (default)
python db_manager.py new

# Jobs from last 7 days
python db_manager.py new --hours 168

# Display more results
python db_manager.py new --display 50
```

### Update Job Status

Track your job applications directly in the database:

```bash
# Mark as applied
python db_manager.py update-status "https://indeed.com/job/123" applied --notes "Applied via website"

# Mark as interested
python db_manager.py update-status "https://linkedin.com/jobs/456" interested --notes "Good fit for skills"

# Mark as rejected
python db_manager.py update-status "https://glassdoor.com/job/789" rejected --notes "Position filled"

# Archive old job
python db_manager.py update-status "https://remote.co/job/999" archived
```

**Available statuses:**
- `new` - Just discovered (default)
- `applied` - You've applied
- `interested` - Want to apply
- `rejected` - Rejected or not interested
- `archived` - Archived for reference

### View Job History

See how jobs have changed over time:

```bash
python db_manager.py history "https://indeed.com/job/123"
```

Shows:
- When job was first discovered
- Changes to title, description, salary
- Status changes you made
- When job was last updated

### Export Database

```bash
# Export all jobs to CSV
python db_manager.py export --format csv

# Export remote jobs only
python db_manager.py export --format excel --remote

# Export specific platform
python db_manager.py export --format json --platform LinkedIn

# Export jobs by status
python db_manager.py export --format csv --status applied --output my_applications.csv
```

### Clean Up Old Jobs

```bash
# Delete jobs older than 90 days (default)
python db_manager.py cleanup

# Custom retention period
python db_manager.py cleanup --days 30

# Keep only last 2 weeks of data
python db_manager.py cleanup --days 14
```

## Database Schema

The database has 4 tables:

### 1. `jobs` - Main job listings
```sql
- id (primary key)
- title, company, location, description
- salary, url, platform
- remote (boolean)
- posted_date, scraped_at
- last_updated
- status (new/applied/interested/rejected/archived)
- notes (your personal notes)
- job_hash (for deduplication)
```

### 2. `job_history` - Change tracking
```sql
- id, job_id (foreign key)
- change_date
- field_name (what changed)
- old_value, new_value
```

### 3. `search_history` - Search analytics
```sql
- id, search_date
- keywords, location, remote_only
- platforms_searched
- results_count, new_jobs_count
```

### 4. `scraping_sessions` - Session tracking
```sql
- id, start_time, end_time
- platforms, keywords
- jobs_found, errors
- duration_seconds
```

## Advanced Features

### 1. Automatic Deduplication

Jobs are deduplicated based on:
- Title + Company + Location
- URL

If a job is scraped multiple times:
- First time: Added as NEW
- Subsequent times: Updated if changed
- Changes are logged in job_history

### 2. Smart Filtering

```bash
# Only show jobs added in last 6 hours
python main.py "DevOps" --show-new-only --new-since-hours 6

# Perfect for scheduled scraping (e.g., run every 6 hours)
# Shows only jobs discovered since last run
```

### 3. Change Tracking

The system automatically tracks:
- **Title changes** - Company renamed position
- **Salary changes** - Updated compensation
- **Description changes** - Modified requirements
- **Status changes** - Your application status

View with: `python db_manager.py history <job_url>`

### 4. Analytics

```bash
# See your application funnel
python db_manager.py stats

# Example output:
# Jobs by Status:
#   new: 245 (81.7%)
#   interested: 32 (10.7%)
#   applied: 18 (6.0%)
#   rejected: 5 (1.7%)
```

## Integration Examples

### Scheduled Scraping Script

```python
from main import JobScraperApp
from database import JobDatabase
import argparse

# Scrape every 6 hours, get only new jobs
args = argparse.Namespace(
    keywords="Python Developer",
    remote=True,
    use_database=True,
    show_new_only=True,
    new_since_hours=6,
    platforms=['indeed', 'linkedin', 'remoteok'],
    output_format=['csv']
)

app = JobScraperApp()
app.run(args)

# Send email notification for new jobs (coming in next update!)
```

### Application Tracking Workflow

```bash
# 1. Search for jobs
python main.py "Backend Engineer" --remote --use-database

# 2. Mark interesting ones
python db_manager.py update-status <url> interested --notes "Good tech stack"

# 3. After applying
python db_manager.py update-status <url> applied --notes "Applied 2024-01-15"

# 4. View your applications
python db_manager.py search "backend engineer" --status applied --export csv
```

### Daily Job Check

```bash
# Morning routine: Check new jobs from last 24h
python db_manager.py new --display 20

# Search saved jobs by keyword
python db_manager.py search "kubernetes" --remote

# Weekly cleanup
python db_manager.py cleanup --days 30
```

## Command Reference

### Main Scraper Commands

| Command | Description |
|---------|-------------|
| `--use-database` | Save to database (default: True) |
| `--show-new-only` | Show only new jobs |
| `--new-since-hours N` | Show jobs from last N hours |
| `--db-stats` | Show database statistics |
| `--search-db KEYWORDS` | Search database |
| `--cleanup-old N` | Delete jobs older than N days |

### Database Manager Commands

| Command | Description |
|---------|-------------|
| `stats` | Show statistics |
| `search KEYWORDS` | Search jobs |
| `new` | List new jobs |
| `update-status URL STATUS` | Update job status |
| `cleanup` | Remove old jobs |
| `export` | Export database |
| `history URL` | View job history |

## Tips & Tricks

### 1. Scheduled Scraping

Use Windows Task Scheduler or cron:

```bash
# Run every 6 hours, save only new jobs
python main.py "Software Engineer" --remote --show-new-only --new-since-hours 6
```

### 2. Multi-Stage Filtering

```bash
# Stage 1: Scrape and save all jobs
python main.py "Full Stack" --remote --use-database

# Stage 2: Search saved jobs with specific criteria
python db_manager.py search "react typescript" --export csv
```

### 3. Application Tracking

Keep notes on each application:

```bash
python db_manager.py update-status <url> applied \
  --notes "Applied via LinkedIn. Referral from John. Follow up on Jan 20."
```

### 4. Database Maintenance

Weekly cleanup routine:

```bash
# Keep 30 days of data
python db_manager.py cleanup --days 30

# View stats
python db_manager.py stats

# Export applications
python db_manager.py export --status applied --format excel
```

## Troubleshooting

### Database locked error
If you see "database is locked":
- Make sure only one scraper is running
- Close any database viewers (DB Browser for SQLite)
- The database uses context managers to prevent this

### Database file location
Default: `jobs.db` in the scraper directory

To use a different location, modify `database.py`:
```python
db = JobDatabase(db_path="custom/path/jobs.db")
```

### Reset database
To start fresh:
```bash
# Backup first!
cp jobs.db jobs.db.backup

# Delete
rm jobs.db

# Next run will create fresh database
python main.py "Python" --remote
```

## What's Next?

In the next update, we'll add:
- **Email notifications** for new jobs
- **Slack/Discord webhooks**
- **Web dashboard** to view jobs in browser
- **AI job matching** based on your preferences

Database integration is complete! 🎉
