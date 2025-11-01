"""
Document Management & E-Signatures Module
Contract management, e-signature integration, document templates, version control
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import secrets
import hashlib

class DocumentManagement:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_document(self, document_data: Dict) -> Dict:
        """Create document"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                content TEXT,
                owner_id TEXT,
                folder_id TEXT,
                tags TEXT,
                version INTEGER DEFAULT 1,
                status TEXT DEFAULT 'draft',
                file_url TEXT,
                file_size INTEGER,
                mime_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        document_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO documents 
            (id, name, type, content, owner_id, folder_id, tags, status, 
             file_url, file_size, mime_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            document_id,
            document_data['name'],
            document_data.get('type', 'contract'),
            document_data.get('content', ''),
            document_data['owner_id'],
            document_data.get('folder_id'),
            json.dumps(document_data.get('tags', [])),
            document_data.get('status', 'draft'),
            document_data.get('file_url'),
            document_data.get('file_size', 0),
            document_data.get('mime_type', 'application/pdf')
        ))
        self.db.commit()
        
        # Create initial version
        self._create_version(document_id, 1, document_data.get('content', ''))
        
        return {
            'success': True,
            'document_id': document_id,
            'version': 1,
            'message': 'Document created successfully'
        }
    
    def update_document(self, document_id: str, updates: Dict) -> Dict:
        """Update document and create new version"""
        cursor = self.db.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        document = cursor.fetchone()
        
        if not document:
            return {'success': False, 'error': 'Document not found'}
        
        current_version = document[8]
        new_version = current_version + 1
        
        # Update document
        update_fields = []
        params = []
        
        for field in ['name', 'content', 'status', 'file_url']:
            if field in updates:
                update_fields.append(f'{field} = ?')
                params.append(updates[field])
        
        if 'tags' in updates:
            update_fields.append('tags = ?')
            params.append(json.dumps(updates['tags']))
        
        update_fields.extend(['version = ?', 'updated_at = ?'])
        params.extend([new_version, datetime.now().isoformat()])
        params.append(document_id)
        
        cursor.execute(f'''
            UPDATE documents 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        
        # Create new version
        if 'content' in updates:
            self._create_version(document_id, new_version, updates['content'])
        
        self.db.commit()
        
        return {
            'success': True,
            'document_id': document_id,
            'version': new_version,
            'message': 'Document updated successfully'
        }
    
    def create_template(self, template_data: Dict) -> Dict:
        """Create document template"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_templates (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                type TEXT,
                content TEXT,
                variables TEXT,
                tags TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        template_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO document_templates 
            (id, name, description, type, content, variables, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_id,
            template_data['name'],
            template_data.get('description', ''),
            template_data.get('type', 'contract'),
            template_data['content'],
            json.dumps(template_data.get('variables', [])),
            json.dumps(template_data.get('tags', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'template_id': template_id,
            'message': 'Template created successfully'
        }
    
    def use_template(self, template_id: str, variables: Dict, owner_id: str) -> Dict:
        """Create document from template"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM document_templates WHERE id = ?', (template_id,))
        template = cursor.fetchone()
        
        if not template:
            return {'success': False, 'error': 'Template not found'}
        
        # Replace variables in template
        content = template[4]
        for key, value in variables.items():
            content = content.replace(f'{{{{{key}}}}}', str(value))
        
        # Create document
        document_data = {
            'name': variables.get('document_name', template[1]),
            'type': template[3],
            'content': content,
            'owner_id': owner_id,
            'status': 'draft'
        }
        
        result = self.create_document(document_data)
        
        # Update template usage
        cursor.execute('''
            UPDATE document_templates 
            SET usage_count = usage_count + 1
            WHERE id = ?
        ''', (template_id,))
        self.db.commit()
        
        return result
    
    def request_signature(self, signature_request: Dict) -> Dict:
        """Request e-signature on document"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signature_requests (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                requester_id TEXT,
                signers TEXT,
                message TEXT,
                status TEXT DEFAULT 'pending',
                expires_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        request_id = secrets.token_urlsafe(16)
        
        # Set expiration (default 30 days)
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        cursor.execute('''
            INSERT INTO signature_requests 
            (id, document_id, requester_id, signers, message, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request_id,
            signature_request['document_id'],
            signature_request['requester_id'],
            json.dumps(signature_request['signers']),
            signature_request.get('message', ''),
            expires_at
        ))
        self.db.commit()
        
        # In production: Send signature request emails via DocuSign/HelloSign API
        
        return {
            'success': True,
            'request_id': request_id,
            'expires_at': expires_at,
            'message': 'Signature request sent'
        }
    
    def add_signature(self, signature_data: Dict) -> Dict:
        """Add signature to document"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signatures (
                id TEXT PRIMARY KEY,
                request_id TEXT,
                document_id TEXT,
                signer_id TEXT,
                signer_name TEXT,
                signer_email TEXT,
                signature_data TEXT,
                ip_address TEXT,
                signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        signature_id = secrets.token_urlsafe(16)
        
        # Generate signature hash
        signature_hash = hashlib.sha256(
            f"{signature_data['document_id']}{signature_data['signer_id']}{datetime.now()}".encode()
        ).hexdigest()
        
        cursor.execute('''
            INSERT INTO signatures 
            (id, request_id, document_id, signer_id, signer_name, signer_email, 
             signature_data, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signature_id,
            signature_data.get('request_id'),
            signature_data['document_id'],
            signature_data['signer_id'],
            signature_data['signer_name'],
            signature_data['signer_email'],
            signature_hash,
            signature_data.get('ip_address')
        ))
        
        # Check if all signers have signed
        if signature_data.get('request_id'):
            self._check_signature_completion(signature_data['request_id'])
        
        self.db.commit()
        
        return {
            'success': True,
            'signature_id': signature_id,
            'signature_hash': signature_hash,
            'message': 'Signature added successfully'
        }
    
    def get_signature_status(self, request_id: str) -> Dict:
        """Get signature request status"""
        cursor = self.db.cursor()
        
        cursor.execute('SELECT * FROM signature_requests WHERE id = ?', (request_id,))
        request = cursor.fetchone()
        
        if not request:
            return {'success': False, 'error': 'Request not found'}
        
        signers = json.loads(request[3])
        
        # Get signatures
        cursor.execute('''
            SELECT signer_id, signer_name, signed_at
            FROM signatures
            WHERE request_id = ?
        ''', (request_id,))
        
        signed_by = [
            {
                'signer_id': row[0],
                'signer_name': row[1],
                'signed_at': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        signed_ids = [s['signer_id'] for s in signed_by]
        pending_signers = [s for s in signers if s['signer_id'] not in signed_ids]
        
        return {
            'request_id': request_id,
            'document_id': request[1],
            'status': request[5],
            'signers_required': len(signers),
            'signers_completed': len(signed_by),
            'signed_by': signed_by,
            'pending_signers': pending_signers,
            'expires_at': request[6],
            'completed_at': request[7]
        }
    
    def get_document_history(self, document_id: str) -> List[Dict]:
        """Get document version history"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT * FROM document_versions 
            WHERE document_id = ?
            ORDER BY version DESC
        ''', (document_id,))
        
        versions = []
        for row in cursor.fetchall():
            versions.append({
                'version': row[2],
                'content': row[3],
                'created_at': row[4],
                'created_by': row[5]
            })
        
        return versions
    
    def share_document(self, share_data: Dict) -> Dict:
        """Share document with users"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_shares (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                shared_by TEXT,
                shared_with TEXT,
                permission TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        share_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO document_shares 
            (id, document_id, shared_by, shared_with, permission, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            share_id,
            share_data['document_id'],
            share_data['shared_by'],
            share_data['shared_with'],
            share_data.get('permission', 'view'),
            share_data.get('expires_at')
        ))
        self.db.commit()
        
        return {
            'success': True,
            'share_id': share_id,
            'message': 'Document shared successfully'
        }
    
    def get_document_analytics(self, owner_id: str) -> Dict:
        """Get document analytics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as drafts,
                SUM(CASE WHEN status = 'final' THEN 1 ELSE 0 END) as final,
                SUM(CASE WHEN status = 'signed' THEN 1 ELSE 0 END) as signed
            FROM documents
            WHERE owner_id = ?
        ''', (owner_id,))
        
        stats = cursor.fetchone()
        
        # Document types
        cursor.execute('''
            SELECT type, COUNT(*) as count
            FROM documents
            WHERE owner_id = ?
            GROUP BY type
        ''', (owner_id,))
        
        by_type = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Signature requests
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM signature_requests
            WHERE requester_id = ?
        ''', (owner_id,))
        
        sig_stats = cursor.fetchone()
        
        return {
            'total_documents': stats[0] or 0,
            'drafts': stats[1] or 0,
            'final': stats[2] or 0,
            'signed': stats[3] or 0,
            'by_type': by_type,
            'signature_requests': {
                'total': sig_stats[0] or 0,
                'completed': sig_stats[1] or 0,
                'pending': sig_stats[2] or 0
            }
        }
    
    def _create_version(self, document_id: str, version: int, content: str, created_by: str = None):
        """Create document version"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_versions (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                version INTEGER,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        ''')
        
        version_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO document_versions 
            (id, document_id, version, content, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (version_id, document_id, version, content, created_by))
        self.db.commit()
    
    def _check_signature_completion(self, request_id: str):
        """Check if all signatures are complete"""
        cursor = self.db.cursor()
        
        cursor.execute('SELECT signers FROM signature_requests WHERE id = ?', (request_id,))
        request = cursor.fetchone()
        
        if not request:
            return
        
        required_signers = json.loads(request[0])
        
        cursor.execute('''
            SELECT COUNT(*) FROM signatures WHERE request_id = ?
        ''', (request_id,))
        
        signed_count = cursor.fetchone()[0]
        
        if signed_count >= len(required_signers):
            cursor.execute('''
                UPDATE signature_requests 
                SET status = 'completed', completed_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), request_id))
            
            # Update document status
            cursor.execute('''
                UPDATE documents 
                SET status = 'signed'
                WHERE id = (SELECT document_id FROM signature_requests WHERE id = ?)
            ''', (request_id,))
            
            self.db.commit()
