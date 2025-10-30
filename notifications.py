"""Email and webhook notification system for job alerts."""
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import os
from database import JobDatabase
from rich.console import Console

console = Console()


class EmailNotifier:
    """Send email notifications for new jobs."""
    
    def __init__(self, 
                 smtp_server: str = None,
                 smtp_port: int = 587,
                 sender_email: str = None,
                 sender_password: str = None):
        """Initialize email notifier.
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (default: 587 for TLS)
            sender_email: Sender email address
            sender_password: Sender email password or app password
        """
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL')
        self.sender_password = sender_password or os.getenv('SENDER_PASSWORD')
        
        if not all([self.smtp_server, self.sender_email, self.sender_password]):
            console.print("[yellow]Warning: Email credentials not configured[/yellow]")
            console.print("Set SMTP_SERVER, SENDER_EMAIL, SENDER_PASSWORD in .env file")
    
    def send_new_jobs_alert(self, 
                           recipient: str, 
                           jobs: List[Dict],
                           keywords: str = None) -> bool:
        """Send email alert for new jobs.
        
        Args:
            recipient: Recipient email address
            jobs: List of job dictionaries
            keywords: Search keywords used
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not jobs:
            console.print("[yellow]No jobs to send[/yellow]")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎯 {len(jobs)} New Job Alert{'s' if len(jobs) > 1 else ''}"
            if keywords:
                msg['Subject'] += f" - {keywords}"
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # Create HTML and plain text versions
            text_content = self._create_text_email(jobs, keywords)
            html_content = self._create_html_email(jobs, keywords)
            
            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            console.print(f"[green]✓[/green] Email sent to {recipient}")
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to send email: {e}[/red]")
            return False
    
    def send_daily_digest(self, 
                         recipient: str,
                         hours: int = 24) -> bool:
        """Send daily digest of new jobs.
        
        Args:
            recipient: Recipient email address
            hours: Hours to look back (default: 24)
            
        Returns:
            True if sent successfully
        """
        db = JobDatabase()
        jobs = db.get_new_jobs(since_hours=hours)
        
        if not jobs:
            console.print("[yellow]No new jobs in digest period[/yellow]")
            return False
        
        # Group jobs by platform
        jobs_by_platform = {}
        for job in jobs:
            platform = job.get('platform', 'Unknown')
            if platform not in jobs_by_platform:
                jobs_by_platform[platform] = []
            jobs_by_platform[platform].append(job)
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Daily Job Digest - {len(jobs)} New Jobs"
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # Create content
            text_content = self._create_digest_text(jobs_by_platform, hours)
            html_content = self._create_digest_html(jobs_by_platform, hours)
            
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            console.print(f"[green]✓[/green] Daily digest sent to {recipient}")
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to send digest: {e}[/red]")
            return False
    
    def send_status_change_alert(self,
                                 recipient: str,
                                 job: Dict,
                                 old_status: str,
                                 new_status: str) -> bool:
        """Send alert when job status changes.
        
        Args:
            recipient: Recipient email address
            job: Job dictionary
            old_status: Previous status
            new_status: New status
            
        Returns:
            True if sent successfully
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📝 Job Status Updated: {job.get('title', 'Job')}"
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # Create content
            text = f"""
Job Status Updated

Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Status: {old_status} → {new_status}

URL: {job.get('url', 'N/A')}

---
Job Scraper Tool
            """
            
            html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #4CAF50;">📝 Job Status Updated</h2>
    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
        <h3 style="margin-top: 0;">{job.get('title', 'N/A')}</h3>
        <p><strong>Company:</strong> {job.get('company', 'N/A')}</p>
        <p><strong>Status:</strong> <span style="color: #999;">{old_status}</span> → <span style="color: #4CAF50;">{new_status}</span></p>
        <a href="{job.get('url', '#')}" style="display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 10px;">View Job</a>
    </div>
