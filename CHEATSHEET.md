# Job Scraper - Quick Command Reference

## 🚀 Most Common Commands

### 1. AI Job Matching (NEW!)
```bash
# FASTEST: Parse your resume (auto-setup in 30 seconds!)
python main.py --parse-resume "my_resume.pdf"

# Or manual setup
python main.py --ai-setup

# Get AI recommendations
python main.py --ai-recommend

# High-quality matches only (80%+)
python main.py --ai-recommend --min-score 80

# Analyze job market skills
python main.py --ai-analyze

# Get learning suggestions
python main.py --ai-suggest
```

### 2. Basic Job Scraping
```bash
# Remote Python jobs
python main.py "python developer" --remote

# Specific platforms
python main.py "software engineer" --platforms indeed linkedin

# With salary filter
python main.py "data scientist" --min-salary 100000 --remote

# Multiple platforms
python main.py "devops" --platforms indeed linkedin glassdoor remoteok
```

### 3. Database Operations
```bash
# Show database stats
python main.py --db-stats

# Show only new jobs
python main.py "developer" --show-new-only

# Search existing jobs
python main.py --search-db "python remote"

# Cleanup old jobs (30+ days)
python main.py --cleanup-old 30
```

### 4. Notifications
```bash
# Email notification for new jobs
python main.py "engineer" --remote --email-notify

# Webhook to Slack/Discord
python main.py "developer" --webhook-notify

# Daily digest email
python main.py --send-digest

# Both email and webhook
python main.py "python" --remote --email-notify --webhook-notify
```

### 5. Web Dashboard
```bash
# Start dashboard
python app.py

# Then open browser to:
http://localhost:5000
```

### 6. Export Results
```bash
# Export to CSV
python main.py "developer" --output-format csv

# Export to JSON
python main.py "engineer" --output-format json

# Export to Excel
python main.py "python" --output-format excel

# Multiple formats
python main.py "data" --output-format csv json excel
```

## ⚡ Power User Combos

### Daily Job Hunt
```bash
# Scrape + Show new + AI recommend + Email
python main.py "Python Developer" --remote --show-new-only --ai-recommend --min-score 75 --email-notify
```

### Complete Search
```bash
# All platforms + Database + AI + Export
python main.py "Full Stack" --remote --platforms indeed linkedin glassdoor --ai-recommend --export csv
```

### Market Research
```bash
# Broad scrape
python main.py "software engineer" --platforms indeed linkedin glassdoor

# Analyze demand
python main.py --ai-analyze

# Find learning path
python main.py --ai-suggest
```

## 📋 All Command Options

### Search Parameters
```bash
--keywords, -k          # Job keywords to search
--location, -l          # Job location
--remote, -r           # Remote jobs only
--job-type, -t         # fulltime, parttime, contract, internship
--min-salary           # Minimum yearly salary
--exclude, -e          # Keywords to exclude
```

### Platform Selection
```bash
--platforms, -p        # Choose platforms:
                       # indeed, linkedin, glassdoor, remoteok
                       # weworkremotely, monster, dice, simplyhired
                       # ziprecruiter, angellist
```

### Output Options
```bash
--output-format, -o    # csv, json, excel
--display, -d          # Number of jobs to display (default: 10)
--deduplicate          # Remove duplicate jobs
--sort-by              # platform, company, title, location
```

### Database Options
```bash
--use-database         # Save jobs to database (default: true)
--show-new-only        # Show only new jobs
--new-since-hours      # Hours for new jobs (default: 24)
--db-stats             # Show database statistics
--search-db            # Search database instead of scraping
--cleanup-old          # Remove jobs older than N days
```

### Notification Options
```bash
--email-notify         # Send email for new jobs
--email-to             # Email recipient
--webhook-notify       # Send Slack/Discord notification
--send-digest          # Send daily digest email
--digest-hours         # Hours to include in digest (default: 24)
```

### AI Matching Options (NEW!)
```bash
--parse-resume FILE    # Parse resume and auto-generate preferences
--ai-setup             # Interactive preferences setup
--ai-recommend         # Get AI recommendations
--ai-analyze           # Analyze skills demand
--ai-suggest           # Get skill learning suggestions
--min-score            # Minimum match score (0-100, default: 60)
```

### Scraping Options
```bash
--max-pages            # Maximum pages per platform
```

## 🎯 Example Workflows

### Workflow 1: Morning Routine
```bash
# Step 1: Check new jobs from last 12 hours
python main.py "Python Developer" --remote --show-new-only --new-since-hours 12

# Step 2: Get AI recommendations
python main.py --ai-recommend --min-score 70

# Step 3: Apply to top matches
# (Use web dashboard or exported CSV)
```

### Workflow 2: Weekly Market Check
```bash
# Monday: Broad scrape
python main.py "Software Engineer" --platforms indeed linkedin glassdoor

# Tuesday: Analyze trends
python main.py --ai-analyze

# Wednesday: Check skill gaps
python main.py --ai-suggest

# Thursday: Focused search
python main.py "Python Remote" --ai-recommend --min-score 75
```

### Workflow 3: Automated Daily Hunt
```bash
# Setup Windows Task Scheduler for 8 AM daily:
python main.py "Senior Developer" --remote --show-new-only --ai-recommend --min-score 75 --email-notify --webhook-notify
```

### Workflow 4: Multi-Role Search
```bash
# Morning: Backend roles
copy preferences_backend.json preferences.json
python main.py "Backend Developer" --ai-recommend

# Afternoon: Full-stack roles
copy preferences_fullstack.json preferences.json
python main.py "Full Stack" --ai-recommend

# Evening: Compare results
python main.py --db-stats
```

