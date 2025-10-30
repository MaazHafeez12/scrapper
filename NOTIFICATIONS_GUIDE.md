# Email & Webhook Notifications Guide

## Overview

Get instant notifications when new jobs are found! The scraper supports:
- **Email notifications** (Gmail, Outlook, custom SMTP)
- **Slack webhooks**
- **Discord webhooks**
- **Daily digest emails**
- **Status change alerts**

## Quick Start

### 1. Configure Email (Gmail Example)

#### Step 1: Enable 2-Factor Authentication
1. Go to Google Account settings
2. Enable 2-Factor Authentication

#### Step 2: Create App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password

#### Step 3: Update .env File
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_char_app_password
RECIPIENT_EMAIL=recipient@example.com
```

### 2. Test Email Notification

```bash
# Scrape jobs and send email for new ones
python main.py "Python Developer" --remote --email-notify

# Send to specific email
python main.py "Data Scientist" --remote --email-notify --email-to your@email.com
```

### 3. Configure Slack Webhook (Optional)

#### Step 1: Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "Job Scraper" and select your workspace

#### Step 2: Enable Incoming Webhooks
1. In your app settings, go to "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to ON
3. Click "Add New Webhook to Workspace"
4. Select the channel and authorize
5. Copy the webhook URL

#### Step 3: Update .env File
```bash
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
WEBHOOK_TYPE=slack
```

### 4. Test Slack Notification

```bash
python main.py "Software Engineer" --remote --webhook-notify
```

### 5. Configure Discord Webhook (Optional)

#### Step 1: Create Webhook
1. Go to your Discord server
2. Right-click the channel → Edit Channel
3. Go to Integrations → Webhooks
4. Click "New Webhook"
5. Name it "Job Scraper" and copy the URL

#### Step 2: Update .env File
```bash
WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
WEBHOOK_TYPE=discord
```

## Email Notification Features

### 1. New Job Alerts

Send email when new jobs are found:

```bash
# Basic notification
python main.py "Frontend Developer" --remote --email-notify

# With custom recipient
python main.py "Backend Engineer" --email-notify --email-to boss@company.com

# Combine with show-new-only
python main.py "DevOps" --show-new-only --email-notify
```

**Email includes:**
- Job title, company, location
- Salary (if available)
- Remote badge
- Platform badge
- "View Job" button for each job
- Beautiful HTML formatting
- Plain text fallback

### 2. Daily Digest

Send daily summary of all new jobs:

```bash
# Send digest for last 24 hours
python main.py --send-digest --email-to your@email.com

# Custom time period (last 48 hours)
python main.py --send-digest --digest-hours 48 --email-to your@email.com
```

**Digest includes:**
- Total new jobs count
- Jobs grouped by platform
- Top 5 jobs per platform
- Summary statistics
- Professional formatting

### 3. Status Change Alerts

Get notified when you update job status:

```python
# In Python code
from notifications import EmailNotifier
from database import JobDatabase

db = JobDatabase()
notifier = EmailNotifier()

# When status changes
job = {...}  # Job dictionary
notifier.send_status_change_alert(
    recipient="your@email.com",
    job=job,
    old_status="new",
    new_status="applied"
)
```

## Webhook Notification Features

### 1. Slack Notifications

```bash
# Send to Slack
python main.py "Machine Learning" --remote --webhook-notify

# Combine with email
python main.py "Data Analyst" --email-notify --webhook-notify
```

**Slack message includes:**
- Rich formatting with blocks
- Job title as bold header
- Company, location, remote badge
- "View Job" button for each job
- Up to 5 jobs shown
- Count of additional jobs

### 2. Discord Notifications

```bash
# Send to Discord
python main.py "Full Stack" --remote --webhook-notify
```

**Discord embed includes:**
- Colored embed (green)
- Job title as embed field name
- Company and location
- Direct links to jobs
- Remote emoji indicator
- Timestamp
- Job count in footer

## SMTP Server Configurations

### Gmail
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
# Use app password, not regular password
```

### Outlook / Office 365
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SENDER_EMAIL=your@outlook.com
SENDER_PASSWORD=your_password
```

### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
# Generate app password at account.yahoo.com
```

### Custom SMTP
```bash
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587  # or 465 for SSL
SENDER_EMAIL=you@yourcompany.com
SENDER_PASSWORD=your_password
```

## Automated Workflows

### 1. Scheduled Email Alerts

**Windows Task Scheduler:**
```powershell
# Run every 6 hours, email new jobs
python main.py "Software Engineer" --remote --show-new-only --new-since-hours 6 --email-notify
```

**Linux/Mac Cron:**
```bash
# Add to crontab (every 6 hours)
0 */6 * * * cd /path/to/scrapper && python main.py "Python Developer" --remote --show-new-only --new-since-hours 6 --email-notify
```

### 2. Daily Digest Schedule

**Windows Task Scheduler:**
```powershell
# Run every morning at 8 AM
python main.py --send-digest --email-to your@email.com
```

**Linux/Mac Cron:**
```bash
# Every day at 8 AM
0 8 * * * cd /path/to/scrapper && python main.py --send-digest --email-to your@email.com
```

### 3. Multi-Channel Notifications

```bash
# Send to email AND Slack
python main.py "Senior Developer" --remote --email-notify --webhook-notify
```

## Advanced Usage

