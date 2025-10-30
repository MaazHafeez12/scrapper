# AI-Powered Job Scraper 🤖🚀

A powerful multi-platform job scraper with **AI-powered matching, auto-apply automation, and smart recommendations**. Search for jobs across 10 platforms, get intelligent match scores, and automatically apply with one command!

> 🎉 **NEW!** Automated job applications with browser automation - apply to multiple jobs automatically!

## Features

✨ **Multi-Platform Support**
- Indeed
- LinkedIn
- Glassdoor
- RemoteOK
- WeWorkRemotely

🤖 **Advanced Browser Automation**
- **Selenium** - Industry standard, stable and reliable
- **Playwright** - Modern Puppeteer alternative for Python (faster!)
- Anti-detection measures
- Dynamic content loading
- Smart waiting and scrolling

🔍 **Advanced Filtering**
- Search by keywords
- Filter by location
- Remote jobs only
- Job type (full-time, part-time, contract, internship)
- Minimum salary requirements
- Exclude specific keywords
- Company filtering

📊 **Export Options**
- CSV format
- JSON format
- Excel format

💾 **Database Integration**
- SQLite database for job storage
- Automatic deduplication across scraping sessions
- Track job changes over time
- Monitor application status (applied, interested, rejected)
- Search history and analytics
- Show only new jobs since last run
- Comprehensive CLI for database management

📧 **Email & Webhook Notifications**
- Email alerts for new jobs
- Daily digest emails
- Slack webhook integration
- Discord webhook integration
- Status change notifications
- Application session summaries

🤖 **Auto-Apply Automation** (NEW!)
- Automatically apply to jobs with browser automation
- Auto-fill personal information and upload resume
- CAPTCHA detection and handling
- Dry-run mode for testing
- Apply to AI-recommended jobs only
- Platform compatibility (Indeed, RemoteOK, etc.)
- Safety features and application limits
- Beautiful HTML email templates
- Scheduled notifications support

🌐 **Web Dashboard** (NEW!)
- Visual interface in browser
- **Kanban board** for job pipeline management
- Drag & drop jobs between stages (New → Applied → Interview → Offer)
- Real-time statistics
- Interactive job filtering
- Status management with one click
- Export from dashboard
- Mobile-responsive design
- RESTful API backend

🎯 **Smart Features**
- Automatic deduplication
- Results sorting
- Summary statistics
- Beautiful console output

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. **(Optional) Install Playwright browsers** for Puppeteer-like automation:
```bash
python -m playwright install chromium
```

4. (Optional) Copy `.env.example` to `.env` and configure settings:
```bash
copy .env.example .env
```

## Usage

### Basic Examples

**Search for remote Python jobs:**
```bash
python main.py --keywords "python developer" --remote
```

**Search on specific platforms:**
```bash
python main.py --keywords "data scientist" --platforms indeed linkedin
```

**Search with salary filter:**
```bash
python main.py --keywords "software engineer" --min-salary 100000
```

**Search with location:**
```bash
python main.py --keywords "web developer" --location "New York"
```

**Export to multiple formats:**
```bash
python main.py --keywords "devops" --output-format csv json excel
```

### All Available Options

```
Options:
  --keywords, -k         Job keywords to search for
  --location, -l         Job location
  --remote, -r           Search for remote jobs only
  --job-type, -t         Type of job (fulltime, parttime, contract, internship)
  --min-salary           Minimum salary (yearly)
  --exclude, -e          Keywords to exclude from results
  
  --platforms, -p        Platforms to scrape (default: all)
                         Choices: indeed, linkedin, glassdoor, remoteok, weworkremotely
  
  --max-pages            Maximum pages to scrape per platform (default: 5)
  --output-format, -o    Output format(s) (default: csv)
                         Choices: csv, json, excel
  --display, -d          Number of jobs to display (default: 10)
  --deduplicate          Remove duplicate jobs
  --sort-by              Sort results by field
                         Choices: platform, company, title, location
```

### Advanced Examples

**Find remote senior developer positions, excluding certain keywords:**
```bash
python main.py --keywords "senior developer" --remote --exclude "junior intern" --min-salary 120000
```

**Search multiple platforms with custom page limit:**
```bash
python main.py --keywords "machine learning" --platforms indeed linkedin remoteok --max-pages 3
```