</body>
</html>
            """
            
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            console.print(f"[green]✓[/green] Status change alert sent")
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to send alert: {e}[/red]")
            return False
    
    def _create_text_email(self, jobs: List[Dict], keywords: str = None) -> str:
        """Create plain text email content."""
        lines = []
        lines.append("🎯 NEW JOB ALERTS")
        lines.append("=" * 50)
        
        if keywords:
            lines.append(f"\nSearch: {keywords}")
        
        lines.append(f"\nFound {len(jobs)} new job{'s' if len(jobs) > 1 else ''}:\n")
        
        for i, job in enumerate(jobs[:20], 1):  # Limit to 20 jobs
            lines.append(f"{i}. {job.get('title', 'N/A')}")
            lines.append(f"   Company: {job.get('company', 'N/A')}")
            lines.append(f"   Location: {job.get('location', 'N/A')}")
            if job.get('salary'):
                lines.append(f"   Salary: {job.get('salary')}")
            lines.append(f"   Remote: {'Yes' if job.get('remote') else 'No'}")
            lines.append(f"   Platform: {job.get('platform', 'N/A')}")
            lines.append(f"   URL: {job.get('url', 'N/A')}")
            lines.append("")
        
        if len(jobs) > 20:
            lines.append(f"... and {len(jobs) - 20} more jobs")
        
        lines.append("\n" + "=" * 50)
        lines.append("Job Scraper Tool")
        
        return "\n".join(lines)
    
    def _create_html_email(self, jobs: List[Dict], keywords: str = None) -> str:
        """Create HTML email content."""
        html_parts = [
            '<html>',
            '<head>',
            '<style>',
            'body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }',
            '.job-card { background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4CAF50; }',
            '.job-title { color: #333; font-size: 18px; font-weight: bold; margin: 0 0 10px 0; }',
            '.job-info { color: #666; margin: 5px 0; }',
            '.remote-badge { background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }',
            '.platform-badge { background-color: #2196F3; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }',
            '.apply-btn { display: inline-block; background-color: #4CAF50; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 10px; }',
            '.apply-btn:hover { background-color: #45a049; }',
            '</style>',
            '</head>',
            '<body>',
            '<h1 style="color: #4CAF50;">🎯 New Job Alerts</h1>',
        ]
        
        if keywords:
            html_parts.append(f'<p><strong>Search:</strong> {keywords}</p>')
        
        html_parts.append(f'<p>Found <strong>{len(jobs)}</strong> new job{"s" if len(jobs) > 1 else ""}:</p>')
        
        for job in jobs[:20]:  # Limit to 20 jobs
            html_parts.append('<div class="job-card">')
            html_parts.append(f'<h2 class="job-title">{job.get("title", "N/A")}</h2>')
            html_parts.append(f'<p class="job-info"><strong>Company:</strong> {job.get("company", "N/A")}</p>')
            html_parts.append(f'<p class="job-info"><strong>Location:</strong> {job.get("location", "N/A")}</p>')
            
            if job.get('salary'):
                html_parts.append(f'<p class="job-info"><strong>Salary:</strong> {job.get("salary")}</p>')
            
            # Badges
            badges = []
            if job.get('remote'):
                badges.append('<span class="remote-badge">Remote</span>')
            badges.append(f'<span class="platform-badge">{job.get("platform", "N/A")}</span>')
            html_parts.append(f'<p class="job-info">{" ".join(badges)}</p>')
            
            # Apply button
            if job.get('url'):
                html_parts.append(f'<a href="{job["url"]}" class="apply-btn">View Job →</a>')
            
            html_parts.append('</div>')
        
        if len(jobs) > 20:
            html_parts.append(f'<p><em>... and {len(jobs) - 20} more jobs</em></p>')
        
        html_parts.append('<hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">')
        html_parts.append('<p style="color: #999; text-align: center;">Job Scraper Tool</p>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    def _create_digest_text(self, jobs_by_platform: Dict[str, List[Dict]], hours: int) -> str:
        """Create plain text digest."""
        lines = []
        lines.append("📊 DAILY JOB DIGEST")
        lines.append("=" * 50)
        lines.append(f"\nNew jobs in the last {hours} hours\n")
        
        total = sum(len(jobs) for jobs in jobs_by_platform.values())
        lines.append(f"Total: {total} new jobs")
        lines.append("")
        
        for platform, jobs in sorted(jobs_by_platform.items()):
            lines.append(f"\n{platform.upper()} ({len(jobs)} jobs)")
            lines.append("-" * 30)
            
            for job in jobs[:5]:  # Top 5 per platform
                lines.append(f"  • {job.get('title', 'N/A')}")
                lines.append(f"    {job.get('company', 'N/A')} - {job.get('location', 'N/A')}")
            
            if len(jobs) > 5:
                lines.append(f"  ... and {len(jobs) - 5} more")
        
        lines.append("\n" + "=" * 50)
        lines.append("Job Scraper Tool")
        
        return "\n".join(lines)
    
    def _create_digest_html(self, jobs_by_platform: Dict[str, List[Dict]], hours: int) -> str:
        """Create HTML digest."""
        total = sum(len(jobs) for jobs in jobs_by_platform.values())
        
        html_parts = [
            '<html>',
            '<head>',
            '<style>',
            'body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }',
            '.platform-section { margin: 20px 0; }',
            '.platform-header { background-color: #2196F3; color: white; padding: 10px; border-radius: 4px; }',
            '.job-item { padding: 10px; margin: 5px 0; background-color: #f5f5f5; border-left: 3px solid #4CAF50; }',
            '.summary { background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }',
            '</style>',
            '</head>',
            '<body>',
            '<h1 style="color: #2196F3;">📊 Daily Job Digest</h1>',
            f'<div class="summary">',
            f'<p style="margin: 0; font-size: 18px;"><strong>{total}</strong> new jobs in the last <strong>{hours}</strong> hours</p>',
            f'</div>',
        ]
        
        for platform, jobs in sorted(jobs_by_platform.items()):
            html_parts.append('<div class="platform-section">')
            html_parts.append(f'<div class="platform-header"><strong>{platform.upper()}</strong> ({len(jobs)} jobs)</div>')
            
            for job in jobs[:5]:
                html_parts.append('<div class="job-item">')
                html_parts.append(f'<strong>{job.get("title", "N/A")}</strong><br>')
                html_parts.append(f'{job.get("company", "N/A")} - {job.get("location", "N/A")}')
                if job.get('url'):
                    html_parts.append(f' <a href="{job["url"]}" style="color: #4CAF50;">View →</a>')
                html_parts.append('</div>')
            
            if len(jobs) > 5:
                html_parts.append(f'<p style="margin-left: 10px;"><em>... and {len(jobs) - 5} more</em></p>')
            
            html_parts.append('</div>')
        
        html_parts.append('<hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">')
        html_parts.append('<p style="color: #999; text-align: center;">Job Scraper Tool</p>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)


class WebhookNotifier:
    """Send webhook notifications (Slack, Discord, etc.)."""
    
    def __init__(self, webhook_url: str = None, webhook_type: str = 'slack'):
        """Initialize webhook notifier.
        
        Args:
            webhook_url: Webhook URL
            webhook_type: Type of webhook ('slack' or 'discord')
        """
        self.webhook_url = webhook_url or os.getenv('WEBHOOK_URL')
        self.webhook_type = webhook_type.lower()
        
        if not self.webhook_url:
            console.print("[yellow]Warning: Webhook URL not configured[/yellow]")
            console.print("Set WEBHOOK_URL in .env file")
    
    def send_new_jobs_notification(self, jobs: List[Dict], keywords: str = None) -> bool:
        """Send webhook notification for new jobs.
        
        Args:
            jobs: List of job dictionaries
            keywords: Search keywords
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            console.print("[yellow]Webhook URL not configured[/yellow]")
            return False
        
        if not jobs:
            return False
        
        try:
            if self.webhook_type == 'slack':
                payload = self._create_slack_payload(jobs, keywords)
            elif self.webhook_type == 'discord':
                payload = self._create_discord_payload(jobs, keywords)
            else:
                console.print(f"[red]Unknown webhook type: {self.webhook_type}[/red]")
                return False
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            console.print(f"[green]✓[/green] Webhook notification sent ({self.webhook_type})")
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to send webhook: {e}[/red]")
            return False
    
    def _create_slack_payload(self, jobs: List[Dict], keywords: str = None) -> dict:
        """Create Slack webhook payload."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 {len(jobs)} New Job Alert{'s' if len(jobs) > 1 else ''}"
                }
            }
        ]
        
        if keywords:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Search:* {keywords}"
                }
            })
        
        blocks.append({"type": "divider"})
        
        # Add first 5 jobs
        for job in jobs[:5]:
            job_text = f"*{job.get('title', 'N/A')}*\n"
            job_text += f"Company: {job.get('company', 'N/A')}\n"
            job_text += f"Location: {job.get('location', 'N/A')}"
            
            if job.get('remote'):
                job_text += " 🏠 Remote"
            
            block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": job_text
                }
            }
            
            if job.get('url'):
                block["accessory"] = {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Job"
                    },
                    "url": job['url']
                }
            
            blocks.append(block)
        
        if len(jobs) > 5:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_... and {len(jobs) - 5} more jobs_"
                }
            })
        
        return {"blocks": blocks}
    
    def _create_discord_payload(self, jobs: List[Dict], keywords: str = None) -> dict:
        """Create Discord webhook payload."""
        embed = {
            "title": f"🎯 {len(jobs)} New Job Alert{'s' if len(jobs) > 1 else ''}",
            "color": 5025616,  # Green
            "fields": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if keywords:
            embed["description"] = f"**Search:** {keywords}"
        
        # Add first 5 jobs
        for job in jobs[:5]:
            field_value = f"**Company:** {job.get('company', 'N/A')}\n"
            field_value += f"**Location:** {job.get('location', 'N/A')}"
            
            if job.get('remote'):
                field_value += " 🏠"
            
            if job.get('url'):
                field_value += f"\n[View Job]({job['url']})"
            
            embed["fields"].append({
                "name": job.get('title', 'N/A'),
                "value": field_value,
                "inline": False
            })
        
        if len(jobs) > 5:
            embed["footer"] = {
                "text": f"... and {len(jobs) - 5} more jobs"
            }
        
        return {"embeds": [embed]}


class NotificationManager:
    """Manage all notification channels."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.email = EmailNotifier()
        self.webhook = WebhookNotifier()
    
    def notify_new_jobs(self, 
                       jobs: List[Dict],
                       keywords: str = None,
                       email_to: str = None,
                       use_webhook: bool = False) -> Dict[str, bool]:
        """Send notifications through all configured channels.
        
        Args:
            jobs: List of job dictionaries
            keywords: Search keywords
            email_to: Email recipient
            use_webhook: Whether to send webhook notification
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        
        if email_to:
            results['email'] = self.email.send_new_jobs_alert(email_to, jobs, keywords)
        
        if use_webhook:
            results['webhook'] = self.webhook.send_new_jobs_notification(jobs, keywords)
        
        return results
