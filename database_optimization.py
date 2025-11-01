"""
Database Optimization Module
Database indexes, query optimization, connection pooling, and performance monitoring
"""

import sqlite3
import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import json
from datetime import datetime

class DatabaseOptimizer:
    """Database optimization and index management"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_indexes(self):
        """Create performance indexes on frequently queried columns"""
        cursor = self.db.cursor()
        
        indexes = [
            # Leads table indexes
            "CREATE INDEX IF NOT EXISTS idx_leads_owner ON leads(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
            "CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score)",
            "CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)",
            
            # Contacts table indexes
            "CREATE INDEX IF NOT EXISTS idx_contacts_owner ON contacts(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)",
            "CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts(created_at)",
            
            # Campaigns table indexes
            "CREATE INDEX IF NOT EXISTS idx_campaigns_owner ON campaigns(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_created ON campaigns(created_at)",
            
            # Outreach table indexes
            "CREATE INDEX IF NOT EXISTS idx_outreach_lead ON outreach_history(lead_id)",
            "CREATE INDEX IF NOT EXISTS idx_outreach_campaign ON outreach_history(campaign_id)",
            "CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_history(status)",
            "CREATE INDEX IF NOT EXISTS idx_outreach_sent ON outreach_history(sent_at)",
            
            # Analytics indexes
            "CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_events(timestamp)",
            
            # Documents indexes
            "CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)",
            
            # Deals/Revenue indexes
            "CREATE INDEX IF NOT EXISTS idx_deals_owner ON deals(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage)",
            "CREATE INDEX IF NOT EXISTS idx_deals_value ON deals(value)",
            "CREATE INDEX IF NOT EXISTS idx_deals_close_date ON deals(expected_close_date)",
            
            # Tasks indexes
            "CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)",
            
            # Webhooks indexes
            "CREATE INDEX IF NOT EXISTS idx_webhooks_owner ON webhooks(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_webhooks_event ON webhooks(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id)",
            "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON webhook_deliveries(status)",
            
            # Workflows indexes
            "CREATE INDEX IF NOT EXISTS idx_workflows_owner ON workflows(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow ON workflow_executions(workflow_id)",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_leads_owner_status ON leads(owner_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_deals_owner_stage ON deals(owner_id, stage)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_assignee_status ON tasks(assignee_id, status)"
        ]
        
        created_count = 0
        for index_query in indexes:
            try:
                cursor.execute(index_query)
                created_count += 1
            except sqlite3.OperationalError as e:
                print(f"Index creation error: {e}")
        
        self.db.commit()
        return created_count
    
    def analyze_tables(self):
        """Analyze tables to update query optimizer statistics"""
        cursor = self.db.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                cursor.execute(f"ANALYZE {table}")
            except sqlite3.OperationalError:
                pass
        
        self.db.commit()
        return len(tables)
    
    def vacuum_database(self):
        """Reclaim unused space and defragment database"""
        cursor = self.db.cursor()
        cursor.execute("VACUUM")
        return True
    
    def get_table_stats(self) -> List[Dict]:
        """Get statistics for all tables"""
        cursor = self.db.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        stats = []
        for table in tables:
            try:
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # Get table size (approximate)
                cursor.execute(f"SELECT SUM(pgsize) FROM dbstat WHERE name=?", (table,))
                size_result = cursor.fetchone()
                size_bytes = size_result[0] if size_result and size_result[0] else 0
                
                stats.append({
                    'table': table,
                    'rows': row_count,
                    'size_kb': round(size_bytes / 1024, 2)
                })
            except sqlite3.OperationalError:
                pass
        
        return stats
    
    def get_index_stats(self) -> List[Dict]:
        """Get statistics for all indexes"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT name, tbl_name 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        
        indexes = []
        for row in cursor.fetchall():
            indexes.append({
                'index': row[0],
                'table': row[1]
            })
        
        return indexes
    
    def optimize_query(self, query: str) -> str:
        """Suggest optimizations for a query"""
        cursor = self.db.cursor()
        
        # Get query plan
        try:
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            suggestions = []
            
            # Check for table scans
            for row in plan:
                detail = str(row).lower()
                if 'scan' in detail and 'index' not in detail:
                    suggestions.append("Consider adding index for scanned columns")
            
            return {
                'query': query,
                'plan': [str(row) for row in plan],
                'suggestions': suggestions
            }
        except sqlite3.OperationalError as e:
            return {'error': str(e)}


class ConnectionPool:
    """Simple SQLite connection pool"""
    
    def __init__(self, database: str, pool_size: int = 5):
        self.database = database
        self.pool_size = pool_size
        self.connections = []
        self.in_use = set()
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Create initial connections"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.database, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.connections.append(conn)
    
    def get_connection(self):
        """Get connection from pool"""
        for conn in self.connections:
            if conn not in self.in_use:
                self.in_use.add(conn)
                return conn
        
        # Create new connection if pool exhausted
        conn = sqlite3.connect(self.database, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self.connections.append(conn)
        self.in_use.add(conn)
        return conn
    
    def release_connection(self, conn):
        """Return connection to pool"""
        if conn in self.in_use:
            self.in_use.remove(conn)
    
    def close_all(self):
        """Close all connections"""
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        self.connections.clear()
        self.in_use.clear()
    
    def get_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            'total_connections': len(self.connections),
            'in_use': len(self.in_use),
            'available': len(self.connections) - len(self.in_use),
            'pool_size': self.pool_size
        }


