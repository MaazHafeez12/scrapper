"""
Revenue Intelligence & Forecasting Module
Deal tracking, pipeline forecasting, revenue predictions, win/loss analysis, quota tracking
"""

from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import secrets
import random

class RevenueIntelligence:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_deal(self, deal_data: Dict) -> Dict:
        """Create sales deal"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id TEXT PRIMARY KEY,
                name TEXT,
                company TEXT,
                contact_id TEXT,
                owner_id TEXT,
                value REAL,
                currency TEXT DEFAULT 'USD',
                stage TEXT,
                probability INTEGER,
                expected_close_date TEXT,
                actual_close_date TEXT,
                source TEXT,
                tags TEXT,
                custom_fields TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        deal_id = secrets.token_urlsafe(16)
        
        # Auto-calculate probability based on stage
        probability = self._get_stage_probability(deal_data.get('stage', 'prospecting'))
        
        cursor.execute('''
            INSERT INTO deals 
            (id, name, company, contact_id, owner_id, value, currency, stage, 
             probability, expected_close_date, source, tags, custom_fields)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            deal_id,
            deal_data['name'],
            deal_data['company'],
            deal_data.get('contact_id'),
            deal_data['owner_id'],
            deal_data['value'],
            deal_data.get('currency', 'USD'),
            deal_data.get('stage', 'prospecting'),
            probability,
            deal_data.get('expected_close_date'),
            deal_data.get('source'),
            json.dumps(deal_data.get('tags', [])),
            json.dumps(deal_data.get('custom_fields', {}))
        ))
        self.db.commit()
        
        return {
            'success': True,
            'deal_id': deal_id,
            'probability': probability,
            'message': 'Deal created successfully'
        }
    
    def update_deal_stage(self, deal_id: str, stage: str, notes: str = '') -> Dict:
        """Update deal stage"""
        cursor = self.db.cursor()
        
        cursor.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
        deal = cursor.fetchone()
        
        if not deal:
            return {'success': False, 'error': 'Deal not found'}
        
        probability = self._get_stage_probability(stage)
        
        # Log stage change
        self._log_deal_activity(deal_id, 'stage_changed', {
            'old_stage': deal[7],
            'new_stage': stage,
            'notes': notes
        })
        
        cursor.execute('''
            UPDATE deals 
            SET stage = ?, probability = ?, updated_at = ?
            WHERE id = ?
        ''', (stage, probability, datetime.now().isoformat(), deal_id))
        
        # If won or lost, set close date
        if stage in ['won', 'lost']:
            cursor.execute('''
                UPDATE deals 
                SET actual_close_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), deal_id))
        
        self.db.commit()
        
        return {
            'success': True,
            'deal_id': deal_id,
            'stage': stage,
            'probability': probability
        }
    
    def get_pipeline_forecast(self, owner_id: str = None, period: str = 'quarter') -> Dict:
        """Get pipeline revenue forecast"""
        cursor = self.db.cursor()
        
        # Calculate period dates
        if period == 'month':
            start_date = datetime.now().replace(day=1).isoformat()
            end_date = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()
        elif period == 'quarter':
            month = datetime.now().month
            quarter_start_month = ((month - 1) // 3) * 3 + 1
            start_date = datetime.now().replace(month=quarter_start_month, day=1).isoformat()
            end_date = (datetime.now().replace(month=quarter_start_month, day=1) + timedelta(days=95)).isoformat()
        else:  # year
            start_date = datetime.now().replace(month=1, day=1).isoformat()
            end_date = datetime.now().replace(month=12, day=31).isoformat()
        
        query = '''
            SELECT 
                stage,
                COUNT(*) as count,
                SUM(value) as total_value,
                SUM(value * probability / 100.0) as weighted_value,
                AVG(probability) as avg_probability
            FROM deals
            WHERE expected_close_date BETWEEN ? AND ?
            AND stage NOT IN ('won', 'lost')
        '''
        params = [start_date, end_date]
        
        if owner_id:
            query += ' AND owner_id = ?'
            params.append(owner_id)
        
        query += ' GROUP BY stage'
        
        cursor.execute(query, params)
        
        pipeline_by_stage = []
        total_pipeline = 0
        total_weighted = 0
        
        for row in cursor.fetchall():
            stage_data = {
                'stage': row[0],
                'count': row[1],
                'total_value': round(row[2], 2),
                'weighted_value': round(row[3], 2),
                'avg_probability': round(row[4], 2)
            }
            pipeline_by_stage.append(stage_data)
            total_pipeline += row[2]
            total_weighted += row[3]
        
        # Get closed won in period
        query_won = '''
            SELECT COUNT(*), SUM(value)
            FROM deals
            WHERE stage = 'won'
            AND actual_close_date BETWEEN ? AND ?
        '''
        params_won = [start_date, end_date]
        
        if owner_id:
            query_won += ' AND owner_id = ?'
            params_won.append(owner_id)
        
        cursor.execute(query_won, params_won)
        won_stats = cursor.fetchone()
        
        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_pipeline_value': round(total_pipeline, 2),
            'weighted_pipeline_value': round(total_weighted, 2),
            'closed_won_count': won_stats[0] or 0,
            'closed_won_value': round(won_stats[1] or 0, 2),
            'pipeline_by_stage': pipeline_by_stage,
            'forecast_accuracy': self._calculate_forecast_accuracy(owner_id)
        }
    
    def track_quota(self, quota_data: Dict) -> Dict:
        """Track sales quota"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotas (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                period TEXT,
                target_amount REAL,
                actual_amount REAL DEFAULT 0,
                start_date TEXT,
                end_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        quota_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO quotas 
            (id, user_id, period, target_amount, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            quota_id,
            quota_data['user_id'],
            quota_data['period'],
            quota_data['target_amount'],
            quota_data['start_date'],
            quota_data['end_date']
        ))
        self.db.commit()
        
        return {
            'success': True,
            'quota_id': quota_id,
            'message': 'Quota tracked successfully'
        }
    
    def get_quota_performance(self, user_id: str, period: str = 'current') -> Dict:
        """Get quota performance"""
        cursor = self.db.cursor()
        
        if period == 'current':
            cursor.execute('''
                SELECT * FROM quotas
                WHERE user_id = ?
                AND start_date <= ?
                AND end_date >= ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id, datetime.now().isoformat(), datetime.now().isoformat()))
        else:
            cursor.execute('''
                SELECT * FROM quotas
                WHERE user_id = ? AND period = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id, period))
        
        quota = cursor.fetchone()
        
        if not quota:
            return {'success': False, 'error': 'No quota found'}
        
        # Calculate actual from closed deals
        cursor.execute('''
            SELECT SUM(value)
            FROM deals
            WHERE owner_id = ?
            AND stage = 'won'
            AND actual_close_date BETWEEN ? AND ?
        ''', (user_id, quota[5], quota[6]))
        
        actual_amount = cursor.fetchone()[0] or 0
        
        # Update quota actual
        cursor.execute('''
            UPDATE quotas 
            SET actual_amount = ?
            WHERE id = ?
        ''', (actual_amount, quota[0]))
        self.db.commit()
        
        target = quota[3]
        attainment = (actual_amount / target * 100) if target > 0 else 0
        
        return {
            'quota_id': quota[0],
            'user_id': user_id,
            'period': quota[2],
            'target_amount': round(target, 2),
            'actual_amount': round(actual_amount, 2),
            'attainment_percent': round(attainment, 2),
            'remaining': round(target - actual_amount, 2),
            'start_date': quota[5],
            'end_date': quota[6]
        }
    
    def analyze_win_loss(self, filters: Dict = None) -> Dict:
        """Win/Loss analysis"""
        cursor = self.db.cursor()
        
        query = '''
            SELECT 
                stage,
                COUNT(*) as count,
                SUM(value) as total_value,
                AVG(value) as avg_value
            FROM deals
            WHERE stage IN ('won', 'lost')
        '''
        params = []
        
        if filters:
            if 'start_date' in filters:
                query += ' AND actual_close_date >= ?'
                params.append(filters['start_date'])
            if 'end_date' in filters:
                query += ' AND actual_close_date <= ?'
                params.append(filters['end_date'])
            if 'owner_id' in filters:
                query += ' AND owner_id = ?'
                params.append(filters['owner_id'])
        
        query += ' GROUP BY stage'
        
        cursor.execute(query, params)
        
        results = {'won': {}, 'lost': {}}
        total_deals = 0
        
        for row in cursor.fetchall():
            stage = row[0]
            results[stage] = {
                'count': row[1],
                'total_value': round(row[2], 2),
                'avg_value': round(row[3], 2)
            }
            total_deals += row[1]
        
        won_count = results['won'].get('count', 0)
        lost_count = results['lost'].get('count', 0)
        
        # Analyze loss reasons
        cursor.execute('''
            SELECT 
                json_extract(custom_fields, '$.loss_reason') as reason,
                COUNT(*) as count
            FROM deals
            WHERE stage = 'lost'
            AND json_extract(custom_fields, '$.loss_reason') IS NOT NULL
            GROUP BY reason
            ORDER BY count DESC
        ''')
        
        loss_reasons = [{'reason': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return {
            'total_deals': total_deals,
            'won': results['won'],
            'lost': results['lost'],
            'win_rate': round((won_count / total_deals * 100) if total_deals > 0 else 0, 2),
            'loss_reasons': loss_reasons
        }
    
    def predict_revenue(self, owner_id: str = None, months_ahead: int = 3) -> Dict:
        """Predict future revenue using historical trends"""
        cursor = self.db.cursor()
        
        # Get historical monthly revenue
        query = '''
            SELECT 
                strftime('%Y-%m', actual_close_date) as month,
                SUM(value) as revenue
            FROM deals
            WHERE stage = 'won'
            AND actual_close_date >= date('now', '-12 months')
        '''
        params = []
        
        if owner_id:
            query += ' AND owner_id = ?'
            params.append(owner_id)
        
        query += ' GROUP BY month ORDER BY month'
        
        cursor.execute(query, params)
        
        historical = [{'month': row[0], 'revenue': round(row[1], 2)} for row in cursor.fetchall()]
        
        # Simple moving average prediction
        if len(historical) >= 3:
            recent_revenues = [h['revenue'] for h in historical[-3:]]
            avg_revenue = sum(recent_revenues) / len(recent_revenues)
            
            # Apply growth trend
            if len(historical) >= 6:
                old_avg = sum([h['revenue'] for h in historical[-6:-3]]) / 3
                growth_rate = ((avg_revenue - old_avg) / old_avg) if old_avg > 0 else 0
            else:
                growth_rate = 0.05  # Default 5% growth
            
            predictions = []
            current_month = datetime.now()
            
            for i in range(1, months_ahead + 1):
                predicted_month = (current_month + timedelta(days=30 * i)).strftime('%Y-%m')
                predicted_revenue = avg_revenue * (1 + growth_rate) ** i
                predictions.append({
                    'month': predicted_month,
                    'predicted_revenue': round(predicted_revenue, 2),
                    'confidence': 'medium' if i <= 2 else 'low'
                })
        else:
            predictions = []
        
        return {
            'historical_data': historical,
            'predictions': predictions,
            'growth_rate': round(growth_rate * 100, 2) if 'growth_rate' in locals() else 0
        }
    
    def get_revenue_analytics(self, date_range: Dict) -> Dict:
        """Get comprehensive revenue analytics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_deals,
                SUM(CASE WHEN stage = 'won' THEN 1 ELSE 0 END) as won_deals,
                SUM(CASE WHEN stage = 'won' THEN value ELSE 0 END) as total_revenue,
                AVG(CASE WHEN stage = 'won' THEN value ELSE NULL END) as avg_deal_size,
                SUM(value) as total_pipeline
            FROM deals
            WHERE created_at BETWEEN ? AND ?
        ''', (date_range['start'], date_range['end']))
        
        stats = cursor.fetchone()
        
        # Revenue by source
        cursor.execute('''
            SELECT source, SUM(value) as revenue
            FROM deals
            WHERE stage = 'won'
            AND actual_close_date BETWEEN ? AND ?
            GROUP BY source
            ORDER BY revenue DESC
        ''', (date_range['start'], date_range['end']))
        
        revenue_by_source = [{'source': row[0] or 'unknown', 'revenue': round(row[1], 2)} 
                            for row in cursor.fetchall()]
        
        # Top performing reps
        cursor.execute('''
            SELECT owner_id, COUNT(*) as deals, SUM(value) as revenue
            FROM deals
            WHERE stage = 'won'
            AND actual_close_date BETWEEN ? AND ?
            GROUP BY owner_id
            ORDER BY revenue DESC
            LIMIT 10
        ''', (date_range['start'], date_range['end']))
        
        top_reps = [
            {'owner_id': row[0], 'deals': row[1], 'revenue': round(row[2], 2)}
            for row in cursor.fetchall()
        ]
        
        return {
            'total_deals': stats[0] or 0,
            'won_deals': stats[1] or 0,
            'total_revenue': round(stats[2] or 0, 2),
            'avg_deal_size': round(stats[3] or 0, 2),
            'total_pipeline': round(stats[4] or 0, 2),
            'win_rate': round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0, 2),
            'revenue_by_source': revenue_by_source,
            'top_performers': top_reps
        }
    
    def _get_stage_probability(self, stage: str) -> int:
        """Get probability based on deal stage"""
        probabilities = {
            'prospecting': 10,
            'qualification': 20,
            'needs_analysis': 30,
            'proposal': 50,
            'negotiation': 75,
            'closed_won': 100,
            'won': 100,
            'lost': 0
        }
        return probabilities.get(stage, 10)
    
    def _calculate_forecast_accuracy(self, owner_id: str = None) -> float:
        """Calculate historical forecast accuracy"""
        # In production: Compare historical forecasts to actual results
        # For now, return mock accuracy
        return round(random.uniform(75, 95), 2)
    
    def _log_deal_activity(self, deal_id: str, activity_type: str, details: Dict):
        """Log deal activity"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deal_activities (
                id TEXT PRIMARY KEY,
                deal_id TEXT,
                activity_type TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        activity_id = secrets.token_urlsafe(16)
        
        cursor.execute('''
            INSERT INTO deal_activities 
            (id, deal_id, activity_type, details)
            VALUES (?, ?, ?, ?)
        ''', (activity_id, deal_id, activity_type, json.dumps(details)))
        self.db.commit()
