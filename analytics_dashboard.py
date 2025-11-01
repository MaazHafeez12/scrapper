"""
Advanced Analytics Dashboard Module
Provides conversion tracking, ROI metrics, and platform performance analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class AnalyticsDashboard:
    """Comprehensive analytics and reporting system."""
    
    def __init__(self):
        self.conversion_events = []
        self.platform_metrics = {}
        self.cost_data = []
        self.revenue_data = []
        
    def track_conversion_event(self, 
                              event_type: str,
                              lead_id: str,
                              details: Dict = None) -> Dict:
        """
        Track conversion funnel event.
        
        Event types: 'discovery', 'contact_attempted', 'response_received', 'deal_closed'
        
        Args:
            event_type: Type of conversion event
            lead_id: Unique identifier for the lead
            details: Additional event details
            
        Returns:
            Dict with event confirmation
        """
        event = {
            'id': f"event_{len(self.conversion_events) + 1}",
            'type': event_type,
            'lead_id': lead_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.conversion_events.append(event)
        
        return {
            'success': True,
            'event_id': event['id'],
            'message': f'Tracked {event_type} for lead {lead_id}'
        }
    
    def get_conversion_funnel(self, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict:
        """
        Get conversion funnel statistics.
        
        Args:
            start_date: Filter events from this date
            end_date: Filter events until this date
            
        Returns:
            Dict with funnel metrics and conversion rates
        """
        # Filter events by date if provided
        filtered_events = self.conversion_events
        if start_date or end_date:
            filtered_events = [
                e for e in self.conversion_events
                if self._is_in_date_range(e['timestamp'], start_date, end_date)
            ]
        
        # Count events by type
        discovery_count = sum(1 for e in filtered_events if e['type'] == 'discovery')
        contact_count = sum(1 for e in filtered_events if e['type'] == 'contact_attempted')
        response_count = sum(1 for e in filtered_events if e['type'] == 'response_received')
        deal_count = sum(1 for e in filtered_events if e['type'] == 'deal_closed')
        
        # Calculate conversion rates
        contact_rate = (contact_count / discovery_count * 100) if discovery_count > 0 else 0
        response_rate = (response_count / contact_count * 100) if contact_count > 0 else 0
        close_rate = (deal_count / response_count * 100) if response_count > 0 else 0
        overall_rate = (deal_count / discovery_count * 100) if discovery_count > 0 else 0
        
        return {
            'funnel_stages': {
                'discovery': {
                    'count': discovery_count,
                    'percentage': 100,
                    'description': 'Jobs/Leads Discovered'
                },
                'contact': {
                    'count': contact_count,
                    'percentage': round(contact_rate, 2),
                    'description': 'Contact Attempts Made',
                    'conversion_from_previous': round(contact_rate, 2)
                },
                'response': {
                    'count': response_count,
                    'percentage': round(response_rate, 2),
                    'description': 'Responses Received',
                    'conversion_from_previous': round(response_rate, 2)
                },
                'deal': {
                    'count': deal_count,
                    'percentage': round(close_rate, 2),
                    'description': 'Deals Closed',
                    'conversion_from_previous': round(close_rate, 2)
                }
            },
            'overall_conversion_rate': round(overall_rate, 2),
            'total_events': len(filtered_events),
            'date_range': {
                'start': start_date.isoformat() if start_date else 'all_time',
                'end': end_date.isoformat() if end_date else 'present'
            }
        }
    
    def track_cost(self, 
                  platform: str,
                  amount: float,
                  cost_type: str,
                  description: str = None) -> Dict:
        """
        Track costs associated with lead generation.
        
        Args:
            platform: Platform name (linkedin, indeed, etc.)
            amount: Cost amount
            cost_type: Type of cost (subscription, advertising, tools, etc.)
            description: Optional description
            
        Returns:
            Dict with cost tracking confirmation
        """
        cost_record = {
            'id': f"cost_{len(self.cost_data) + 1}",
            'platform': platform,
            'amount': amount,
            'cost_type': cost_type,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        self.cost_data.append(cost_record)
        
        return {
            'success': True,
            'cost_id': cost_record['id'],
            'message': f'Tracked ${amount} cost for {platform}'
        }
    
    def track_revenue(self,
                     lead_id: str,
                     amount: float,
                     platform: str,
                     description: str = None) -> Dict:
        """
        Track revenue from closed deals.
        
        Args:
            lead_id: Lead that generated revenue
            amount: Revenue amount
            platform: Source platform
            description: Optional description
            
        Returns:
            Dict with revenue tracking confirmation
        """
        revenue_record = {
            'id': f"revenue_{len(self.revenue_data) + 1}",
            'lead_id': lead_id,
            'amount': amount,
            'platform': platform,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        self.revenue_data.append(revenue_record)
        
        return {
            'success': True,
            'revenue_id': revenue_record['id'],
            'message': f'Tracked ${amount} revenue from {platform}'
        }
    
    def get_roi_metrics(self,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict:
        """
        Calculate ROI metrics.
        
        Args:
            start_date: Start date for calculation
            end_date: End date for calculation
            
        Returns:
            Dict with comprehensive ROI metrics
        """
        # Filter data by date
        filtered_costs = self._filter_by_date(self.cost_data, start_date, end_date)
        filtered_revenue = self._filter_by_date(self.revenue_data, start_date, end_date)
        
        total_costs = sum(c['amount'] for c in filtered_costs)
        total_revenue = sum(r['amount'] for r in filtered_revenue)
        
        profit = total_revenue - total_costs
        roi_percentage = (profit / total_costs * 100) if total_costs > 0 else 0
        
        # Cost per lead
        discovery_events = [
            e for e in self.conversion_events
            if e['type'] == 'discovery' and self._is_in_date_range(e['timestamp'], start_date, end_date)
        ]
        cost_per_lead = (total_costs / len(discovery_events)) if len(discovery_events) > 0 else 0
        
        # Cost per deal
        deal_events = [
            e for e in self.conversion_events
            if e['type'] == 'deal_closed' and self._is_in_date_range(e['timestamp'], start_date, end_date)
        ]
        cost_per_deal = (total_costs / len(deal_events)) if len(deal_events) > 0 else 0
        
        # Revenue per deal
        revenue_per_deal = (total_revenue / len(deal_events)) if len(deal_events) > 0 else 0
        
        return {
            'total_costs': round(total_costs, 2),
            'total_revenue': round(total_revenue, 2),
            'profit': round(profit, 2),
            'roi_percentage': round(roi_percentage, 2),
            'cost_per_lead': round(cost_per_lead, 2),
            'cost_per_deal': round(cost_per_deal, 2),
            'revenue_per_deal': round(revenue_per_deal, 2),
            'deals_closed': len(deal_events),
            'leads_generated': len(discovery_events),
            'date_range': {
                'start': start_date.isoformat() if start_date else 'all_time',
                'end': end_date.isoformat() if end_date else 'present'
            }
        }
    
    def get_platform_performance(self,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict:
        """
        Compare performance across platforms.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dict with platform comparison metrics
        """
        platforms = ['linkedin', 'indeed', 'remoteok', 'weworkremotely', 
                    'glassdoor', 'wellfound', 'nodesk']
        
        platform_stats = {}
        
        for platform in platforms:
            # Count events by platform
            platform_events = [
                e for e in self.conversion_events
                if e.get('details', {}).get('platform') == platform
                and self._is_in_date_range(e['timestamp'], start_date, end_date)
            ]
            
            discoveries = sum(1 for e in platform_events if e['type'] == 'discovery')
            contacts = sum(1 for e in platform_events if e['type'] == 'contact_attempted')
            responses = sum(1 for e in platform_events if e['type'] == 'response_received')
            deals = sum(1 for e in platform_events if e['type'] == 'deal_closed')
            
            # Calculate platform-specific costs and revenue
            platform_costs = sum(
                c['amount'] for c in self.cost_data
                if c['platform'] == platform 
                and self._is_in_date_range(c['timestamp'], start_date, end_date)
            )
            
            platform_revenue = sum(
                r['amount'] for r in self.revenue_data
                if r['platform'] == platform
                and self._is_in_date_range(r['timestamp'], start_date, end_date)
            )
            
            # Calculate metrics
            conversion_rate = (deals / discoveries * 100) if discoveries > 0 else 0
            roi = ((platform_revenue - platform_costs) / platform_costs * 100) if platform_costs > 0 else 0
            
            platform_stats[platform] = {
                'discoveries': discoveries,
                'contacts': contacts,
                'responses': responses,
                'deals': deals,
                'conversion_rate': round(conversion_rate, 2),
                'costs': round(platform_costs, 2),
                'revenue': round(platform_revenue, 2),
                'roi': round(roi, 2),
                'cost_per_lead': round(platform_costs / discoveries, 2) if discoveries > 0 else 0,
                'cost_per_deal': round(platform_costs / deals, 2) if deals > 0 else 0
            }
        
        # Rank platforms
        ranked_platforms = sorted(
            platform_stats.items(),
            key=lambda x: x[1]['roi'],
            reverse=True
        )
        
        return {
            'platforms': platform_stats,
            'ranking': [
                {
                    'platform': p[0],
                    'roi': p[1]['roi'],
                    'deals': p[1]['deals'],
                    'conversion_rate': p[1]['conversion_rate']
                }
                for p in ranked_platforms
            ],
            'best_performer': ranked_platforms[0][0] if ranked_platforms else None,
            'date_range': {
                'start': start_date.isoformat() if start_date else 'all_time',
                'end': end_date.isoformat() if end_date else 'present'
            }
        }
    
    def get_time_series_analysis(self,
                                granularity: str = 'daily',
                                days: int = 30) -> Dict:
        """
        Get time-series analysis of key metrics.
        
        Args:
            granularity: 'daily', 'weekly', or 'monthly'
            days: Number of days to analyze
            
        Returns:
            Dict with time-series data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Group events by time period
        time_periods = self._group_by_time(self.conversion_events, start_date, granularity)
        
        series_data = []
        for period, events in time_periods.items():
            discoveries = sum(1 for e in events if e['type'] == 'discovery')
            contacts = sum(1 for e in events if e['type'] == 'contact_attempted')
            responses = sum(1 for e in events if e['type'] == 'response_received')
            deals = sum(1 for e in events if e['type'] == 'deal_closed')
            
            series_data.append({
                'period': period,
                'discoveries': discoveries,
                'contacts': contacts,
                'responses': responses,
                'deals': deals,
                'conversion_rate': round(deals / discoveries * 100, 2) if discoveries > 0 else 0
            })
        
        return {
            'granularity': granularity,
            'days_analyzed': days,
            'data_points': len(series_data),
            'series': series_data,
            'trends': self._calculate_trends(series_data)
        }
    
    def _is_in_date_range(self, 
                         timestamp_str: str,
                         start_date: Optional[datetime],
                         end_date: Optional[datetime]) -> bool:
        """Check if timestamp is within date range."""
        if not start_date and not end_date:
            return True
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            if start_date and timestamp < start_date:
                return False
            if end_date and timestamp > end_date:
                return False
            return True
        except:
            return False
    
    def _filter_by_date(self, 
                       data: List[Dict],
                       start_date: Optional[datetime],
                       end_date: Optional[datetime]) -> List[Dict]:
        """Filter data by date range."""
        return [
            item for item in data
            if self._is_in_date_range(item['timestamp'], start_date, end_date)
        ]
    
    def _group_by_time(self, 
                      events: List[Dict],
                      start_date: datetime,
                      granularity: str) -> Dict:
        """Group events by time period."""
        groups = {}
        
        for event in events:
            try:
                timestamp = datetime.fromisoformat(event['timestamp'])
                if timestamp < start_date:
                    continue
                
                if granularity == 'daily':
                    period_key = timestamp.strftime('%Y-%m-%d')
                elif granularity == 'weekly':
                    period_key = timestamp.strftime('%Y-W%W')
                else:  # monthly
                    period_key = timestamp.strftime('%Y-%m')
                
                if period_key not in groups:
                    groups[period_key] = []
                groups[period_key].append(event)
            except:
                continue
        
        return groups
    
    def _calculate_trends(self, series_data: List[Dict]) -> Dict:
        """Calculate trend indicators."""
        if len(series_data) < 2:
            return {'trend': 'insufficient_data'}
        
        recent = series_data[-5:] if len(series_data) >= 5 else series_data
        
        avg_discoveries = sum(d['discoveries'] for d in recent) / len(recent)
        avg_deals = sum(d['deals'] for d in recent) / len(recent)
        avg_conversion = sum(d['conversion_rate'] for d in recent) / len(recent)
        
        # Simple trend detection
        discoveries_trend = 'increasing' if recent[-1]['discoveries'] > avg_discoveries else 'decreasing'
        deals_trend = 'increasing' if recent[-1]['deals'] > avg_deals else 'decreasing'
        conversion_trend = 'improving' if recent[-1]['conversion_rate'] > avg_conversion else 'declining'
        
        return {
            'discoveries': discoveries_trend,
            'deals': deals_trend,
            'conversion': conversion_trend,
            'avg_discoveries': round(avg_discoveries, 2),
            'avg_deals': round(avg_deals, 2),
            'avg_conversion_rate': round(avg_conversion, 2)
        }
