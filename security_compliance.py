"""
Advanced Security & Compliance Module
2FA, audit logs, GDPR compliance, data encryption, role-based access control
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import hashlib
import secrets
import base64

class SecurityCompliance:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def setup_2fa(self, user_id: str, method: str = 'totp') -> Dict:
        """Setup two-factor authentication"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_2fa (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                method TEXT,
                secret_key TEXT,
                backup_codes TEXT,
                enabled INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Generate TOTP secret
        secret = secrets.token_urlsafe(32)
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_2fa 
            (id, user_id, method, secret_key, backup_codes, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, user_id, method, secret,
            json.dumps(backup_codes), 0
        ))
        self.db.commit()
        
        return {
            'success': True,
            'secret': secret,
            'backup_codes': backup_codes,
            'qr_code_url': f'otpauth://totp/BusinessDev:{user_id}?secret={secret}&issuer=BusinessDev',
            'message': '2FA setup initiated. Verify to enable.'
        }
    
    def verify_2fa(self, user_id: str, code: str) -> Dict:
        """Verify 2FA code"""
        cursor = self.db.cursor()
        cursor.execute('SELECT secret_key, backup_codes FROM user_2fa WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return {'success': False, 'error': '2FA not setup'}
        
        secret, backup_codes_json = row
        backup_codes = json.loads(backup_codes_json)
        
        # In production: Verify TOTP code using pyotp
        # import pyotp
        # totp = pyotp.TOTP(secret)
        # is_valid = totp.verify(code)
        
        # Mock verification (accept any 6-digit code or backup code)
        is_valid = len(code) == 6 or code in backup_codes
        
        if is_valid:
            cursor.execute('''
                UPDATE user_2fa 
                SET enabled = 1, verified = 1
                WHERE user_id = ?
            ''', (user_id,))
            
            # Remove used backup code
            if code in backup_codes:
                backup_codes.remove(code)
                cursor.execute('''
                    UPDATE user_2fa SET backup_codes = ? WHERE user_id = ?
                ''', (json.dumps(backup_codes), user_id))
            
            self.db.commit()
            return {'success': True, 'message': '2FA verified successfully'}
        
        return {'success': False, 'error': 'Invalid 2FA code'}
    
    def log_audit_event(self, event_data: Dict) -> Dict:
        """Log audit event"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                event_type TEXT,
                resource_type TEXT,
                resource_id TEXT,
                action TEXT,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        log_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO audit_logs 
            (id, user_id, event_type, resource_type, resource_id, action, 
             ip_address, user_agent, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            event_data.get('user_id'),
            event_data['event_type'],
            event_data.get('resource_type'),
            event_data.get('resource_id'),
            event_data['action'],
            event_data.get('ip_address'),
            event_data.get('user_agent'),
            json.dumps(event_data.get('details', {}))
        ))
        self.db.commit()
        
        return {'success': True, 'log_id': log_id}
    
    def get_audit_logs(self, filters: Dict) -> List[Dict]:
        """Get audit logs with filters"""
        cursor = self.db.cursor()
        
        query = 'SELECT * FROM audit_logs WHERE 1=1'
        params = []
        
        if 'user_id' in filters:
            query += ' AND user_id = ?'
            params.append(filters['user_id'])
        
        if 'event_type' in filters:
            query += ' AND event_type = ?'
            params.append(filters['event_type'])
        
        if 'start_date' in filters:
            query += ' AND timestamp >= ?'
            params.append(filters['start_date'])
        
        if 'end_date' in filters:
            query += ' AND timestamp <= ?'
            params.append(filters['end_date'])
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(filters.get('limit', 100))
        
        cursor.execute(query, params)
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'user_id': row[1],
                'event_type': row[2],
                'resource_type': row[3],
                'resource_id': row[4],
                'action': row[5],
                'ip_address': row[6],
                'user_agent': row[7],
                'details': json.loads(row[8]) if row[8] else {},
                'timestamp': row[9]
            })
        
        return logs
    
    def create_role(self, role_data: Dict) -> Dict:
        """Create user role with permissions"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        role_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO roles (id, name, description, permissions)
            VALUES (?, ?, ?, ?)
        ''', (
            role_id,
            role_data['name'],
            role_data.get('description', ''),
            json.dumps(role_data.get('permissions', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'role_id': role_id,
            'message': 'Role created successfully'
        }
    
    def assign_role(self, user_id: str, role_id: str) -> Dict:
        """Assign role to user"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                role_id TEXT,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        assignment_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO user_roles (id, user_id, role_id)
            VALUES (?, ?, ?)
        ''', (assignment_id, user_id, role_id))
        self.db.commit()
        
        return {
            'success': True,
            'assignment_id': assignment_id,
            'message': 'Role assigned successfully'
        }
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT r.permissions 
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
        ''', (user_id,))
        
        for row in cursor.fetchall():
            permissions = json.loads(row[0])
            if permission in permissions or '*' in permissions:
                return True
        
        return False
    
    def export_data(self, user_id: str, data_types: List[str]) -> Dict:
        """Export user data (GDPR compliance)"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_exports (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                data_types TEXT,
                status TEXT DEFAULT 'processing',
                file_url TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        export_id = secrets.token_urlsafe(16)
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        cursor.execute('''
            INSERT INTO data_exports 
            (id, user_id, data_types, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (
            export_id, user_id,
            json.dumps(data_types),
            expires_at
        ))
        self.db.commit()
        
        # In production: Process export asynchronously
        # export_service.process_export(export_id, user_id, data_types)
        
        return {
            'success': True,
            'export_id': export_id,
            'status': 'processing',
            'estimated_time': '5-10 minutes',
            'expires_at': expires_at
        }
    
    def delete_user_data(self, user_id: str, data_types: List[str] = None) -> Dict:
        """Delete user data (GDPR right to be forgotten)"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_deletions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                data_types TEXT,
                status TEXT DEFAULT 'pending',
                requested_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        deletion_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO data_deletions 
            (id, user_id, data_types, requested_at)
            VALUES (?, ?, ?, ?)
        ''', (
            deletion_id, user_id,
            json.dumps(data_types if data_types else ['all']),
            datetime.now().isoformat()
        ))
        self.db.commit()
        
        return {
            'success': True,
            'deletion_id': deletion_id,
            'status': 'pending',
            'message': 'Data deletion request submitted'
        }
    
    def encrypt_sensitive_data(self, data: str, key: str = None) -> str:
        """Encrypt sensitive data"""
        # In production: Use proper encryption (AES-256, Fernet, etc.)
        # from cryptography.fernet import Fernet
        # cipher = Fernet(key)
        # return cipher.encrypt(data.encode()).decode()
        
        # Mock encryption (base64 for demo)
        return base64.b64encode(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str, key: str = None) -> str:
        """Decrypt sensitive data"""
        # In production: Use proper decryption
        # from cryptography.fernet import Fernet
        # cipher = Fernet(key)
        # return cipher.decrypt(encrypted_data.encode()).decode()
        
        # Mock decryption
        return base64.b64decode(encrypted_data.encode()).decode()
    
    def get_compliance_report(self, date_range: Dict) -> Dict:
        """Generate compliance report"""
        cursor = self.db.cursor()
        
        # Get security events
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM audit_logs
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY event_type
        ''', (date_range['start'], date_range['end']))
        
        security_events = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get 2FA adoption
        cursor.execute('''
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_2fa
            FROM user_2fa
        ''')
        
        twofa_stats = cursor.fetchone()
        
        # Get data exports
        cursor.execute('''
            SELECT COUNT(*) FROM data_exports
            WHERE created_at BETWEEN ? AND ?
        ''', (date_range['start'], date_range['end']))
        
        export_count = cursor.fetchone()[0]
        
        # Get data deletions
        cursor.execute('''
            SELECT COUNT(*) FROM data_deletions
            WHERE requested_at BETWEEN ? AND ?
        ''', (date_range['start'], date_range['end']))
        
        deletion_count = cursor.fetchone()[0]
        
        return {
            'report_period': date_range,
            'security_events': security_events,
            'two_factor_auth': {
                'total_users': twofa_stats[0] or 0,
                'enabled': twofa_stats[1] or 0,
                'adoption_rate': round((twofa_stats[1] / twofa_stats[0] * 100) if twofa_stats[0] > 0 else 0, 2)
            },
            'gdpr_compliance': {
                'data_exports': export_count,
                'data_deletions': deletion_count
            }
        }
    
    def set_data_retention_policy(self, policy_data: Dict) -> Dict:
        """Set data retention policy"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS retention_policies (
                id TEXT PRIMARY KEY,
                name TEXT,
                data_type TEXT,
                retention_days INTEGER,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        policy_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO retention_policies 
            (id, name, data_type, retention_days)
            VALUES (?, ?, ?, ?)
        ''', (
            policy_id,
            policy_data['name'],
            policy_data['data_type'],
            policy_data['retention_days']
        ))
        self.db.commit()
        
        return {
            'success': True,
            'policy_id': policy_id,
            'message': 'Retention policy created'
        }
    
    def enforce_retention_policies(self) -> Dict:
        """Enforce data retention policies"""
        cursor = self.db.cursor()
        
        cursor.execute('SELECT * FROM retention_policies WHERE active = 1')
        policies = cursor.fetchall()
        
        deleted_count = 0
        
        for policy in policies:
            policy_id, name, data_type, retention_days, active, created_at = policy
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
            
            # Delete old data based on type
            if data_type == 'audit_logs':
                cursor.execute('DELETE FROM audit_logs WHERE timestamp < ?', (cutoff_date,))
                deleted_count += cursor.rowcount
            elif data_type == 'email_campaigns':
                cursor.execute('DELETE FROM email_campaigns WHERE created_at < ?', (cutoff_date,))
                deleted_count += cursor.rowcount
            # Add more data types as needed
        
        self.db.commit()
        
        return {
            'success': True,
            'policies_enforced': len(policies),
            'records_deleted': deleted_count
        }
