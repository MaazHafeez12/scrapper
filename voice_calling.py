"""
Voice Calling System Module
Twilio Voice API for automated calls, voicemail drops, call recording, transcription
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import hashlib
import random

class VoiceCallingSystem:
    def __init__(self, db_connection, account_sid: str = None, auth_token: str = None, from_number: str = None):
        self.db = db_connection
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        
        # In production: Initialize Twilio client
        # from twilio.rest import Client
        # self.client = Client(account_sid, auth_token)
        self.client = None
        
    def make_call(self, to_number: str, call_type: str, campaign_id: str = None, 
                  script_id: str = None) -> Dict:
        """Make an outbound call"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_calls (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                to_number TEXT,
                from_number TEXT,
                call_type TEXT,
                script_id TEXT,
                status TEXT,
                duration INTEGER,
                recording_url TEXT,
                transcription TEXT,
                call_sid TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                answered INTEGER DEFAULT 0,
                voicemail_detected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        call_id = hashlib.md5(f"{to_number}{datetime.now()}".encode()).hexdigest()[:12]
        
        # Get script if provided
        script_content = None
        if script_id:
            cursor.execute('SELECT content FROM call_scripts WHERE id = ?', (script_id,))
            script_row = cursor.fetchone()
            if script_row:
                script_content = script_row[0]
        
        # In production: Make actual Twilio call
        call_sid = f"CA{random.randint(10000000, 99999999)}"
        
        # Log call attempt
        cursor.execute('''
            INSERT INTO voice_calls 
            (id, campaign_id, to_number, from_number, call_type, script_id, status, call_sid, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (call_id, campaign_id, to_number, self.from_number, call_type, script_id, 
              'initiated', call_sid, datetime.now().isoformat()))
        self.db.commit()
        
        return {
            'success': True,
            'call_id': call_id,
            'call_sid': call_sid,
            'status': 'initiated',
            'message': 'Call initiated successfully'
        }
    
    def make_bulk_calls(self, contacts: List[Dict], campaign_id: str, script_id: str) -> Dict:
        """Make bulk outbound calls"""
        results = {
            'total': len(contacts),
            'initiated': 0,
            'failed': 0,
            'calls': []
        }
        
        for contact in contacts:
            try:
                result = self.make_call(
                    to_number=contact['phone'],
                    call_type='outbound',
                    campaign_id=campaign_id,
                    script_id=script_id
                )
                results['initiated'] += 1
                results['calls'].append({
                    'phone': contact['phone'],
                    'status': 'initiated',
                    'call_id': result['call_id']
                })
            except Exception as e:
                results['failed'] += 1
                results['calls'].append({
                    'phone': contact['phone'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    def drop_voicemail(self, to_number: str, voicemail_id: str, campaign_id: str = None) -> Dict:
        """Drop pre-recorded voicemail"""
        cursor = self.db.cursor()
        
        # Get voicemail recording
        cursor.execute('SELECT recording_url FROM voicemail_drops WHERE id = ?', (voicemail_id,))
        voicemail_row = cursor.fetchone()
        
        if not voicemail_row:
            return {'success': False, 'error': 'Voicemail not found'}
        
        recording_url = voicemail_row[0]
        
        # In production: Use Twilio to drop voicemail
        # Use AMD (Answering Machine Detection) to detect voicemail and play recording
        call_result = self.make_call(
            to_number=to_number,
            call_type='voicemail_drop',
            campaign_id=campaign_id
        )
        
        return {
            'success': True,
            'call_id': call_result['call_id'],
            'message': 'Voicemail drop initiated'
        }
    
    def update_call_status(self, call_id: str, status: str, details: Dict) -> Dict:
        """Update call status from webhook"""
        cursor = self.db.cursor()
        
        update_fields = ['status = ?']
        params = [status]
        
        if 'duration' in details:
            update_fields.append('duration = ?')
            params.append(details['duration'])
        
        if 'answered' in details:
            update_fields.append('answered = ?')
            params.append(1 if details['answered'] else 0)
        
        if 'voicemail_detected' in details:
            update_fields.append('voicemail_detected = ?')
            params.append(1 if details['voicemail_detected'] else 0)
        
        if 'recording_url' in details:
            update_fields.append('recording_url = ?')
            params.append(details['recording_url'])
        
        if status in ['completed', 'failed', 'no-answer']:
            update_fields.append('end_time = ?')
            params.append(datetime.now().isoformat())
        
        params.append(call_id)
        
        cursor.execute(f'''
            UPDATE voice_calls 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        self.db.commit()
        
        return {'success': True, 'call_id': call_id}
    
    def get_call_recording(self, call_id: str) -> Dict:
        """Get call recording URL"""
        cursor = self.db.cursor()
        cursor.execute('SELECT recording_url FROM voice_calls WHERE id = ?', (call_id,))
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return {'success': False, 'error': 'Recording not found'}
        
        return {
            'success': True,
            'call_id': call_id,
            'recording_url': row[0]
        }
    
    def transcribe_call(self, call_id: str) -> Dict:
        """Transcribe call recording"""
        cursor = self.db.cursor()
        cursor.execute('SELECT recording_url FROM voice_calls WHERE id = ?', (call_id,))
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return {'success': False, 'error': 'Recording not found'}
        
        # In production: Use Twilio transcription or external service (Deepgram, AssemblyAI)
        transcription = "Mock transcription of the call conversation..."
        
        cursor.execute('UPDATE voice_calls SET transcription = ? WHERE id = ?', 
                      (transcription, call_id))
        self.db.commit()
        
        return {
            'success': True,
            'call_id': call_id,
            'transcription': transcription
        }
    
    def create_call_script(self, script_data: Dict) -> Dict:
        """Create call script for campaigns"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_scripts (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                content TEXT,
                voice TEXT,
                language TEXT,
                tts_provider TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        script_id = hashlib.md5(f"{script_data['name']}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO call_scripts 
            (id, name, description, content, voice, language, tts_provider, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            script_id,
            script_data['name'],
            script_data.get('description', ''),
            script_data['content'],
            script_data.get('voice', 'alice'),
            script_data.get('language', 'en-US'),
            script_data.get('tts_provider', 'twilio'),
            json.dumps(script_data.get('tags', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'script_id': script_id,
            'message': 'Call script created successfully'
        }
    
    def create_voicemail_drop(self, voicemail_data: Dict) -> Dict:
        """Create pre-recorded voicemail for dropping"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voicemail_drops (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                recording_url TEXT,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        voicemail_id = hashlib.md5(f"{voicemail_data['name']}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO voicemail_drops 
            (id, name, description, recording_url, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            voicemail_id,
            voicemail_data['name'],
            voicemail_data.get('description', ''),
            voicemail_data['recording_url'],
            voicemail_data.get('duration', 0)
        ))
        self.db.commit()
        
        return {
            'success': True,
            'voicemail_id': voicemail_id,
            'message': 'Voicemail drop created successfully'
        }
    
    def create_voice_campaign(self, campaign_data: Dict) -> Dict:
        """Create voice calling campaign"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_campaigns (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                script_id TEXT,
                voicemail_id TEXT,
                target_contacts TEXT,
                schedule TEXT,
                max_attempts INTEGER,
                call_window_start TEXT,
                call_window_end TEXT,
                timezone TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        campaign_id = hashlib.md5(f"{campaign_data['name']}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO voice_campaigns 
            (id, name, description, script_id, voicemail_id, target_contacts, 
             schedule, max_attempts, call_window_start, call_window_end, timezone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign_id,
            campaign_data['name'],
            campaign_data.get('description', ''),
            campaign_data.get('script_id'),
            campaign_data.get('voicemail_id'),
            json.dumps(campaign_data['target_contacts']),
            campaign_data.get('schedule', 'immediate'),
            campaign_data.get('max_attempts', 3),
            campaign_data.get('call_window_start', '09:00'),
            campaign_data.get('call_window_end', '17:00'),
            campaign_data.get('timezone', 'UTC')
        ))
        self.db.commit()
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Voice campaign created successfully'
        }
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get voice campaign statistics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                SUM(CASE WHEN answered = 1 THEN 1 ELSE 0 END) as answered,
                SUM(CASE WHEN voicemail_detected = 1 THEN 1 ELSE 0 END) as voicemails,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(duration) as avg_duration
            FROM voice_calls
            WHERE campaign_id = ?
        ''', (campaign_id,))
        
        stats = cursor.fetchone()
        
        return {
            'campaign_id': campaign_id,
            'total_calls': stats[0] or 0,
            'answered': stats[1] or 0,
            'voicemails': stats[2] or 0,
            'completed': stats[3] or 0,
            'failed': stats[4] or 0,
            'avg_duration': round(stats[5] or 0, 2),
            'answer_rate': round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0, 2),
            'completion_rate': round((stats[3] / stats[0] * 100) if stats[0] > 0 else 0, 2)
        }
    
    def get_call_analytics(self, date_range: Dict) -> Dict:
        """Get overall call analytics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                SUM(CASE WHEN answered = 1 THEN 1 ELSE 0 END) as answered,
                SUM(CASE WHEN voicemail_detected = 1 THEN 1 ELSE 0 END) as voicemails,
                SUM(duration) as total_duration,
                AVG(duration) as avg_duration
            FROM voice_calls
            WHERE created_at BETWEEN ? AND ?
        ''', (date_range['start'], date_range['end']))
        
        stats = cursor.fetchone()
        
        # Get calls by day
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM voice_calls
            WHERE created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (date_range['start'], date_range['end']))
        
        daily_calls = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get top performers
        cursor.execute('''
            SELECT to_number, COUNT(*) as calls, AVG(duration) as avg_duration
            FROM voice_calls
            WHERE created_at BETWEEN ? AND ? AND answered = 1
            GROUP BY to_number
            ORDER BY avg_duration DESC
            LIMIT 10
        ''', (date_range['start'], date_range['end']))
        
        top_contacts = [
            {'phone': row[0], 'calls': row[1], 'avg_duration': round(row[2], 2)}
            for row in cursor.fetchall()
        ]
        
        return {
            'total_calls': stats[0] or 0,
            'answered': stats[1] or 0,
            'voicemails': stats[2] or 0,
            'total_duration': stats[3] or 0,
            'avg_duration': round(stats[4] or 0, 2),
            'answer_rate': round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0, 2),
            'daily_calls': daily_calls,
            'top_contacts': top_contacts
        }