**Get full-time jobs in specific location with deduplication:**
```bash
python main.py --keywords "full stack" --location "San Francisco" --job-type fulltime --deduplicate --sort-by company
```

## Configuration

Edit `config.py` or create a `.env` file to customize:

- `USE_SELENIUM`: Use Selenium for browser automation (default: True)
- `USE_PLAYWRIGHT`: Use Playwright (Puppeteer alternative) (default: False)
- `HEADLESS_MODE`: Run browser in headless mode (default: True)
- `LOAD_IMAGES`: Load images (disable for faster scraping) (default: False)
- `REQUEST_DELAY`: Delay between requests in seconds (default: 2)
- `MAX_PAGES`: Maximum pages to scrape (default: 5)

### Browser Automation

**Selenium (Default):**
- Stable and mature
- Auto-installs ChromeDriver
- Great documentation

**Playwright (Puppeteer Alternative):**
- 30-50% faster than Selenium
- Better anti-detection
- Modern async API
- Requires: `python -m playwright install chromium`

See [BROWSER_AUTOMATION.md](BROWSER_AUTOMATION.md) for detailed guide.

## Database Features

The scraper includes a powerful SQLite database that automatically saves and tracks all jobs:

**Quick Start:**
```bash
# Scraping automatically saves to database
python main.py "Python Developer" --remote

# View only new jobs since last run
python main.py "Data Scientist" --show-new-only

# Show database statistics
python main.py --db-stats

# Search saved jobs
python main.py --search-db "machine learning"
```

**Database Manager CLI:**
```bash
# View statistics
python db_manager.py stats

# Search jobs
python db_manager.py search "senior engineer" --remote

# List new jobs from last 24h
python db_manager.py new

# Track applications
python db_manager.py update-status <job_url> applied --notes "Applied today"

# Export database
python db_manager.py export --format csv --remote

# Clean up old jobs
python db_manager.py cleanup --days 90
```

**Features:**
- ✅ Automatic deduplication across runs
- ✅ Track job changes over time
- ✅ Monitor application status
- ✅ Search history and analytics
- ✅ Show only new jobs
- ✅ Job change history
- ✅ Comprehensive CLI tools

📖 **See [DATABASE_GUIDE.md](DATABASE_GUIDE.md) for complete database documentation**

## Email & Webhook Notifications

Never miss a job opportunity! Get instant notifications:

**Email Notifications:**
```bash
# Email alert for new jobs
python main.py "Python Developer" --remote --email-notify

# Daily digest
python main.py --send-digest --email-to your@email.com

# Scheduled alerts (every 6 hours)
python main.py "Software Engineer" --show-new-only --new-since-hours 6 --email-notify
```

**Slack/Discord Webhooks:**
```bash
# Send to Slack
python main.py "Data Scientist" --remote --webhook-notify

# Send to both email and Slack
python main.py "Backend Engineer" --email-notify --webhook-notify
```

**Configuration (.env file):**
```bash
# Email (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@example.com

# Webhook (Slack/Discord)
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
WEBHOOK_TYPE=slack
```

**Features:**
- ✅ Beautiful HTML email templates
- ✅ Slack/Discord rich formatting
- ✅ Daily digest summaries
- ✅ Status change alerts
- ✅ Perfect for scheduled scraping
- ✅ Multi-channel notifications

📖 **See [NOTIFICATIONS_GUIDE.md](NOTIFICATIONS_GUIDE.md) for complete setup guide**

## Web Dashboard

Manage jobs visually in your web browser!

**Quick Start:**
```bash
# Install Flask
pip install flask

# Start dashboard
python app.py

# Open browser
http://localhost:5000
```

**Features:**
- 📊 Real-time statistics (total, remote, new, applied)
- 🔍 Advanced filtering (keywords, platform, status, remote)
- 📋 Beautiful job cards with quick actions
- ✓ One-click status updates (applied, interested, rejected)
- 📥 Export filtered jobs (CSV, JSON, Excel)
- 📱 Mobile-responsive design
- 🔄 Auto-refreshing stats
- 💡 Job details modal

**Screenshots:**
- Statistics dashboard with 4 key metrics
- Filter panel with keyword search
- Job cards with status badges
- Quick action buttons on each job
- Export options in multiple formats

