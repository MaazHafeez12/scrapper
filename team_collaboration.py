"""
Team Collaboration & Management Module
Team workspace, task assignments, comments, mentions, activity feeds, notifications
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import secrets
import re

class TeamCollaboration:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_workspace(self, workspace_data: Dict) -> Dict:
        """Create team workspace"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                owner_id TEXT,
                settings TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        workspace_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workspaces 
            (id, name, description, owner_id, settings)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            workspace_id,
            workspace_data['name'],
            workspace_data.get('description', ''),
            workspace_data['owner_id'],
            json.dumps(workspace_data.get('settings', {}))
        ))
        self.db.commit()
        
        # Add owner as admin
        self.add_member(workspace_id, workspace_data['owner_id'], 'admin')
        
        return {
            'success': True,
            'workspace_id': workspace_id,
            'message': 'Workspace created successfully'
        }
    
    def add_member(self, workspace_id: str, user_id: str, role: str = 'member') -> Dict:
        """Add member to workspace"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workspace_members (
                id TEXT PRIMARY KEY,
                workspace_id TEXT,
                user_id TEXT,
                role TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        member_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workspace_members 
            (id, workspace_id, user_id, role)
            VALUES (?, ?, ?, ?)
        ''', (member_id, workspace_id, user_id, role))
        self.db.commit()
        
        # Log activity
        self._log_activity(workspace_id, user_id, 'member_added', 
                          {'member_id': member_id, 'role': role})
        
        return {
            'success': True,
            'member_id': member_id,
            'message': 'Member added successfully'
        }
    
    def create_task(self, task_data: Dict) -> Dict:
        """Create task"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                workspace_id TEXT,
                title TEXT,
                description TEXT,
                assigned_to TEXT,
                created_by TEXT,
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                due_date TIMESTAMP,
                tags TEXT,
                attachments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        task_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO tasks 
            (id, workspace_id, title, description, assigned_to, created_by, 
             status, priority, due_date, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            task_data['workspace_id'],
            task_data['title'],
            task_data.get('description', ''),
            task_data.get('assigned_to'),
            task_data['created_by'],
            task_data.get('status', 'todo'),
            task_data.get('priority', 'medium'),
            task_data.get('due_date'),
            json.dumps(task_data.get('tags', []))
        ))
        self.db.commit()
        
        # Log activity
        self._log_activity(task_data['workspace_id'], task_data['created_by'], 
                          'task_created', {'task_id': task_id, 'title': task_data['title']})
        
        # Send notification if assigned
        if task_data.get('assigned_to'):
            self._send_notification(
                task_data['assigned_to'],
                'task_assigned',
                f"You've been assigned: {task_data['title']}",
                {'task_id': task_id}
            )
        
        return {
            'success': True,
            'task_id': task_id,
            'message': 'Task created successfully'
        }
    
    def update_task(self, task_id: str, updates: Dict) -> Dict:
        """Update task"""
        cursor = self.db.cursor()
        
        # Get current task
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return {'success': False, 'error': 'Task not found'}
        
        # Build update query
        update_fields = []
        params = []
        
        for field in ['title', 'description', 'assigned_to', 'status', 'priority', 'due_date']:
            if field in updates:
                update_fields.append(f'{field} = ?')
                params.append(updates[field])
        
        if 'tags' in updates:
            update_fields.append('tags = ?')
            params.append(json.dumps(updates['tags']))
        
        update_fields.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        
        params.append(task_id)
        
        cursor.execute(f'''
            UPDATE tasks 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        self.db.commit()
        
        # Log activity
        self._log_activity(task[1], updates.get('updated_by', task[6]), 
                          'task_updated', {'task_id': task_id, 'updates': list(updates.keys())})
        
        return {
            'success': True,
            'task_id': task_id,
            'message': 'Task updated successfully'
        }
    
    def add_comment(self, comment_data: Dict) -> Dict:
        """Add comment to task"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                user_id TEXT,
                content TEXT,
                mentions TEXT,
                attachments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        comment_id = secrets.token_urlsafe(16)
        
        # Extract mentions (@username)
        mentions = self._extract_mentions(comment_data['content'])
        
        cursor.execute('''
            INSERT INTO comments 
            (id, task_id, user_id, content, mentions)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            comment_id,
            comment_data['task_id'],
            comment_data['user_id'],
            comment_data['content'],
            json.dumps(mentions)
        ))
        self.db.commit()
        
        # Send notifications to mentioned users
        for mention in mentions:
            self._send_notification(
                mention,
                'mentioned',
                f"You were mentioned in a comment",
                {'comment_id': comment_id, 'task_id': comment_data['task_id']}
            )
        
        return {
            'success': True,
            'comment_id': comment_id,
            'mentions': mentions,
            'message': 'Comment added successfully'
        }
    
    def get_activity_feed(self, workspace_id: str, limit: int = 50) -> List[Dict]:
        """Get workspace activity feed"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT * FROM activity_logs 
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (workspace_id, limit))
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'id': row[0],
                'workspace_id': row[1],
                'user_id': row[2],
                'action': row[3],
                'details': json.loads(row[4]) if row[4] else {},
                'created_at': row[5]
            })
        
        return activities
    
    def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        """Get user notifications"""
        cursor = self.db.cursor()
        
        query = '''
            SELECT * FROM notifications 
            WHERE user_id = ?
        '''
        
        if unread_only:
            query += ' AND read = 0'
        
        query += ' ORDER BY created_at DESC LIMIT 50'
        
        cursor.execute(query, (user_id,))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row[0],
                'user_id': row[1],
                'type': row[2],
                'message': row[3],
                'data': json.loads(row[4]) if row[4] else {},
                'read': row[5] == 1,
                'created_at': row[6]
            })
        
        return notifications
    
    def mark_notification_read(self, notification_id: str) -> Dict:
        """Mark notification as read"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE notifications 
            SET read = 1
            WHERE id = ?
        ''', (notification_id,))
        self.db.commit()
        
        return {
            'success': True,
            'notification_id': notification_id
        }
    
    def get_team_analytics(self, workspace_id: str) -> Dict:
        """Get team analytics"""
        cursor = self.db.cursor()
        
        # Task statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) as todo
            FROM tasks
            WHERE workspace_id = ?
        ''', (workspace_id,))
        
        task_stats = cursor.fetchone()
        
        # Member activity
        cursor.execute('''
            SELECT user_id, COUNT(*) as activity_count
            FROM activity_logs
            WHERE workspace_id = ?
            AND created_at >= ?
            GROUP BY user_id
            ORDER BY activity_count DESC
        ''', (workspace_id, (datetime.now() - timedelta(days=7)).isoformat()))
        
        member_activity = [
            {'user_id': row[0], 'activity_count': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Task completion rate by assignee
        cursor.execute('''
            SELECT 
                assigned_to,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE workspace_id = ? AND assigned_to IS NOT NULL
            GROUP BY assigned_to
        ''', (workspace_id,))
        
        completion_by_user = [
            {
                'user_id': row[0],
                'total_tasks': row[1],
                'completed': row[2],
                'completion_rate': round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2)
            }
            for row in cursor.fetchall()
        ]
        
        return {
            'workspace_id': workspace_id,
            'tasks': {
                'total': task_stats[0] or 0,
                'completed': task_stats[1] or 0,
                'in_progress': task_stats[2] or 0,
                'todo': task_stats[3] or 0,
                'completion_rate': round((task_stats[1] / task_stats[0] * 100) if task_stats[0] > 0 else 0, 2)
            },
            'member_activity': member_activity,
            'completion_by_user': completion_by_user
        }
    
    def search_workspace(self, workspace_id: str, query: str) -> Dict:
        """Search workspace content"""
        cursor = self.db.cursor()
        
        search_pattern = f'%{query}%'
        
        # Search tasks
        cursor.execute('''
            SELECT id, title, description, status
            FROM tasks
            WHERE workspace_id = ? 
            AND (title LIKE ? OR description LIKE ?)
            LIMIT 20
        ''', (workspace_id, search_pattern, search_pattern))
        
        tasks = [
            {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'status': row[3],
                'type': 'task'
            }
            for row in cursor.fetchall()
        ]
        
        # Search comments
        cursor.execute('''
            SELECT c.id, c.content, c.task_id
            FROM comments c
            JOIN tasks t ON c.task_id = t.id
            WHERE t.workspace_id = ? AND c.content LIKE ?
            LIMIT 20
        ''', (workspace_id, search_pattern))
        
        comments = [
            {
                'id': row[0],
                'content': row[1],
                'task_id': row[2],
                'type': 'comment'
            }
            for row in cursor.fetchall()
        ]
        
        return {
            'success': True,
            'query': query,
            'results': {
                'tasks': tasks,
                'comments': comments,
                'total': len(tasks) + len(comments)
            }
        }
    
    def _log_activity(self, workspace_id: str, user_id: str, action: str, details: Dict):
        """Log workspace activity"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id TEXT PRIMARY KEY,
                workspace_id TEXT,
                user_id TEXT,
                action TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        activity_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO activity_logs 
            (id, workspace_id, user_id, action, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (activity_id, workspace_id, user_id, action, json.dumps(details)))
        self.db.commit()
    
    def _send_notification(self, user_id: str, notification_type: str, 
                          message: str, data: Dict):
        """Send notification to user"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                message TEXT,
                data TEXT,
                read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        notification_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO notifications 
            (id, user_id, type, message, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (notification_id, user_id, notification_type, message, json.dumps(data)))
        self.db.commit()
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        pattern = r'@(\w+)'
        mentions = re.findall(pattern, content)
        return list(set(mentions))  # Remove duplicates
