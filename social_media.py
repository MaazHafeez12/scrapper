"""
Social Media Automation Module
LinkedIn/Twitter outreach, auto-connection, DM automation, post engagement
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import hashlib
import random
import time

class SocialMediaAutomation:
    def __init__(self, db_connection):
        self.db = db_connection
        # In production: Initialize LinkedIn and Twitter API clients
        self.linkedin_client = None
        self.twitter_client = None
        
    def connect_linkedin_account(self, user_id: str, credentials: Dict) -> Dict:
        """Connect LinkedIn account for automation"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                platform TEXT,
                username TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TIMESTAMP,
                account_status TEXT DEFAULT 'active',
                daily_limit INTEGER,
                daily_usage INTEGER DEFAULT 0,
                last_reset TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        account_id = hashlib.md5(f"{user_id}linkedin{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO social_accounts 
            (id, user_id, platform, username, access_token, refresh_token, 
             token_expires_at, daily_limit, last_reset)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_id, user_id, 'linkedin',
            credentials.get('username'),
            credentials.get('access_token'),
            credentials.get('refresh_token'),
            credentials.get('expires_at'),
            credentials.get('daily_limit', 100),
            datetime.now().isoformat()
        ))
        self.db.commit()
        
        return {
            'success': True,
            'account_id': account_id,
            'platform': 'linkedin',
            'message': 'LinkedIn account connected successfully'
        }
    
    def send_connection_request(self, account_id: str, profile_url: str, 
                                message: str = None) -> Dict:
        """Send LinkedIn connection request"""
        # Check rate limits
        if not self._check_rate_limit(account_id):
            return {'success': False, 'error': 'Daily limit reached'}
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_connections (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                platform TEXT,
                profile_url TEXT,
                profile_name TEXT,
                connection_message TEXT,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                accepted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        connection_id = hashlib.md5(f"{account_id}{profile_url}{datetime.now()}".encode()).hexdigest()[:12]
        
        # In production: Use LinkedIn API to send connection request
        # linkedin_api.send_connection_request(profile_url, message)
        
        cursor.execute('''
            INSERT INTO social_connections 
            (id, account_id, platform, profile_url, connection_message, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            connection_id, account_id, 'linkedin', profile_url,
            message or "I'd like to connect with you on LinkedIn.",
            datetime.now().isoformat()
        ))
        
        self._increment_usage(account_id)
        self.db.commit()
        
        return {
            'success': True,
            'connection_id': connection_id,
            'message': 'Connection request sent'
        }
    
    def send_linkedin_message(self, account_id: str, profile_url: str, 
                             message: str, campaign_id: str = None) -> Dict:
        """Send LinkedIn direct message"""
        if not self._check_rate_limit(account_id):
            return {'success': False, 'error': 'Daily limit reached'}
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_messages (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                campaign_id TEXT,
                platform TEXT,
                recipient_url TEXT,
                recipient_name TEXT,
                message_content TEXT,
                status TEXT DEFAULT 'sent',
                sent_at TIMESTAMP,
                read_at TIMESTAMP,
                replied_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        message_id = hashlib.md5(f"{account_id}{profile_url}{datetime.now()}".encode()).hexdigest()[:12]
        
        # In production: Use LinkedIn API to send message
        # linkedin_api.send_message(profile_url, message)
        
        cursor.execute('''
            INSERT INTO social_messages 
            (id, account_id, campaign_id, platform, recipient_url, message_content, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            message_id, account_id, campaign_id, 'linkedin',
            profile_url, message, datetime.now().isoformat()
        ))
        
        self._increment_usage(account_id)
        self.db.commit()
        
        return {
            'success': True,
            'message_id': message_id,
            'message': 'LinkedIn message sent'
        }
    
    def auto_engage_posts(self, account_id: str, search_keywords: List[str], 
                         actions: List[str], limit: int = 10) -> Dict:
        """Automatically engage with LinkedIn posts (like, comment, share)"""
        if not self._check_rate_limit(account_id):
            return {'success': False, 'error': 'Daily limit reached'}
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_engagements (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                platform TEXT,
                post_url TEXT,
                post_author TEXT,
                engagement_type TEXT,
                comment_text TEXT,
                engaged_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        results = {
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'total': 0
        }
        
        # In production: Search LinkedIn for posts with keywords
        # posts = linkedin_api.search_posts(keywords=search_keywords, limit=limit)
        
        # Mock engagement
        for i in range(min(limit, 10)):
            engagement_type = random.choice(actions)
            engagement_id = hashlib.md5(f"{account_id}{i}{datetime.now()}".encode()).hexdigest()[:12]
            
            cursor.execute('''
                INSERT INTO social_engagements 
                (id, account_id, platform, post_url, engagement_type, engaged_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                engagement_id, account_id, 'linkedin',
                f"https://linkedin.com/posts/{random.randint(1000, 9999)}",
                engagement_type, datetime.now().isoformat()
            ))
            
            if engagement_type == 'like':
                results['likes'] += 1
            elif engagement_type == 'comment':
                results['comments'] += 1
            elif engagement_type == 'share':
                results['shares'] += 1
            
            results['total'] += 1
            self._increment_usage(account_id)
        
        self.db.commit()
        
        return {
            'success': True,
            'engagements': results
        }
    
    def schedule_linkedin_post(self, account_id: str, post_data: Dict) -> Dict:
        """Schedule LinkedIn post"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                platform TEXT,
                content TEXT,
                media_urls TEXT,
                hashtags TEXT,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'scheduled',
                posted_at TIMESTAMP,
                post_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        post_id = hashlib.md5(f"{account_id}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO scheduled_posts 
            (id, account_id, platform, content, media_urls, hashtags, scheduled_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            post_id, account_id, 'linkedin',
            post_data['content'],
            json.dumps(post_data.get('media_urls', [])),
            json.dumps(post_data.get('hashtags', [])),
            post_data['scheduled_time']
        ))
        self.db.commit()
        
        return {
            'success': True,
            'post_id': post_id,
            'scheduled_for': post_data['scheduled_time'],
            'message': 'Post scheduled successfully'
        }
    
    def create_social_campaign(self, campaign_data: Dict) -> Dict:
        """Create social media outreach campaign"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_campaigns (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                name TEXT,
                description TEXT,
                platform TEXT,
                campaign_type TEXT,
                target_profiles TEXT,
                message_template TEXT,
                auto_connect INTEGER DEFAULT 0,
                auto_message INTEGER DEFAULT 0,
                auto_engage INTEGER DEFAULT 0,
                daily_limit INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        campaign_id = hashlib.md5(f"{campaign_data['name']}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO social_campaigns 
            (id, account_id, name, description, platform, campaign_type, 
             target_profiles, message_template, auto_connect, auto_message, 
             auto_engage, daily_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign_id,
            campaign_data['account_id'],
            campaign_data['name'],
            campaign_data.get('description', ''),
            campaign_data.get('platform', 'linkedin'),
            campaign_data['campaign_type'],
            json.dumps(campaign_data.get('target_profiles', [])),
            campaign_data.get('message_template', ''),
            1 if campaign_data.get('auto_connect') else 0,
            1 if campaign_data.get('auto_message') else 0,
            1 if campaign_data.get('auto_engage') else 0,
            campaign_data.get('daily_limit', 50)
        ))
        self.db.commit()
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Social media campaign created'
        }
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get social campaign statistics"""
        cursor = self.db.cursor()
        
        cursor.execute('SELECT account_id, platform FROM social_campaigns WHERE id = ?', (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            return {'success': False, 'error': 'Campaign not found'}
        
        account_id = campaign[0]
        
        # Connection requests
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM social_connections
            WHERE account_id = ?
        ''', (account_id,))
        
        connections = cursor.fetchone()
        
        # Messages
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replies
            FROM social_messages
            WHERE campaign_id = ?
        ''', (campaign_id,))
        
        messages = cursor.fetchone()
        
        # Engagements
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN engagement_type = 'like' THEN 1 ELSE 0 END) as likes,
                SUM(CASE WHEN engagement_type = 'comment' THEN 1 ELSE 0 END) as comments,
                SUM(CASE WHEN engagement_type = 'share' THEN 1 ELSE 0 END) as shares
            FROM social_engagements
            WHERE account_id = ?
        ''', (account_id,))
        
        engagements = cursor.fetchone()
        
        return {
            'campaign_id': campaign_id,
            'connections': {
                'total': connections[0] or 0,
                'accepted': connections[1] or 0,
                'pending': connections[2] or 0,
                'acceptance_rate': round((connections[1] / connections[0] * 100) if connections[0] > 0 else 0, 2)
            },
            'messages': {
                'total': messages[0] or 0,
                'replies': messages[1] or 0,
                'reply_rate': round((messages[1] / messages[0] * 100) if messages[0] > 0 else 0, 2)
            },
            'engagements': {
                'total': engagements[0] or 0,
                'likes': engagements[1] or 0,
                'comments': engagements[2] or 0,
                'shares': engagements[3] or 0
            }
        }
    
    def get_social_analytics(self, account_id: str, date_range: Dict) -> Dict:
        """Get overall social media analytics"""
        cursor = self.db.cursor()
        
        # Daily activity
        cursor.execute('''
            SELECT DATE(sent_at) as date, COUNT(*) as count
            FROM social_messages
            WHERE account_id = ? AND sent_at BETWEEN ? AND ?
            GROUP BY DATE(sent_at)
            ORDER BY date
        ''', (account_id, date_range['start'], date_range['end']))
        
        daily_messages = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Top engaging posts
        cursor.execute('''
            SELECT post_url, COUNT(*) as engagements
            FROM social_engagements
            WHERE account_id = ? AND engaged_at BETWEEN ? AND ?
            GROUP BY post_url
            ORDER BY engagements DESC
            LIMIT 10
        ''', (account_id, date_range['start'], date_range['end']))
        
        top_posts = [{'url': row[0], 'engagements': row[1]} for row in cursor.fetchall()]
        
        return {
            'account_id': account_id,
            'daily_messages': daily_messages,
            'top_posts': top_posts
        }
    
    def _check_rate_limit(self, account_id: str) -> bool:
        """Check if account has reached daily rate limit"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT daily_limit, daily_usage, last_reset 
            FROM social_accounts WHERE id = ?
        ''', (account_id,))
        
        row = cursor.fetchone()
        if not row:
            return False
        
        daily_limit, daily_usage, last_reset = row
        last_reset_dt = datetime.fromisoformat(last_reset)
        
        # Reset if it's a new day
        if datetime.now().date() > last_reset_dt.date():
            cursor.execute('''
                UPDATE social_accounts 
                SET daily_usage = 0, last_reset = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), account_id))
            self.db.commit()
            return True
        
        return daily_usage < daily_limit
    
    def _increment_usage(self, account_id: str):
        """Increment daily usage counter"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE social_accounts 
            SET daily_usage = daily_usage + 1
            WHERE id = ?
        ''', (account_id,))