class QueryPerformanceMonitor:
    """Monitor and log query performance"""
    
    def __init__(self):
        self.query_log = []
        self.slow_query_threshold = 1.0  # seconds
        
    def log_query(self, query: str, execution_time: float, result_count: int = 0):
        """Log query execution"""
        log_entry = {
            'query': query[:200],  # Truncate long queries
            'execution_time': round(execution_time, 4),
            'result_count': result_count,
            'timestamp': datetime.now().isoformat(),
            'is_slow': execution_time > self.slow_query_threshold
        }
        
        self.query_log.append(log_entry)
        
        # Keep only last 1000 queries
        if len(self.query_log) > 1000:
            self.query_log = self.query_log[-1000:]
        
        return log_entry
    
    def get_slow_queries(self) -> List[Dict]:
        """Get all slow queries"""
        return [q for q in self.query_log if q['is_slow']]
    
    def get_query_stats(self) -> Dict:
        """Get overall query statistics"""
        if not self.query_log:
            return {
                'total_queries': 0,
                'avg_time': 0,
                'slow_queries': 0,
                'fastest': 0,
                'slowest': 0
            }
        
        times = [q['execution_time'] for q in self.query_log]
        
        return {
            'total_queries': len(self.query_log),
            'avg_time': round(sum(times) / len(times), 4),
            'slow_queries': len(self.get_slow_queries()),
            'fastest': round(min(times), 4),
            'slowest': round(max(times), 4)
        }
    
    def monitor_query(self, func: Callable):
        """Decorator to monitor query execution"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log query
            query = kwargs.get('query', func.__name__)
            result_count = len(result) if isinstance(result, list) else 1
            self.log_query(str(query), execution_time, result_count)
            
            return result
        return wrapper
    
    def clear_log(self):
        """Clear query log"""
        self.query_log.clear()


class OptimizedQueryBuilder:
    """Build optimized queries"""
    
    @staticmethod
    def paginated_query(table: str, page: int = 1, per_page: int = 50, 
                       where: str = None, order_by: str = None) -> str:
        """Generate paginated query"""
        offset = (page - 1) * per_page
        
        query = f"SELECT * FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            query += " ORDER BY created_at DESC"
        
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        return query
    
    @staticmethod
    def count_query(table: str, where: str = None) -> str:
        """Generate optimized count query"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        return query
    
    @staticmethod
    def batch_insert(table: str, columns: List[str], values: List[tuple]) -> str:
        """Generate batch insert query"""
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        
        return query
    
    @staticmethod
    def optimized_join(primary_table: str, join_table: str, 
                       join_on: str, select_columns: List[str] = None) -> str:
        """Generate optimized join query"""
        if select_columns:
            columns = ', '.join(select_columns)
        else:
            columns = f"{primary_table}.*, {join_table}.*"
        
        query = f"""
            SELECT {columns}
            FROM {primary_table}
            INNER JOIN {join_table} ON {join_on}
        """
        
        return query.strip()


class DatabaseMaintenanceService:
    """Automated database maintenance"""
    
    def __init__(self, optimizer: DatabaseOptimizer):
        self.optimizer = optimizer
        self.maintenance_log = []
        
    def run_maintenance(self) -> Dict:
        """Run full database maintenance"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'tasks': []
        }
        
        # Create/update indexes
        try:
            index_count = self.optimizer.create_indexes()
            results['tasks'].append({
                'task': 'create_indexes',
                'status': 'success',
                'details': f"Created/verified {index_count} indexes"
            })
        except Exception as e:
            results['tasks'].append({
                'task': 'create_indexes',
                'status': 'error',
                'error': str(e)
            })
        
        # Analyze tables
        try:
            table_count = self.optimizer.analyze_tables()
            results['tasks'].append({
                'task': 'analyze_tables',
                'status': 'success',
                'details': f"Analyzed {table_count} tables"
            })
        except Exception as e:
            results['tasks'].append({
                'task': 'analyze_tables',
                'status': 'error',
                'error': str(e)
            })
        
        # Vacuum (optional - can be slow)
        # try:
        #     self.optimizer.vacuum_database()
        #     results['tasks'].append({
        #         'task': 'vacuum',
        #         'status': 'success'
        #     })
        # except Exception as e:
        #     results['tasks'].append({
        #         'task': 'vacuum',
        #         'status': 'error',
        #         'error': str(e)
        #     })
        
        self.maintenance_log.append(results)
        return results
    
    def get_maintenance_history(self) -> List[Dict]:
        """Get maintenance history"""
        return self.maintenance_log