**API Endpoints:**
- GET `/api/jobs` - Get jobs with filtering
- GET `/api/stats` - Get statistics
- POST `/api/jobs/<id>/status` - Update status
- GET `/api/export` - Export jobs
- GET `/api/new-jobs` - Get recent jobs
- ...and more!

📖 **See [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) for complete documentation**

## AI Job Matching

Get intelligent job recommendations powered by AI! 🤖

**Quick Start:**
```bash
# NEW! Parse your resume for instant setup (30 seconds!)
python main.py --parse-resume "my_resume.pdf"

# Or setup manually
python main.py --ai-setup

# Get recommendations
python main.py --ai-recommend

# Analyze skills demand
python main.py --ai-analyze

# Get skill suggestions
python main.py --ai-suggest
```

**Features:**
- 📄 **Resume Parser** - Auto-extract skills from your resume (NEW!)
- 🎯 **Smart Scoring** - Jobs rated 0-100% based on your preferences
- 🧠 **Machine Learning** - Learns from your feedback automatically
- 📊 **Skills Analysis** - See which skills are most in-demand
- 💡 **Learning Suggestions** - Know what skills to learn next
- ⚙️ **Customizable** - Configure weights, skills, preferences
- 🔄 **Automatic Updates** - Preferences improve over time

**Scoring Factors:**
- Required skills (40%) - Must-have technical skills
- Preferred skills (30%) - Nice-to-have bonuses
- Remote preference (15%) - Work location match
- Salary match (10%) - Meets minimum requirements
- Company preference (5%) - Preferred employers
- Penalties for excluded keywords/companies

**Example Output:**
```
🤖 AI Job Recommendations (min score: 60)

🌟 85.5% - Senior Python Developer
   Company: TechCorp
   Location: Remote
   Salary: $120,000 - $150,000
   ✓ Skills: python, django, aws, docker
   ✗ Missing: kubernetes

⭐ 72.3% - Full Stack Engineer
   Company: StartupCo
   ...
```

**Web Dashboard Integration:**
- View AI recommendations in browser
- Edit preferences visually
- See match score breakdown
- Export top matches

📖 **See [AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md) for complete AI guide**
📖 **See [RESUME_PARSER_GUIDE.md](RESUME_PARSER_GUIDE.md) for resume parsing guide**

## Auto-Apply Automation

Automatically apply to jobs using browser automation! 🤖

**Quick Start:**
```bash
# Setup template with your info
python main.py --auto-apply-setup

# Test with dry run
python main.py --auto-apply --dry-run --max-applications 2 --show-browser

# Apply to AI-recommended jobs
python main.py --auto-apply --ai-recommend --min-score 80 --max-applications 5

# Apply to new jobs from today
python main.py --auto-apply --show-new-only --max-applications 10
```

**Features:**
- 📝 **Auto-fill Forms** - Personal info, email, phone automatically filled
- 📎 **Upload Resume** - Automatically attach resume and cover letter
- 🎯 **Smart Targeting** - Combine with AI recommendations
- 🔒 **CAPTCHA Handling** - Detects and waits for manual solving
- 🧪 **Dry Run Mode** - Test without actually submitting
- ⚡ **Platform Support** - Works with Indeed, RemoteOK, and more
- 📊 **Track Applications** - Auto-updates database status
- 🔄 **Session Control** - Limits and delays for safety

**Safety Features:**
- Maximum applications per session (default: 10)
- Delay between applications (default: 10s)
- Confirmation before starting
- Detailed error reporting
- Platform compatibility checks

**Example Workflow:**
```bash
# 1. Scrape jobs
python main.py "Python Developer" --remote --platforms indeed remoteok

# 2. Get AI recommendations
python main.py --ai-recommend --min-score 75

# 3. Auto-apply to top matches
python main.py --auto-apply --ai-recommend --min-score 80 --max-applications 5 --email-notify
```

**Supported Platforms:**
- ✅ Indeed (Excellent - Quick Apply)
- ✅ RemoteOK (Excellent - Simple forms)
- ✅ SimplyHired (Good compatibility)
- ⚠️ LinkedIn (Limited - Easy Apply only)
- ⚠️ Glassdoor (Limited - redirects vary)