### Programmatic Notifications

```python
from notifications import NotificationManager, EmailNotifier, WebhookNotifier
from database import JobDatabase

# Get new jobs from database
db = JobDatabase()
new_jobs = db.get_new_jobs(since_hours=24)

# Send via all channels
manager = NotificationManager()
results = manager.notify_new_jobs(
    jobs=new_jobs,
    keywords="Python Developer",
    email_to="your@email.com",
    use_webhook=True
)

print(f"Email sent: {results.get('email', False)}")
print(f"Webhook sent: {results.get('webhook', False)}")
```

### Custom Email Content

```python
from notifications import EmailNotifier

notifier = EmailNotifier(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender_email="your@gmail.com",
    sender_password="your_app_password"
)

# Send custom alert
jobs = [...]  # Your jobs list
notifier.send_new_jobs_alert(
    recipient="recipient@example.com",
    jobs=jobs,
    keywords="Custom Search"
)
```

### Custom Webhook Payload

```python
from notifications import WebhookNotifier

notifier = WebhookNotifier(
    webhook_url="https://hooks.slack.com/...",
    webhook_type="slack"  # or "discord"
)

jobs = [...]  # Your jobs list
notifier.send_new_jobs_notification(jobs, keywords="My Search")
```

## Email Template Customization

The HTML emails use clean, professional styling:
- Responsive design
- Job cards with colored borders
- Badge system (Remote, Platform)
- Call-to-action buttons
- Mobile-friendly layout

To customize templates, edit the methods in `notifications.py`:
- `_create_html_email()` - New job alerts
- `_create_digest_html()` - Daily digests
- Modify CSS in the `<style>` section

## Troubleshooting

### Email Issues

**"Authentication failed"**
- Gmail: Use app password, not regular password
- Enable 2FA first, then generate app password
- Check SMTP_SERVER and SMTP_PORT are correct

**"Connection refused"**
- Check firewall isn't blocking port 587
- Try port 465 with SSL: `smtplib.SMTP_SSL()`
- Verify SMTP server address

**"Sender address rejected"**
- Make sure SENDER_EMAIL matches your account
- Some providers require verified sender

**Emails not arriving**
- Check spam/junk folder
- Verify RECIPIENT_EMAIL is correct
- Test with a simple email first

### Webhook Issues

**"Webhook URL not configured"**
- Set WEBHOOK_URL in .env file
- Make sure no spaces or quotes in URL

**"Failed to send webhook"**
- Verify webhook URL is correct
- Check webhook wasn't deleted in Slack/Discord
- Test URL with curl:
  ```bash
  curl -X POST -H 'Content-Type: application/json' \
    -d '{"text":"test"}' YOUR_WEBHOOK_URL
  ```

**Slack: "Invalid payload"**
- Ensure WEBHOOK_TYPE=slack in .env
- Check Slack webhook format in notifications.py

**Discord: Messages not appearing**
- Ensure WEBHOOK_TYPE=discord in .env
- Verify channel permissions
- Check Discord webhook format

### Debug Mode

Enable debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your notification command
```

## Security Best Practices

1. **Never commit .env file**
   - Already in .gitignore
   - Keep credentials secret

2. **Use app passwords**
   - Don't use your main email password
   - Generate specific app passwords

3. **Rotate credentials**
   - Change passwords periodically
   - Regenerate app passwords if compromised

4. **Limit permissions**
   - Use email accounts with minimal access
   - Create separate accounts for automation

5. **Webhook security**
   - Keep webhook URLs secret
   - Regenerate if exposed
   - Use Discord/Slack URL validation

## Performance Tips

1. **Rate limiting**
   - Don't send emails too frequently
   - Combine multiple jobs in one email
   - Use daily digest for summaries

2. **Batch notifications**
   - Collect jobs first, then notify once
   - Avoid sending email per job

3. **Filter before notifying**
   - Only notify for truly new jobs
   - Use --show-new-only flag
   - Set appropriate time windows

## Command Reference

```bash
# Email notifications
--email-notify              # Send email for new jobs
--email-to EMAIL            # Recipient email
--send-digest               # Send daily digest
--digest-hours N            # Digest time period

# Webhook notifications
--webhook-notify            # Send webhook notification

# Combined usage
python main.py "Python" --remote --email-notify --webhook-notify
python main.py --send-digest --email-to boss@company.com
python main.py "DevOps" --show-new-only --new-since-hours 6 --email-notify
```

## Examples

### Morning Job Check
```bash
# Email you new jobs from overnight
python main.py "Software Engineer" --show-new-only --new-since-hours 12 --email-notify
```

### Team Notifications
```bash
# Send to team Slack channel
python main.py "Frontend Developer" --remote --webhook-notify
```

### Executive Summary
```bash
# Daily digest to manager
python main.py --send-digest --digest-hours 24 --email-to manager@company.com
```

### Real-time Alerts
```bash
# Immediate notification when new jobs appear
python main.py "Senior Python" --remote --show-new-only --email-notify --webhook-notify
```

## See Also

- [DATABASE_GUIDE.md](DATABASE_GUIDE.md) - Database features
- [QUICKSTART.md](QUICKSTART.md) - Getting started
- [README.md](README.md) - Main documentation
- `.env.example` - Configuration template

---

**Notifications Complete!** 🎉 Never miss a job opportunity again!
