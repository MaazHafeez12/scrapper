"""
Advanced Workflow Automation Builder Module
Visual workflow builder, conditional logic, triggers, actions, custom automation flows
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import secrets

class WorkflowAutomation:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_workflow(self, workflow_data: Dict) -> Dict:
        """Create automation workflow"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT,
                description TEXT,
                trigger_type TEXT,
                trigger_config TEXT,
                nodes TEXT,
                edges TEXT,
                active INTEGER DEFAULT 1,
                execution_count INTEGER DEFAULT 0,
                last_executed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        workflow_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workflows 
            (id, user_id, name, description, trigger_type, trigger_config, nodes, edges)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_id,
            workflow_data['user_id'],
            workflow_data['name'],
            workflow_data.get('description', ''),
            workflow_data['trigger_type'],
            json.dumps(workflow_data.get('trigger_config', {})),
            json.dumps(workflow_data.get('nodes', [])),
            json.dumps(workflow_data.get('edges', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'workflow_id': workflow_id,
            'message': 'Workflow created successfully'
        }
    
    def execute_workflow(self, workflow_id: str, trigger_data: Dict = None) -> Dict:
        """Execute workflow"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM workflows WHERE id = ? AND active = 1', (workflow_id,))
        workflow = cursor.fetchone()
        
        if not workflow:
            return {'success': False, 'error': 'Workflow not found or inactive'}
        
        # Create execution record
        execution_id = self._create_execution(workflow_id, trigger_data or {})
        
        nodes = json.loads(workflow[7])
        edges = json.loads(workflow[8])
        
        # Execute workflow logic
        try:
            results = self._process_workflow_nodes(nodes, edges, trigger_data or {}, execution_id)
            
            self._update_execution(execution_id, 'completed', results)
            
            cursor.execute('''
                UPDATE workflows 
                SET execution_count = execution_count + 1, last_executed = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), workflow_id))
            self.db.commit()
            
            return {
                'success': True,
                'execution_id': execution_id,
                'results': results
            }
            
        except Exception as e:
            self._update_execution(execution_id, 'failed', {'error': str(e)})
            return {
                'success': False,
                'execution_id': execution_id,
                'error': str(e)
            }
    
    def create_trigger(self, trigger_data: Dict) -> Dict:
        """Create workflow trigger"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_triggers (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                type TEXT,
                config TEXT,
                conditions TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        trigger_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workflow_triggers 
            (id, workflow_id, type, config, conditions)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            trigger_id,
            trigger_data['workflow_id'],
            trigger_data['type'],  # webhook, schedule, event, manual
            json.dumps(trigger_data.get('config', {})),
            json.dumps(trigger_data.get('conditions', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'trigger_id': trigger_id,
            'message': 'Trigger created successfully'
        }
    
    def add_action(self, action_data: Dict) -> Dict:
        """Add action to workflow"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_actions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                name TEXT,
                type TEXT,
                config TEXT,
                position INTEGER,
                depends_on TEXT,
                conditions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        action_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workflow_actions 
            (id, workflow_id, name, type, config, position, depends_on, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            action_id,
            action_data['workflow_id'],
            action_data['name'],
            action_data['type'],  # email, slack, webhook, crm, api_call, delay
            json.dumps(action_data.get('config', {})),
            action_data.get('position', 0),
            json.dumps(action_data.get('depends_on', [])),
            json.dumps(action_data.get('conditions', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'action_id': action_id,
            'message': 'Action added successfully'
        }
    
    def add_condition(self, condition_data: Dict) -> Dict:
        """Add conditional logic to workflow"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_conditions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                node_id TEXT,
                operator TEXT,
                field TEXT,
                value TEXT,
                true_path TEXT,
                false_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        condition_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workflow_conditions 
            (id, workflow_id, node_id, operator, field, value, true_path, false_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            condition_id,
            condition_data['workflow_id'],
            condition_data['node_id'],
            condition_data['operator'],  # equals, not_equals, contains, greater_than, etc.
            condition_data['field'],
            condition_data['value'],
            condition_data.get('true_path'),
            condition_data.get('false_path')
        ))
        self.db.commit()
        
        return {
            'success': True,
            'condition_id': condition_id,
            'message': 'Condition added successfully'
        }
    
    def create_template(self, template_data: Dict) -> Dict:
        """Create workflow template"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_templates (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                category TEXT,
                workflow_config TEXT,
                tags TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        template_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workflow_templates 
            (id, name, description, category, workflow_config, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            template_id,
            template_data['name'],
            template_data.get('description', ''),
            template_data.get('category', 'general'),
            json.dumps(template_data['workflow_config']),
            json.dumps(template_data.get('tags', []))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'template_id': template_id,
            'message': 'Template created successfully'
        }
    
    def use_template(self, template_id: str, user_id: str, customizations: Dict = None) -> Dict:
        """Create workflow from template"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM workflow_templates WHERE id = ?', (template_id,))
        template = cursor.fetchone()
        
        if not template:
            return {'success': False, 'error': 'Template not found'}
        
        workflow_config = json.loads(template[4])
        
        # Apply customizations
        if customizations:
            workflow_config.update(customizations)
        
        workflow_config['user_id'] = user_id
        
        result = self.create_workflow(workflow_config)
        
        # Update template usage
        cursor.execute('''
            UPDATE workflow_templates 
            SET usage_count = usage_count + 1
            WHERE id = ?
        ''', (template_id,))
        self.db.commit()
        
        return result
    
    def get_workflow_analytics(self, workflow_id: str) -> Dict:
        """Get workflow analytics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(CAST((julianday(completed_at) - julianday(started_at)) * 86400000 AS INTEGER)) as avg_duration
            FROM workflow_executions
            WHERE workflow_id = ?
        ''', (workflow_id,))
        
        stats = cursor.fetchone()
        
        # Get recent executions
        cursor.execute('''
            SELECT started_at, completed_at, status
            FROM workflow_executions
            WHERE workflow_id = ?
            ORDER BY started_at DESC
            LIMIT 10
        ''', (workflow_id,))
        
        recent = [
            {
                'started_at': row[0],
                'completed_at': row[1],
                'status': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            'workflow_id': workflow_id,
            'total_executions': stats[0] or 0,
            'successful': stats[1] or 0,
            'failed': stats[2] or 0,
            'success_rate': round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0, 2),
            'avg_duration_ms': round(stats[3] or 0, 2),
            'recent_executions': recent
        }
    
    def get_workflow_logs(self, workflow_id: str, limit: int = 50) -> List[Dict]:
        """Get workflow execution logs"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT * FROM workflow_executions 
            WHERE workflow_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        ''', (workflow_id, limit))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'execution_id': row[0],
                'workflow_id': row[1],
                'trigger_data': json.loads(row[2]),
                'status': row[3],
                'results': json.loads(row[4]) if row[4] else {},
                'started_at': row[5],
                'completed_at': row[6]
            })
        
        return logs
    
    def _create_execution(self, workflow_id: str, trigger_data: Dict) -> str:
        """Create workflow execution record"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                trigger_data TEXT,
                status TEXT DEFAULT 'running',
                results TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        execution_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO workflow_executions 
            (id, workflow_id, trigger_data)
            VALUES (?, ?, ?)
        ''', (execution_id, workflow_id, json.dumps(trigger_data)))
        self.db.commit()
        
        return execution_id
    
    def _update_execution(self, execution_id: str, status: str, results: Dict):
        """Update execution status"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE workflow_executions 
            SET status = ?, results = ?, completed_at = ?
            WHERE id = ?
        ''', (status, json.dumps(results), datetime.now().isoformat(), execution_id))
        self.db.commit()
    
    def _process_workflow_nodes(self, nodes: List[Dict], edges: List[Dict], 
                                context: Dict, execution_id: str) -> Dict:
        """Process workflow nodes and execute actions"""
        results = {'steps': [], 'context': context}
        
        # Find start node
        start_nodes = [n for n in nodes if n.get('type') == 'start']
        if not start_nodes:
            return results
        
        current_node = start_nodes[0]
        visited = set()
        
        while current_node and current_node['id'] not in visited:
            visited.add(current_node['id'])
            
            # Execute node action
            node_result = self._execute_node_action(current_node, context)
            results['steps'].append({
                'node_id': current_node['id'],
                'type': current_node.get('type'),
                'result': node_result
            })
            
            # Update context with node results
            context.update(node_result.get('data', {}))
            
            # Find next node based on edges
            next_edges = [e for e in edges if e['source'] == current_node['id']]
            if not next_edges:
                break
            
            # Handle conditional branching
            if current_node.get('type') == 'condition':
                condition_met = self._evaluate_condition(current_node, context)
                next_edge = next((e for e in next_edges if e.get('condition') == condition_met), None)
            else:
                next_edge = next_edges[0] if next_edges else None
            
            if not next_edge:
                break
            
            current_node = next((n for n in nodes if n['id'] == next_edge['target']), None)
        
        return results
    
    def _execute_node_action(self, node: Dict, context: Dict) -> Dict:
        """Execute single node action"""
        node_type = node.get('type')
        config = node.get('config', {})
        
        # In production: Implement actual action execution
        if node_type == 'email':
            return {'success': True, 'action': 'email_sent', 'data': {'email_id': 'mock123'}}
        elif node_type == 'slack':
            return {'success': True, 'action': 'slack_sent', 'data': {'message_ts': 'mock456'}}
        elif node_type == 'webhook':
            return {'success': True, 'action': 'webhook_called', 'data': {'response': 200}}
        elif node_type == 'delay':
            return {'success': True, 'action': 'delayed', 'data': {'delay_ms': config.get('duration', 1000)}}
        else:
            return {'success': True, 'action': 'processed'}
    
    def _evaluate_condition(self, node: Dict, context: Dict) -> bool:
        """Evaluate conditional logic"""
        config = node.get('config', {})
        field = config.get('field')
        operator = config.get('operator')
        value = config.get('value')
        
        if field not in context:
            return False
        
        field_value = context[field]
        
        if operator == 'equals':
            return field_value == value
        elif operator == 'not_equals':
            return field_value != value
        elif operator == 'contains':
            return value in str(field_value)
        elif operator == 'greater_than':
            return float(field_value) > float(value)
        elif operator == 'less_than':
            return float(field_value) < float(value)
        
        return False
