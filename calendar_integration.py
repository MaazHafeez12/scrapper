"""
Calendar Integration & Meeting Scheduler Module
Google Calendar API, Calendly-style scheduling, automated booking
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import hashlib
import random

class CalendarIntegration:
    def __init__(self, db_connection):
        self.db = db_connection
        # In production, use Google Calendar API credentials
        self.calendar_service = None  # google.calendar().service()
        
    def create_scheduling_link(self, user_id: str, settings: Dict) -> Dict:
        """Create a Calendly-style scheduling link"""
        link_id = hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduling_links (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                description TEXT,
                duration_minutes INTEGER,
                buffer_time INTEGER,
                available_days TEXT,
                available_hours TEXT,
                timezone TEXT,
                meeting_type TEXT,
                location TEXT,
                custom_questions TEXT,
                confirmation_page TEXT,
                redirect_url TEXT,
                max_bookings_per_day INTEGER,
                min_notice_hours INTEGER,
                max_advance_days INTEGER,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO scheduling_links 
            (id, user_id, title, description, duration_minutes, buffer_time, 
             available_days, available_hours, timezone, meeting_type, location,
             custom_questions, confirmation_page, redirect_url, 
             max_bookings_per_day, min_notice_hours, max_advance_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            link_id, user_id,
            settings.get('title', 'Meeting'),
            settings.get('description', ''),
            settings.get('duration_minutes', 30),
            settings.get('buffer_time', 15),
            json.dumps(settings.get('available_days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])),
            json.dumps(settings.get('available_hours', {'start': '09:00', 'end': '17:00'})),
            settings.get('timezone', 'UTC'),
            settings.get('meeting_type', 'video'),  # video, phone, in-person
            settings.get('location', ''),
            json.dumps(settings.get('custom_questions', [])),
            settings.get('confirmation_page', ''),
            settings.get('redirect_url', ''),
            settings.get('max_bookings_per_day', 10),
            settings.get('min_notice_hours', 24),
            settings.get('max_advance_days', 60)
        ))
        self.db.commit()
        
        return {
            'link_id': link_id,
            'url': f'https://yourapp.com/schedule/{link_id}',
            'embed_code': f'<iframe src="https://yourapp.com/schedule/{link_id}" width="100%" height="800px"></iframe>',
            'settings': settings
        }
    
    def get_available_slots(self, link_id: str, date_range: Dict) -> List[Dict]:
        """Get available time slots for booking"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM scheduling_links WHERE id = ?', (link_id,))
        link = cursor.fetchone()
        
        if not link:
            return []
        
        available_days = json.loads(link[6])
        available_hours = json.loads(link[7])
        duration = link[4]
        buffer = link[5]
        
        # Get existing bookings
        cursor.execute('''
            SELECT start_time, end_time FROM meetings 
            WHERE scheduling_link_id = ? AND status != 'cancelled'
            AND start_time BETWEEN ? AND ?
        ''', (link_id, date_range['start'], date_range['end']))
        booked_slots = cursor.fetchall()
        
        # Generate available slots
        slots = []
        current_date = datetime.fromisoformat(date_range['start'])
        end_date = datetime.fromisoformat(date_range['end'])
        
        while current_date < end_date:
            day_name = current_date.strftime('%a')
            if day_name in available_days:
                # Generate slots for this day
                start_hour, start_min = map(int, available_hours['start'].split(':'))
                end_hour, end_min = map(int, available_hours['end'].split(':'))
                
                slot_time = current_date.replace(hour=start_hour, minute=start_min)
                day_end = current_date.replace(hour=end_hour, minute=end_min)
                
                while slot_time + timedelta(minutes=duration) <= day_end:
                    slot_end = slot_time + timedelta(minutes=duration)
                    
                    # Check if slot is not booked
                    is_available = True
                    for booked_start, booked_end in booked_slots:
                        booked_start_dt = datetime.fromisoformat(booked_start)
                        booked_end_dt = datetime.fromisoformat(booked_end)
                        
                        if (slot_time < booked_end_dt and slot_end > booked_start_dt):
                            is_available = False
                            break
                    
                    if is_available:
                        slots.append({
                            'start': slot_time.isoformat(),
                            'end': slot_end.isoformat(),
                            'duration': duration,
                            'available': True
                        })
                    
                    slot_time += timedelta(minutes=duration + buffer)
            
            current_date += timedelta(days=1)
        
        return slots
    
    def book_meeting(self, link_id: str, booking_data: Dict) -> Dict:
        """Book a meeting slot"""
        cursor = self.db.cursor()
        
        # Validate slot availability
        cursor.execute('SELECT * FROM scheduling_links WHERE id = ?', (link_id,))
        link = cursor.fetchone()
        
        if not link:
            return {'success': False, 'error': 'Invalid scheduling link'}
        
        # Check if slot is still available
        start_time = datetime.fromisoformat(booking_data['start_time'])
        end_time = datetime.fromisoformat(booking_data['end_time'])
        
        cursor.execute('''
            SELECT COUNT(*) FROM meetings 
            WHERE scheduling_link_id = ? AND status != 'cancelled'
            AND ((start_time <= ? AND end_time > ?) OR (start_time < ? AND end_time >= ?))
        ''', (link_id, start_time.isoformat(), start_time.isoformat(), 
              end_time.isoformat(), end_time.isoformat()))
        
        if cursor.fetchone()[0] > 0:
            return {'success': False, 'error': 'Time slot no longer available'}
        
        # Create meeting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id TEXT PRIMARY KEY,
                scheduling_link_id TEXT,
                attendee_name TEXT,
                attendee_email TEXT,
                attendee_phone TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                timezone TEXT,
                meeting_type TEXT,
                location TEXT,
                notes TEXT,
                custom_responses TEXT,
                status TEXT DEFAULT 'scheduled',
                google_event_id TEXT,
                zoom_meeting_id TEXT,
                reminder_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        meeting_id = hashlib.md5(f"{link_id}{booking_data['attendee_email']}{datetime.now()}".encode()).hexdigest()[:12]
        
        cursor.execute('''
            INSERT INTO meetings 
            (id, scheduling_link_id, attendee_name, attendee_email, attendee_phone,
             start_time, end_time, timezone, meeting_type, location, notes, custom_responses)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            meeting_id, link_id,
            booking_data['attendee_name'],
            booking_data['attendee_email'],
            booking_data.get('attendee_phone', ''),
            booking_data['start_time'],
            booking_data['end_time'],
            booking_data.get('timezone', 'UTC'),
            link[9],  # meeting_type from link
            link[10],  # location from link
            booking_data.get('notes', ''),
            json.dumps(booking_data.get('custom_responses', {}))
        ))
        self.db.commit()
        
        # In production: Create Google Calendar event
        google_event_id = self._create_google_calendar_event(link, booking_data, meeting_id)
        
        # In production: Create Zoom meeting if video
        zoom_meeting_id = None
        if link[9] == 'video':
            zoom_meeting_id = self._create_zoom_meeting(link, booking_data)
        
        # Send confirmation emails
        self._send_meeting_confirmation(link, booking_data, meeting_id)
        
        return {
            'success': True,
            'meeting_id': meeting_id,
            'google_event_id': google_event_id,
            'zoom_meeting_id': zoom_meeting_id,
            'meeting_details': {
                'title': link[2],
                'start_time': booking_data['start_time'],
                'end_time': booking_data['end_time'],
                'type': link[9],
                'location': link[10] if link[9] == 'in-person' else 'Video call link will be sent'
            }
        }
    
    def reschedule_meeting(self, meeting_id: str, new_time: Dict) -> Dict:
        """Reschedule an existing meeting"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        meeting = cursor.fetchone()
        
        if not meeting:
            return {'success': False, 'error': 'Meeting not found'}
        
        # Validate new slot
        link_id = meeting[1]
        start_time = datetime.fromisoformat(new_time['start_time'])
        end_time = datetime.fromisoformat(new_time['end_time'])
        
        cursor.execute('''
            SELECT COUNT(*) FROM meetings 
            WHERE scheduling_link_id = ? AND id != ? AND status != 'cancelled'
            AND ((start_time <= ? AND end_time > ?) OR (start_time < ? AND end_time >= ?))
        ''', (link_id, meeting_id, start_time.isoformat(), start_time.isoformat(),
              end_time.isoformat(), end_time.isoformat()))
        
        if cursor.fetchone()[0] > 0:
            return {'success': False, 'error': 'New time slot not available'}
        
        # Update meeting
        cursor.execute('''
            UPDATE meetings 
            SET start_time = ?, end_time = ?, reminder_sent = 0
            WHERE id = ?
        ''', (new_time['start_time'], new_time['end_time'], meeting_id))
        self.db.commit()
        
        # Update Google Calendar event
        self._update_google_calendar_event(meeting[13], new_time)
        
        # Send reschedule notifications
        self._send_reschedule_notification(meeting, new_time)
        
        return {
            'success': True,
            'meeting_id': meeting_id,
            'new_time': new_time
        }
    
    def cancel_meeting(self, meeting_id: str, reason: str = '') -> Dict:
        """Cancel a meeting"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        meeting = cursor.fetchone()
        
        if not meeting:
            return {'success': False, 'error': 'Meeting not found'}
        
        cursor.execute('''
            UPDATE meetings SET status = 'cancelled' WHERE id = ?
        ''', (meeting_id,))
        self.db.commit()
        
        # Cancel Google Calendar event
        if meeting[13]:
            self._cancel_google_calendar_event(meeting[13])
        
        # Send cancellation emails
        self._send_cancellation_notification(meeting, reason)
        
        return {
            'success': True,
            'meeting_id': meeting_id,
            'message': 'Meeting cancelled successfully'
        }
    
    def get_upcoming_meetings(self, user_id: str = None, days: int = 7) -> List[Dict]:
        """Get upcoming meetings"""
        cursor = self.db.cursor()
        end_date = (datetime.now() + timedelta(days=days)).isoformat()
        
        if user_id:
            cursor.execute('''
                SELECT m.* FROM meetings m
                JOIN scheduling_links l ON m.scheduling_link_id = l.id
                WHERE l.user_id = ? AND m.status = 'scheduled'
                AND m.start_time >= ? AND m.start_time <= ?
                ORDER BY m.start_time
            ''', (user_id, datetime.now().isoformat(), end_date))
        else:
            cursor.execute('''
                SELECT * FROM meetings 
                WHERE status = 'scheduled'
                AND start_time >= ? AND start_time <= ?
                ORDER BY start_time
            ''', (datetime.now().isoformat(), end_date))
        
        meetings = []
        for row in cursor.fetchall():
            meetings.append({
                'id': row[0],
                'attendee_name': row[2],
                'attendee_email': row[3],
                'start_time': row[5],
                'end_time': row[6],
                'timezone': row[7],
                'type': row[8],
                'location': row[9],
                'notes': row[10]
            })
        
        return meetings
    
    def send_meeting_reminders(self) -> Dict:
        """Send reminders for upcoming meetings"""
        cursor = self.db.cursor()
        
        # Get meetings starting in next 24 hours that haven't been reminded
        reminder_time = (datetime.now() + timedelta(hours=24)).isoformat()
        
        cursor.execute('''
            SELECT * FROM meetings 
            WHERE status = 'scheduled' AND reminder_sent = 0
            AND start_time <= ? AND start_time > ?
        ''', (reminder_time, datetime.now().isoformat()))
        
        meetings = cursor.fetchall()
        sent_count = 0
        
        for meeting in meetings:
            # Send reminder email
            self._send_meeting_reminder(meeting)
            
            # Mark as reminded
            cursor.execute('UPDATE meetings SET reminder_sent = 1 WHERE id = ?', (meeting[0],))
            sent_count += 1
        
        self.db.commit()
        
        return {
            'success': True,
            'reminders_sent': sent_count
        }
    
    def get_calendar_analytics(self, user_id: str, date_range: Dict) -> Dict:
        """Get calendar analytics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_meetings,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM meetings m
            JOIN scheduling_links l ON m.scheduling_link_id = l.id
            WHERE l.user_id = ?
            AND m.created_at BETWEEN ? AND ?
        ''', (user_id, date_range['start'], date_range['end']))
        
        stats = cursor.fetchone()
        
        # Get booking rate by day
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as bookings
            FROM meetings m
            JOIN scheduling_links l ON m.scheduling_link_id = l.id
            WHERE l.user_id = ?
            AND m.created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (user_id, date_range['start'], date_range['end']))
        
        daily_bookings = [{'date': row[0], 'bookings': row[1]} for row in cursor.fetchall()]
        
        # Most popular meeting types
        cursor.execute('''
            SELECT meeting_type, COUNT(*) as count
            FROM meetings m
            JOIN scheduling_links l ON m.scheduling_link_id = l.id
            WHERE l.user_id = ?
            AND m.created_at BETWEEN ? AND ?
            GROUP BY meeting_type
            ORDER BY count DESC
        ''', (user_id, date_range['start'], date_range['end']))
        
        meeting_types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return {
            'total_meetings': stats[0],
            'scheduled': stats[1],
            'cancelled': stats[2],
            'completed': stats[3],
            'cancellation_rate': round((stats[2] / stats[0] * 100) if stats[0] > 0 else 0, 2),
            'daily_bookings': daily_bookings,
            'meeting_types': meeting_types
        }
    
    def _create_google_calendar_event(self, link, booking_data, meeting_id) -> str:
        """Create Google Calendar event (mock implementation)"""
        # In production: Use Google Calendar API
        # event = self.calendar_service.events().insert(calendarId='primary', body=event_data).execute()
        return f"gcal_{meeting_id}"
    
    def _create_zoom_meeting(self, link, booking_data) -> str:
        """Create Zoom meeting (mock implementation)"""
        # In production: Use Zoom API
        return f"zoom_{random.randint(100000000, 999999999)}"
    
    def _update_google_calendar_event(self, event_id, new_time):
        """Update Google Calendar event"""
        # In production: Use Google Calendar API
        pass
    
    def _cancel_google_calendar_event(self, event_id):
        """Cancel Google Calendar event"""
        # In production: Use Google Calendar API
        pass
    
    def _send_meeting_confirmation(self, link, booking_data, meeting_id):
        """Send meeting confirmation email"""
        # In production: Send email with meeting details
        pass
    
    def _send_reschedule_notification(self, meeting, new_time):
        """Send reschedule notification"""
        # In production: Send email notification
        pass
    
    def _send_cancellation_notification(self, meeting, reason):
        """Send cancellation notification"""
        # In production: Send email notification
        pass
    
    def _send_meeting_reminder(self, meeting):
        """Send meeting reminder"""
        # In production: Send reminder email/SMS
        pass
