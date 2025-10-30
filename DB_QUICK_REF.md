# Database Quick Reference

## Main Scraper Commands

### Basic Scraping (Database Auto-Enabled)
```bash
python main.py "Python Developer" --remote
```

### Show Only New Jobs
```bash
python main.py "Data Scientist" --show-new-only
python main.py "Frontend" --show-new-only --new-since-hours 48
```

### Database Statistics
```bash
python main.py --db-stats
```

### Search Database
```bash
python main.py --search-db "machine learning"
python main.py --search-db "react" --remote --platforms Indeed
```

### Cleanup
```bash
python main.py --cleanup-old 90
```

## Database Manager Commands

### Statistics
```bash
python db_manager.py stats
```

### Search
```bash
python db_manager.py search "python developer"
python db_manager.py search "senior" --remote --export csv
python db_manager.py search "backend" --platform LinkedIn --status interested
```

### List New Jobs
```bash
python db_manager.py new
python db_manager.py new --hours 168  # Last 7 days
```

### Update Job Status
```bash
python db_manager.py update-status "https://example.com/job/123" applied
python db_manager.py update-status "URL" interested --notes "Good match"
python db_manager.py update-status "URL" rejected --notes "Not interested"
```

Available statuses: `new`, `applied`, `interested`, `rejected`, `archived`

### Export Database
```bash
python db_manager.py export --format csv
python db_manager.py export --format excel --remote
python db_manager.py export --format json --status applied
```

### View History
```bash
python db_manager.py history "https://example.com/job/123"
```

### Cleanup
```bash
python db_manager.py cleanup --days 90
```

## Common Workflows

### Daily Job Check
```bash
# Check new jobs from last 24h
python db_manager.py new --display 20

# Or search for specific keywords
python db_manager.py search "kubernetes" --remote
```

### Application Tracking
```bash
# 1. Search and scrape
python main.py "Backend Engineer" --remote

# 2. Mark interesting jobs
python db_manager.py update-status <url> interested

# 3. After applying
python db_manager.py update-status <url> applied --notes "Applied 2024-01-15"

# 4. Export your applications
python db_manager.py export --status applied --format excel
```

### Scheduled Scraping
```bash
# Run every 6 hours, show only new jobs
python main.py "Software Engineer" --remote --show-new-only --new-since-hours 6
```

### Weekly Maintenance
```bash
# View stats
python db_manager.py stats

# Clean up old jobs
python db_manager.py cleanup --days 30

# Export all data
python db_manager.py export --format csv
```

## Database Location

Default: `jobs.db` in the scraper directory

## Tables

- `jobs` - All job listings
- `job_history` - Change tracking
- `search_history` - Search analytics
- `scraping_sessions` - Session tracking

## Tips

1. **Use --show-new-only for scheduled scraping** - Only see jobs you haven't seen before
2. **Track applications with update-status** - Never lose track of where you applied
3. **Export by status** - Create a spreadsheet of jobs you're interested in
4. **View history** - See how jobs change over time (salary updates, etc.)
5. **Regular cleanup** - Delete old jobs to keep database fast

## See Also

- [DATABASE_GUIDE.md](DATABASE_GUIDE.md) - Complete documentation
- [README.md](README.md) - Main project documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
