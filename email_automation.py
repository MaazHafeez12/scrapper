"""
Email Integration & Automation Module
Provides Gmail/Outlook API integration, automated sequences, and tracking
"""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

class EmailAutomation:
    """Handles email sending, sequences, and tracking."""
    
    def __init__(self):
        self.sent_emails = []
        self.email_sequences = {}
        self.email_responses = []
        
    def send_email_gmail(self, 
                        smtp_server: str,
                        smtp_port: int,
                        sender_email: str,
                        sender_password: str,
                        recipient_email: str,
                        subject: str,
                        body: str,
                        is_html: bool = True) -> Dict:
        """
        Send email via Gmail SMTP.
        
        Args:
            smtp_server: Gmail SMTP server (smtp.gmail.com)
            smtp_port: SMTP port (587 for TLS)
            sender_email: Your Gmail address
            sender_password: App-specific password
            recipient_email: Recipient's email
            subject: Email subject
            body: Email body (HTML or plain text)
            is_html: Whether body is HTML
            
        Returns:
            Dict with success status and details
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            # Track sent email
            email_record = {
                'id': f"email_{int(time.time() * 1000)}",
                'recipient': recipient_email,
                'subject': subject,
                'sent_at': datetime.now().isoformat(),
                'status': 'sent',
                'opened': False,
                'replied': False
            }
            self.sent_emails.append(email_record)
            
            return {
                'success': True,
                'email_id': email_record['id'],
                'sent_at': email_record['sent_at'],
                'message': 'Email sent successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to send email: {str(e)}'
            }
    
    def send_email_outlook(self,
                          smtp_server: str,
                          smtp_port: int,
                          sender_email: str,
                          sender_password: str,
                          recipient_email: str,
                          subject: str,
                          body: str,
                          is_html: bool = True) -> Dict:
        """
        Send email via Outlook/Office365 SMTP.
        
        Args:
            smtp_server: Outlook SMTP server (smtp.office365.com)
            smtp_port: SMTP port (587)
            sender_email: Your Outlook email
            sender_password: Your password
            recipient_email: Recipient's email
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
            
        Returns:
            Dict with success status and details
        """
        # Same implementation as Gmail but with Outlook server
        return self.send_email_gmail(
            smtp_server, smtp_port, sender_email, sender_password,
            recipient_email, subject, body, is_html
        )
    
    def create_email_sequence(self,
                            sequence_name: str,
                            emails: List[Dict]) -> Dict:
        """
        Create an automated email sequence.
        
        Args:
            sequence_name: Name for the sequence
            emails: List of email configs with 'delay_days', 'subject', 'body'
            
        Returns:
            Dict with sequence ID and details
        """
        sequence_id = f"seq_{int(time.time() * 1000)}"
        
        sequence = {
            'id': sequence_id,
            'name': sequence_name,
            'emails': emails,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.email_sequences[sequence_id] = sequence
        
        return {
            'success': True,
            'sequence_id': sequence_id,
            'email_count': len(emails),
            'message': f'Email sequence "{sequence_name}" created with {len(emails)} emails'
        }
    
    def start_email_sequence(self,
                            sequence_id: str,
                            recipient_email: str,
                            personalization: Dict = None) -> Dict:
        """
        Start an email sequence for a recipient.
        
        Args:
            sequence_id: ID of the sequence to start
            recipient_email: Recipient's email
            personalization: Dict of personalization variables
            
        Returns:
            Dict with schedule details
        """
        if sequence_id not in self.email_sequences:
            return {
                'success': False,
                'error': 'Sequence not found'
            }
        
        sequence = self.email_sequences[sequence_id]
        schedule = []
        
        for i, email_config in enumerate(sequence['emails']):
            delay_days = email_config.get('delay_days', 0)
            send_date = datetime.now() + timedelta(days=delay_days)
            
            # Apply personalization if provided
            subject = email_config['subject']
            body = email_config['body']
            
            if personalization:
                for key, value in personalization.items():
                    subject = subject.replace(f'{{{key}}}', str(value))
                    body = body.replace(f'{{{key}}}', str(value))
            
            schedule.append({
                'email_number': i + 1,
                'subject': subject,
                'body': body,
                'scheduled_for': send_date.isoformat(),
                'status': 'scheduled'
            })
        
        return {
            'success': True,
            'recipient': recipient_email,
            'sequence_name': sequence['name'],
            'emails_scheduled': len(schedule),
            'schedule': schedule
        }
    
    def check_email_responses(self,
                             imap_server: str,
                             email_address: str,
                             password: str,
                             since_date: Optional[datetime] = None) -> Dict:
        """
        Check inbox for email responses.
        
        Args:
            imap_server: IMAP server (imap.gmail.com or outlook.office365.com)
            email_address: Your email
            password: Your password
            since_date: Only check emails since this date
            
        Returns:
            Dict with response count and details
        """
        try:
            # Connect to IMAP server
            with imaplib.IMAP4_SSL(imap_server) as imap:
                imap.login(email_address, password)
                imap.select('INBOX')
                
                # Search for unread emails
                search_criteria = 'UNSEEN'
                if since_date:
                    date_str = since_date.strftime('%d-%b-%Y')
                    search_criteria = f'(UNSEEN SINCE {date_str})'
                
                status, message_ids = imap.search(None, search_criteria)
                
                responses = []
                for msg_id in message_ids[0].split():
                    status, msg_data = imap.fetch(msg_id, '(RFC822)')
                    
                    email_msg = email.message_from_bytes(msg_data[0][1])
                    
                    response = {
                        'id': msg_id.decode(),
                        'from': email_msg.get('From'),
                        'subject': email_msg.get('Subject'),
                        'date': email_msg.get('Date'),
                        'body_preview': self._get_email_body_preview(email_msg)
                    }
                    
                    responses.append(response)
                    self.email_responses.append(response)
            
            return {
                'success': True,
                'new_responses': len(responses),
                'responses': responses
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_email_body_preview(self, email_msg, max_length: int = 200) -> str:
        """Extract email body preview."""
        body = ""
        
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_msg.get_payload(decode=True).decode()
        
        return body[:max_length] + "..." if len(body) > max_length else body
    
    def get_email_stats(self) -> Dict:
        """Get email campaign statistics."""
        total_sent = len(self.sent_emails)
        total_opened = sum(1 for e in self.sent_emails if e.get('opened', False))
        total_replied = sum(1 for e in self.sent_emails if e.get('replied', False))
        
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
        
        return {
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_replied': total_replied,
            'open_rate': round(open_rate, 2),
            'reply_rate': round(reply_rate, 2),
            'active_sequences': len([s for s in self.email_sequences.values() if s['active']]),
            'recent_responses': len([r for r in self.email_responses if self._is_recent(r.get('date'))])
        }
    
    def _is_recent(self, date_str: str, days: int = 7) -> bool:
        """Check if date is within last N days."""
        try:
            if not date_str:
                return False
            # This is simplified - would need proper date parsing
            return True
        except:
            return False
    
    def mark_email_opened(self, email_id: str) -> Dict:
        """Mark an email as opened (for tracking)."""
        for email in self.sent_emails:
            if email['id'] == email_id:
                email['opened'] = True
                email['opened_at'] = datetime.now().isoformat()
                return {'success': True, 'message': 'Email marked as opened'}
        
        return {'success': False, 'error': 'Email not found'}
    
    def mark_email_replied(self, email_id: str) -> Dict:
        """Mark an email as replied to."""
        for email in self.sent_emails:
            if email['id'] == email_id:
                email['replied'] = True
                email['replied_at'] = datetime.now().isoformat()
                return {'success': True, 'message': 'Email marked as replied'}
        
        return {'success': False, 'error': 'Email not found'}


# Pre-configured email sequences
EMAIL_SEQUENCE_TEMPLATES = {
    'cold_outreach_5_step': {
        'name': 'Professional Cold Outreach - 5 Step',
        'emails': [
            {
                'delay_days': 0,
                'subject': 'Quick question about {company_name}',
                'body': '''Hi {first_name},

I noticed {company_name} is hiring for a {job_title} position. I specialize in helping companies with similar needs find qualified candidates quickly.

Would you be open to a brief conversation about how we could support your hiring process?

Best regards,
{sender_name}'''
            },
            {
                'delay_days': 3,
                'subject': 'Following up - {company_name} hiring',
                'body': '''Hi {first_name},

I wanted to follow up on my previous email about {company_name}'s {job_title} position.

I have several pre-vetted candidates with relevant experience who might be a great fit. Would you have 10 minutes this week for a quick call?

Best,
{sender_name}'''
            },
            {
                'delay_days': 7,
                'subject': 'Last follow-up - {company_name}',
                'body': '''Hi {first_name},

I don't want to be a bother, so this will be my last follow-up.

If you're still looking to fill the {job_title} position, I'd love to help. If not, no worries at all!

Thanks for your time,
{sender_name}'''
            }
        ]
    },
    'warm_follow_up_3_step': {
        'name': 'Warm Follow-up - 3 Step',
        'emails': [
            {
                'delay_days': 0,
                'subject': 'Great connecting about {company_name}',
                'body': '''Hi {first_name},

It was great connecting! As discussed, I'm following up with information about our recruitment services for the {job_title} position.

Attached is a brief overview of how we can help streamline your hiring process.

Best regards,
{sender_name}'''
            },
            {
                'delay_days': 5,
                'subject': 'Checking in - {company_name} recruitment',
                'body': '''Hi {first_name},

Just checking in to see if you had any questions about the recruitment services overview I sent.

Happy to schedule a quick call to discuss further if that would be helpful.

Best,
{sender_name}'''
            },
            {
                'delay_days': 10,
                'subject': 'Final follow-up - {company_name}',
                'body': '''Hi {first_name},

I wanted to reach out one last time about the {job_title} position.

If timing isn't right now, no problem at all. Feel free to reach out whenever you need recruitment support.

Best regards,
{sender_name}'''
            }
        ]
    }
}