## 🌐 Web Dashboard Quick Reference

### Start Dashboard
```bash
python app.py
# Open http://localhost:5000
```

### Available Pages
- **Main Dashboard** - View all jobs
- **Statistics** - Job metrics
- **AI Recommendations** - Scored matches
- **Preferences** - Edit AI settings

### API Endpoints
```bash
# Jobs
GET  /api/jobs
GET  /api/jobs/<id>
POST /api/jobs/<id>/status
GET  /api/new-jobs

# Stats
GET  /api/stats
GET  /api/platforms

# Export
GET  /api/export

# AI (NEW!)
GET  /api/ai/recommendations
GET  /api/ai/preferences
POST /api/ai/preferences
GET  /api/ai/analyze-skills
GET  /api/ai/suggest-skills
GET  /api/ai/score-job/<id>

# Notifications
POST /api/notify

# History
GET  /api/jobs/<id>/history
GET  /api/search-history

# Cleanup
POST /api/cleanup
```

## 🔧 Configuration Files

### .env (Email & Webhooks)
```env
# Email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@email.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@email.com

# Webhook settings
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### preferences.json (AI Matching)
```json
{
  "required_skills": ["python", "django"],
  "preferred_skills": ["docker", "aws"],
  "excluded_keywords": ["junior"],
  "min_salary": 100000,
  "remote_only": true,
  "job_types": ["fulltime"],
  "preferred_companies": [],
  "excluded_companies": []
}
```

### config.py (General Settings)
```python
MAX_PAGES = 3
REQUEST_DELAY = 2
MAX_RETRIES = 3
TIMEOUT = 30
```

## 📚 Documentation Files

- **README.md** - Project overview
- **QUICKSTART.md** - Quick setup guide
- **INSTALLATION.md** - Detailed installation
- **DATABASE_GUIDE.md** - Database features
- **NOTIFICATIONS_GUIDE.md** - Notification setup
- **DASHBOARD_GUIDE.md** - Web dashboard docs
- **AI_MATCHING_GUIDE.md** - AI matching complete guide
- **AI_EXAMPLES.md** - AI usage examples
- **BROWSER_AUTOMATION.md** - Selenium/Playwright guide
- **PROGRESS_UPDATE.md** - Feature status

## 🐛 Troubleshooting

### Problem: Python not found
```bash
# Install Python 3.8+ from python.org
# Or use Microsoft Store on Windows
```

### Problem: Module not found
```bash
pip install -r requirements.txt
```

### Problem: No jobs found
```bash
# Try broader search
python main.py "developer"

# Try more platforms
python main.py "developer" --platforms indeed linkedin glassdoor remoteok

# Increase pages
python main.py "developer" --max-pages 5
```

### Problem: AI giving no recommendations
```bash
# Lower score threshold
python main.py --ai-recommend --min-score 30

# Check preferences
cat preferences.json

# Re-run setup
python main.py --ai-setup
```

### Problem: Email not sending
```bash
# Check .env file exists and has correct settings
# For Gmail: Use app-specific password
# Test with: python main.py --send-digest
```

### Problem: Web dashboard won't start
```bash
# Install Flask
pip install flask

# Check port 5000 is free
# Try different port: Edit app.py, change port=5000 to port=8080
```

## 🎓 Learn More

### Test AI System
```bash
python test_ai.py
```

### View Examples
```bash
# Python API examples
python examples.py

# Playwright examples
python examples_playwright.py

# Database CLI
python db_manager.py --help
```

### Get Help
```bash
# Main application help
python main.py --help

# Database manager help
python db_manager.py --help

# Check requirements
cat requirements.txt

# View configuration
cat config.py
```

## 📊 Feature Status

✅ Multi-platform scraping (10 platforms)
✅ Advanced filtering (remote, salary, location)
✅ Database integration (SQLite)
✅ Application tracking
✅ Email notifications (Gmail, Outlook, Yahoo)
✅ Webhook notifications (Slack, Discord)
✅ Web dashboard (Flask + REST API)
✅ AI job matching (ML-powered scoring)
✅ Skills analysis
✅ Export (CSV, JSON, Excel)
✅ Comprehensive documentation

## 🚀 Quick Start for New Users

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. AUTO-SETUP: Parse your resume (FASTEST!)
python main.py --parse-resume "your_resume.pdf"
# Supports PDF, DOCX, TXT formats
# Extracts skills, experience, salary expectations automatically

# Or manual setup:
python main.py --ai-setup

# 3. Scrape some jobs
python main.py "Python Developer" --remote --platforms indeed linkedin

# 4. Get AI recommendations
python main.py --ai-recommend

# 5. (Optional) Start web dashboard
python app.py
```

## 💡 Pro Tips

1. **Use AI Setup First**: Run `--ai-setup` before first scraping
2. **Scrape Regularly**: More data = Better AI recommendations
3. **Adjust Threshold**: Start with `--min-score 60`, increase as needed
4. **Check Market Trends**: Run `--ai-analyze` monthly
5. **Update Skills**: Add new skills to preferences as you learn
6. **Use Dashboard**: Visual interface is easier than CLI
7. **Automate**: Setup scheduled tasks for daily scraping
8. **Export Results**: Keep CSV backups of top matches
9. **Monitor Stats**: Check `--db-stats` to track progress
10. **Read Docs**: Full guides have advanced tips

---

**Need more help?** Check the documentation files or run commands with `--help`

**Happy job hunting! 🎯🚀**
