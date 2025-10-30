# Web Dashboard Guide

## Overview

The Job Scraper now includes a beautiful web dashboard for managing jobs in your browser! Access all features through an intuitive visual interface.

![Dashboard Features](https://img.shields.io/badge/Features-Complete-success)
![Status](https://img.shields.io/badge/Status-Production Ready-blue)

## Quick Start

### 1. Install Flask

```bash
pip install flask==3.0.0
# or
pip install -r requirements.txt
```

### 2. Start the Dashboard

```bash
python app.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

The dashboard will automatically open with:
- Real-time statistics
- Job listings with filters
- Status management
- Export capabilities

## Features

### 📊 Statistics Dashboard

**Top of page shows 4 key metrics:**
- **Total Jobs** - All jobs in database
- **Remote Jobs** - Count of remote positions
- **New (24h)** - Jobs added in last 24 hours
- **Applied** - Jobs you've applied to

**Updates automatically** every 30 seconds

### 🔍 Advanced Filtering

**Filter jobs by:**
- **Keywords** - Search in title, company, description
- **Platform** - Indeed, LinkedIn, Glassdoor, etc.
- **Status** - New, Applied, Interested, Rejected, Archived
- **Remote Only** - Show only remote positions

**Actions:**
- **Apply Filters** - Search with current filters
- **Reset** - Clear all filters

### 📋 Job Listings

**Each job card shows:**
- Job title and company
- Location and salary (if available)
- Remote badge (if remote)
- Platform badge
- Status badge (color-coded)
- Time since scraped

**Quick Actions:**
- ✓ **Applied** - Mark as applied
- ★ **Interested** - Save for later
- ✗ **Reject** - Mark as not interested
- **View Job →** - Open job posting

**Click any job card** to see full details in modal

### 📥 Export Options

Export filtered jobs to:
- **CSV** - Excel-compatible spreadsheet
- **JSON** - API/database format
- **Excel** - Native .xlsx format

Exports respect current filters!

### 🎯 Job Status Management

**Update status directly from dashboard:**
- Click status buttons on job cards
- Instant update
- Statistics refresh automatically
- Color-coded badges:
  - 🟠 **New** - Just discovered
  - 🟢 **Applied** - Application submitted
  - 🔵 **Interested** - Want to apply
  - 🔴 **Rejected** - Not interested
  - ⚪ **Archived** - Archived for reference

## Dashboard Layout

### Header
- Project title and description
- Gradient background
- Always visible

### Statistics Section
- 4 stat cards in responsive grid
- Hover effects
- Real-time updates

### Filters Section
- Keyword search
- Platform dropdown
- Status dropdown
- Remote toggle
- Apply/Reset buttons

### Jobs List
- Scrollable job cards
- Hover highlighting
- Quick action buttons
- Click for details

### Job Details Modal
- Full job information
- Description preview
- Direct link to apply
- Close button

## API Endpoints

The dashboard uses these REST APIs:

### GET /api/jobs
Get jobs with filtering
```
Query params:
  - keywords: str
  - platform: str
  - status: str
  - remote_only: bool
  - limit: int
  - offset: int
```

### GET /api/jobs/<id>
Get single job details

### POST /api/jobs/<id>/status
Update job status
```json
{
  "status": "applied",
  "notes": "Applied via website"
}
```

### GET /api/stats
Get database statistics

### GET /api/new-jobs
Get new jobs from last N hours
```
Query params:
  - hours: int (default 24)
```

### GET /api/platforms
Get list of available platforms

### GET /api/export
Export jobs to file
```
Query params:
  - format: csv|json|excel
  - platform: str
  - status: str
  - remote_only: bool
```

### GET /api/jobs/<id>/history
Get job change history

### GET /api/search-history
Get recent search history

### POST /api/notify
Send notification for selected jobs
```json
{
  "job_ids": [1, 2, 3],
  "channel": "email",
  "recipient": "you@email.com"
}
```

### POST /api/cleanup
Clean up old jobs
```json
{
  "days": 90
}
```

## Customization

### Change Port

Edit `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### Enable Production Mode

```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

For production, use a WSGI server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Customize Colors

Edit `templates/index.html` CSS:
```css
/* Primary color */
.btn-primary {
    background: #YOUR_COLOR;
}

/* Header gradient */
.header {
    background: linear-gradient(135deg, #COLOR1 0%, #COLOR2 100%);
}
```

### Add Authentication

```python
from flask import session, redirect, url_for

@app.before_request
def require_login():
    if 'user' not in session and request.endpoint != 'login':
        return redirect(url_for('login'))
```

## Advanced Usage

### Integrate with Scraping

**Auto-refresh dashboard after scraping:**
```python
# In main.py after scraping
import requests

# Scrape jobs...
jobs = scrape_all_platforms(...)

# Dashboard will auto-update
# Or manually trigger refresh via API
```

### Scheduled Updates

**Dashboard shows real-time data from database**
- Run scraper via cron/Task Scheduler
- Dashboard reflects changes automatically
- No manual refresh needed

### Multiple Users

**For team usage:**
1. Deploy to server (not localhost)
2. Add authentication (Flask-Login)
3. Add user-specific filters
4. Share URL with team

Example deployment:
```bash
# Install gunicorn
pip install gunicorn

# Run on server
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Access from anywhere
http://your-server-ip:5000
```

### Mobile Access

Dashboard is **fully responsive**:
- Works on phones and tablets
- Touch-friendly buttons
- Optimized layouts
- Swipe gestures

Access from phone:
1. Find your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Start dashboard: `python app.py`
3. On phone, open: `http://YOUR_IP:5000`

## Keyboard Shortcuts

- **Escape** - Close modal
- **Ctrl+R** - Refresh jobs
- **Ctrl+F** - Focus search

## Troubleshooting

### Port Already in Use

```
Error: Address already in use
```

**Solution:**
1. Change port in `app.py`
2. Or kill process using port 5000:
```powershell
# Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:5000 | xargs kill
```

### Cannot Connect from Other Devices

**Problem:** Can only access from localhost

**Solution:**
1. Make sure app runs on `0.0.0.0` not `127.0.0.1`
2. Check firewall allows port 5000
3. Use computer's IP, not localhost

### Database Locked Error

**Problem:** Database is locked

**Solution:**
1. Close any DB browsers
2. Stop other scraper instances
3. Restart dashboard

### Jobs Not Showing

**Problem:** Empty jobs list

**Solution:**
1. Run scraper first: `python main.py "Python" --remote`
2. Check database exists: `jobs.db`
3. View stats: `python db_manager.py stats`

### Slow Performance

**Problem:** Dashboard is slow

**Solution:**
1. Limit jobs displayed: Modify `limit` in `/api/jobs`
2. Add pagination
3. Use production WSGI server (gunicorn)
4. Clean up old jobs: `python db_manager.py cleanup --days 30`

## Security Considerations

### Development Mode

**Current setup is for development:**
- Debug mode enabled
- No authentication
- Local access only

### Production Deployment

**For production:**

1. **Disable Debug Mode**
```python
app.run(debug=False)
```

2. **Add Authentication**
```bash
pip install flask-login
```

3. **Use HTTPS**
```bash
# Use reverse proxy (nginx) with SSL
# Or use Flask-Talisman
pip install flask-talisman
```

4. **Set Secret Key**
```python
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
```

5. **Use Production Server**
```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

6. **Add Rate Limiting**
```bash
pip install flask-limiter
```

## Performance Tips

1. **Pagination** - Limit jobs per page
2. **Caching** - Cache statistics (Flask-Caching)
3. **Lazy Loading** - Load jobs as you scroll
4. **Compression** - Enable gzip (Flask-Compress)
5. **CDN** - Serve static files from CDN

## Browser Compatibility

✅ **Supported Browsers:**
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera
- Mobile browsers

**Requires:** JavaScript enabled

## Deployment Options

### Local Development
```bash
python app.py
# Access: http://localhost:5000
```

### Docker
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create job-scraper-dashboard
git push heroku main
```

### AWS/Azure/GCP
Use standard Python web app deployment
- Elastic Beanstalk (AWS)
- App Service (Azure)
- App Engine (GCP)

## Future Enhancements

### Planned Features
- 📱 Progressive Web App (PWA)
- 🔔 Real-time notifications (WebSockets)
- 📊 Charts and analytics
- 👥 Multi-user support
- 🔐 OAuth authentication
- 📧 Send emails from dashboard
- 🤖 AI job matching interface
- 📅 Application calendar view
- 💾 Bulk operations
- 🌙 Dark mode

### Coming Soon
- Search history view
- Job comparison tool
- Company research panel
- Salary analytics
- Application timeline
- Interview tracker

## Integration Examples

### With Main Scraper
```bash
# 1. Run scraper
python main.py "Python" --remote --use-database

# 2. View in dashboard
python app.py
# Open http://localhost:5000
```

### With Notifications
```bash
# Scrape and notify
python main.py "DevOps" --show-new-only --email-notify

# View results in dashboard
python app.py
```

### With Database Manager
```bash
# Update status via CLI
python db_manager.py update-status <url> applied

# See change in dashboard (auto-refreshes)
```

## Command Reference

```bash
# Start dashboard
python app.py

# Custom port
python app.py --port 8080

# Production mode
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With auto-reload (development)
export FLASK_ENV=development
flask run
```

## Tips & Tricks

1. **Bookmark URL** - Quick access to dashboard
2. **Use filters** - Save time finding specific jobs
3. **Bulk status updates** - Select multiple jobs
4. **Export regularly** - Backup your data
5. **Mobile access** - Check jobs on the go
6. **Keyboard shortcuts** - Faster navigation
7. **Share with team** - Deploy to server
8. **Auto-refresh** - Leave dashboard open

## Support

**Documentation:**
- README.md - Main documentation
- DATABASE_GUIDE.md - Database features
- NOTIFICATIONS_GUIDE.md - Email & webhooks

**Code:**
- `app.py` - Flask backend
- `templates/index.html` - Frontend
- `database.py` - Database operations

---

**Dashboard Complete!** 🎉 Manage your job search visually!
