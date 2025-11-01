"""
Webhook System & Real-time Integrations Module
Webhook management, real-time events, custom integrations, payload transformation
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import hashlib
import secrets
import requests
import hmac

class WebhookSystem:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_webhook(self, webhook_data: Dict) -> Dict:
        """Create webhook endpoint"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT,
                url TEXT,
                events TEXT,
                secret TEXT,
                active INTEGER DEFAULT 1,
                retry_enabled INTEGER DEFAULT 1,
                max_retries INTEGER DEFAULT 3,
                headers TEXT,
                payload_template TEXT,
                last_triggered TIMESTAMP,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        webhook_id = secrets.token_urlsafe(16)
        secret = secrets.token_urlsafe(32)
        
        cursor.execute('''
            INSERT INTO webhooks 
            (id, user_id, name, url, events, secret, retry_enabled, max_retries, 
             headers, payload_template)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            webhook_id,
            webhook_data['user_id'],
            webhook_data['name'],
            webhook_data['url'],
            json.dumps(webhook_data.get('events', [])),
            secret,
            1 if webhook_data.get('retry_enabled', True) else 0,
            webhook_data.get('max_retries', 3),
            json.dumps(webhook_data.get('headers', {})),
            webhook_data.get('payload_template', '{}')
        ))
        self.db.commit()
        
        return {
            'success': True,
            'webhook_id': webhook_id,
            'secret': secret,
            'message': 'Webhook created successfully'
        }
    
    def trigger_webhook(self, webhook_id: str, event: str, payload: Dict) -> Dict:
        """Trigger webhook with event data"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM webhooks WHERE id = ? AND active = 1', (webhook_id,))
        webhook = cursor.fetchone()
        
        if not webhook:
            return {'success': False, 'error': 'Webhook not found or inactive'}
        
        webhook_url = webhook[3]
        events = json.loads(webhook[4])
        secret = webhook[5]
        headers = json.loads(webhook[10])
        
        # Check if event is subscribed
        if event not in events:
            return {'success': False, 'error': 'Event not subscribed'}
        
        # Create delivery
        delivery_id = self._create_delivery(webhook_id, event, payload)
        
        # Transform payload if template exists
        transformed_payload = self._transform_payload(webhook[11], payload)
        
        # Generate signature
        signature = self._generate_signature(transformed_payload, secret)
        
        # Prepare headers
        request_headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': event,
            'X-Webhook-Delivery': delivery_id,
            **headers
        }
        
        # Send webhook
        try:
            response = requests.post(
                webhook_url,
                json=transformed_payload,
                headers=request_headers,
                timeout=10
            )
            
            success = response.status_code in [200, 201, 202, 204]
            
            self._update_delivery(delivery_id, 'success' if success else 'failed', 
                                response.status_code, response.text)
            
            # Update webhook stats
            if success:
                cursor.execute('''
                    UPDATE webhooks 
                    SET success_count = success_count + 1, last_triggered = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), webhook_id))
            else:
                cursor.execute('''
                    UPDATE webhooks 
                    SET failure_count = failure_count + 1
                    WHERE id = ?
                ''', (webhook_id,))
            
            self.db.commit()
            
            return {
                'success': success,
                'delivery_id': delivery_id,
                'status_code': response.status_code,
                'response': response.text[:500]
            }
            
        except Exception as e:
            self._update_delivery(delivery_id, 'failed', 0, str(e))
            cursor.execute('''
                UPDATE webhooks 
                SET failure_count = failure_count + 1
                WHERE id = ?
            ''', (webhook_id,))
            self.db.commit()
            
            return {
                'success': False,
                'delivery_id': delivery_id,
                'error': str(e)
            }
    
    def broadcast_event(self, user_id: str, event: str, payload: Dict) -> Dict:
        """Broadcast event to all subscribed webhooks"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id FROM webhooks 
            WHERE user_id = ? AND active = 1
        ''', (user_id,))
        
        webhooks = cursor.fetchall()
        results = []
        
        for webhook in webhooks:
            webhook_id = webhook[0]
            result = self.trigger_webhook(webhook_id, event, payload)
            results.append({
                'webhook_id': webhook_id,
                'success': result['success'],
                'delivery_id': result.get('delivery_id')
            })
        
        return {
            'success': True,
            'total_webhooks': len(webhooks),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }
    
    def retry_failed_delivery(self, delivery_id: str) -> Dict:
        """Retry failed webhook delivery"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM webhook_deliveries WHERE id = ?', (delivery_id,))
        delivery = cursor.fetchone()
        
        if not delivery:
            return {'success': False, 'error': 'Delivery not found'}
        
        webhook_id = delivery[1]
        event = delivery[2]
        payload = json.loads(delivery[3])
        
        return self.trigger_webhook(webhook_id, event, payload)
    
    def get_webhook_logs(self, webhook_id: str, limit: int = 50) -> List[Dict]:
        """Get webhook delivery logs"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT * FROM webhook_deliveries 
            WHERE webhook_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (webhook_id, limit))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'delivery_id': row[0],
                'webhook_id': row[1],
                'event': row[2],
                'payload': json.loads(row[3]),
                'status': row[4],
                'response_code': row[5],
                'response_body': row[6],
                'attempt': row[7],
                'created_at': row[8]
            })
        
        return logs
    
    def create_integration(self, integration_data: Dict) -> Dict:
        """Create custom integration"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integrations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT,
                type TEXT,
                config TEXT,
                auth_type TEXT,
                credentials TEXT,
                active INTEGER DEFAULT 1,
                last_sync TIMESTAMP,
                sync_frequency INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        integration_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO integrations 
            (id, user_id, name, type, config, auth_type, credentials, sync_frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            integration_id,
            integration_data['user_id'],
            integration_data['name'],
            integration_data['type'],
            json.dumps(integration_data.get('config', {})),
            integration_data.get('auth_type', 'api_key'),
            json.dumps(integration_data.get('credentials', {})),
            integration_data.get('sync_frequency', 3600)
        ))
        self.db.commit()
        
        return {
            'success': True,
            'integration_id': integration_id,
            'message': 'Integration created successfully'
        }
    
    def sync_integration(self, integration_id: str) -> Dict:
        """Sync data with external integration"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM integrations WHERE id = ?', (integration_id,))
        integration = cursor.fetchone()
        
        if not integration:
            return {'success': False, 'error': 'Integration not found'}
        
        integration_type = integration[3]
        config = json.loads(integration[4])
        credentials = json.loads(integration[6])
        
        # In production: Implement actual integration sync
        # if integration_type == 'zapier':
        #     sync_zapier(config, credentials)
        # elif integration_type == 'make':
        #     sync_make(config, credentials)
        
        cursor.execute('''
            UPDATE integrations 
            SET last_sync = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), integration_id))
        self.db.commit()
        
        return {
            'success': True,
            'integration_id': integration_id,
            'synced_at': datetime.now().isoformat()
        }
    
    def create_event_subscription(self, subscription_data: Dict) -> Dict:
        """Create event subscription for real-time updates"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                event_type TEXT,
                filters TEXT,
                callback_url TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        subscription_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO event_subscriptions 
            (id, user_id, event_type, filters, callback_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            subscription_id,
            subscription_data['user_id'],
            subscription_data['event_type'],
            json.dumps(subscription_data.get('filters', {})),
            subscription_data['callback_url']
        ))
        self.db.commit()
        
        return {
            'success': True,
            'subscription_id': subscription_id,
            'message': 'Event subscription created'
        }
    
    def get_webhook_stats(self, user_id: str) -> Dict:
        """Get webhook statistics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active,
                SUM(success_count) as total_success,
                SUM(failure_count) as total_failures
            FROM webhooks
            WHERE user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT event, COUNT(*) as count
            FROM webhook_deliveries wd
            JOIN webhooks w ON wd.webhook_id = w.id
            WHERE w.user_id = ?
            GROUP BY event
            ORDER BY count DESC
            LIMIT 10
        ''', (user_id,))
        
        top_events = [{'event': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return {
            'total_webhooks': stats[0] or 0,
            'active_webhooks': stats[1] or 0,
            'total_deliveries': (stats[2] or 0) + (stats[3] or 0),
            'successful_deliveries': stats[2] or 0,
            'failed_deliveries': stats[3] or 0,
            'success_rate': round((stats[2] / ((stats[2] or 0) + (stats[3] or 0)) * 100) if ((stats[2] or 0) + (stats[3] or 0)) > 0 else 0, 2),
            'top_events': top_events
        }
    
    def _create_delivery(self, webhook_id: str, event: str, payload: Dict) -> str:
        """Create webhook delivery record"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_deliveries (
                id TEXT PRIMARY KEY,
                webhook_id TEXT,
                event TEXT,
                payload TEXT,
                status TEXT,
                response_code INTEGER,
                response_body TEXT,
                attempt INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        delivery_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO webhook_deliveries 
            (id, webhook_id, event, payload, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            delivery_id, webhook_id, event,
            json.dumps(payload), 'pending'
        ))
        self.db.commit()
        
        return delivery_id
    
    def _update_delivery(self, delivery_id: str, status: str, 
                        response_code: int, response_body: str):
        """Update delivery status"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE webhook_deliveries 
            SET status = ?, response_code = ?, response_body = ?
            WHERE id = ?
        ''', (status, response_code, response_body[:1000], delivery_id))
        self.db.commit()
    
    def _transform_payload(self, template: str, data: Dict) -> Dict:
        """Transform payload using template"""
        if not template or template == '{}':
            return data
        
        # In production: Implement jinja2 or similar templating
        # template_obj = Template(template)
        # return json.loads(template_obj.render(**data))
        
        return data
    
    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