⚠️ **Important:** Use responsibly! Start with dry-run, keep limits low (5-10), and follow platform Terms of Service.

📖 **See [AUTO_APPLY_GUIDE.md](AUTO_APPLY_GUIDE.md) for complete documentation**

## Output

Results are saved to the `output/` directory with timestamps:
- `jobs_YYYYMMDD_HHMMSS.csv`
- `jobs_YYYYMMDD_HHMMSS.json`
- `jobs_YYYYMMDD_HHMMSS.xlsx`

Jobs are also automatically saved to `jobs.db` database for tracking.

## Project Structure

```
Scrapper/
├── main.py                    # Main application entry point
├── config.py                  # Configuration settings
├── filters.py                 # Job filtering logic
├── export.py                  # Data export utilities
├── database.py                # SQLite database management (NEW!)
├── db_manager.py              # Database CLI tool (NEW!)
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── jobs.db                    # SQLite database (auto-created)
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py       # Abstract base class
│   ├── playwright_scraper.py # Playwright base class
│   ├── indeed_scraper.py
│   ├── linkedin_scraper.py
│   ├── glassdoor_scraper.py
│   ├── remoteok_scraper.py
│   ├── weworkremotely_scraper.py
│   ├── monster_scraper.py
│   ├── dice_scraper.py
│   ├── simplyhired_scraper.py
│   ├── ziprecruiter_scraper.py
│   └── angellist_scraper.py
└── output/                    # Export directory
```

## Notes

- Some platforms may require Selenium (Chrome) for JavaScript rendering
- Be respectful of rate limits - use appropriate delays
- LinkedIn and Glassdoor may have stricter anti-scraping measures
- Results depend on publicly available job listings

## Share publicly for free

If you want others to test without paying for hosting, the fastest path is a free, temporary public URL via Cloudflare Tunnel on your Windows machine:

- Double-click `share_public.bat` (or run it in PowerShell). It will:
   - Start the Flask app locally
   - Download `cloudflared.exe` if missing
   - Open a public URL like `https://<random>.trycloudflare.com` you can share

See `DEPLOY_FREE.md` for detailed instructions and additional zero-cost options (GitHub Codespaces), plus caveats about running scrapers on free hosting providers.

## Troubleshooting

**ChromeDriver issues:**
- The tool automatically downloads ChromeDriver
- Ensure Chrome browser is installed on your system

**No results found:**
- Try broader search terms
- Reduce filters
- Check if the platform websites are accessible

**Slow performance:**
- Reduce `--max-pages`
- Use fewer platforms
- Disable Selenium for faster platforms (edit scrapers)

## 📚 Documentation

- **[CHEATSHEET.md](CHEATSHEET.md)** - Quick command reference (start here!)
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[AUTO_APPLY_GUIDE.md](AUTO_APPLY_GUIDE.md)** - Auto-apply automation guide (NEW!) 🤖
- **[RESUME_PARSER_GUIDE.md](RESUME_PARSER_GUIDE.md)** - Resume parsing guide
- **[KANBAN_GUIDE.md](KANBAN_GUIDE.md)** - Kanban board guide
- **[AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md)** - Complete AI matching guide
- **[AI_EXAMPLES.md](AI_EXAMPLES.md)** - AI usage examples
- **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - Database features
- **[NOTIFICATIONS_GUIDE.md](NOTIFICATIONS_GUIDE.md)** - Notification setup
- **[DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)** - Web dashboard docs
- **[BROWSER_AUTOMATION.md](BROWSER_AUTOMATION.md)** - Browser automation guide
- **[PROGRESS_UPDATE.md](PROGRESS_UPDATE.md)** - Feature status and roadmap

## 🎯 Quick Links

- Need help? → [CHEATSHEET.md](CHEATSHEET.md)
- Getting started? → [QUICKSTART.md](QUICKSTART.md)
- Auto-apply jobs? → [AUTO_APPLY_GUIDE.md](AUTO_APPLY_GUIDE.md) 🤖
- Using AI matching? → [AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md)
- Want examples? → [AI_EXAMPLES.md](AI_EXAMPLES.md)

## License

This tool is for educational purposes. Please respect the terms of service of each job platform.
