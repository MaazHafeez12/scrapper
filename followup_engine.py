"""
Automated Follow-up Engine
Smart follow-up system with engagement-based timing and automatic adjustments
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class FollowUpEngine:
    """Intelligent automated follow-up system."""
    
    def __init__(self):
        self.follow_up_rules = self._load_default_rules()
        self.scheduled_followups = []
        self.engagement_history = {}
        
    def _load_default_rules(self) -> Dict:
        """Load default follow-up rules."""
        return {
            'no_response': {
                'intervals': [3, 5, 7],  # Days between follow-ups
                'max_attempts': 3,
                'stop_on_response': True
            },
            'opened_not_responded': {
                'intervals': [2, 4, 6],
                'max_attempts': 4,
                'stop_on_response': True
            },
            'clicked_not_responded': {
                'intervals': [1, 3, 5],
                'max_attempts': 5,
                'stop_on_response': True
            },
            'partial_engagement': {
                'intervals': [4, 7, 10],
                'max_attempts': 3,
                'stop_on_response': True
            }
        }
    
    def create_follow_up_sequence(self, 
                                  lead_id: str,
                                  initial_email_id: str,
                                  rule_type: str = 'no_response') -> Dict:
        """
        Create automated follow-up sequence.
        
        Args:
            lead_id: Unique lead identifier
            initial_email_id: ID of the initial email
            rule_type: Type of follow-up rule to apply
            
        Returns:
            Dict with sequence details
        """
        if rule_type not in self.follow_up_rules:
            return {
                'success': False,
                'error': f'Invalid rule type. Available: {list(self.follow_up_rules.keys())}'
            }
        
        rule = self.follow_up_rules[rule_type]
        sequence_id = f"seq_{lead_id}_{int(datetime.now().timestamp())}"
        
        followups = []
        for i, interval in enumerate(rule['intervals']):
            scheduled_date = datetime.now() + timedelta(days=interval)
            
            followup = {
                'id': f"{sequence_id}_followup_{i+1}",
                'sequence_id': sequence_id,
                'lead_id': lead_id,
                'attempt_number': i + 1,
                'scheduled_for': scheduled_date.isoformat(),
                'status': 'scheduled',
                'rule_type': rule_type,
                'auto_adjust': True
            }
            
            followups.append(followup)
            self.scheduled_followups.append(followup)
        
        return {
            'success': True,
            'sequence_id': sequence_id,
            'lead_id': lead_id,
            'rule_type': rule_type,
            'max_attempts': rule['max_attempts'],
            'followups_scheduled': len(followups),
            'schedule': followups
        }
    
    def update_on_engagement(self, 
                            lead_id: str,
                            engagement_type: str,
                            sequence_id: Optional[str] = None) -> Dict:
        """
        Update follow-up schedule based on engagement.
        
        Args:
            lead_id: Lead identifier
            engagement_type: 'opened', 'clicked', 'replied', 'unsubscribed'
            sequence_id: Optional specific sequence to update
            
        Returns:
            Dict with updated schedule
        """
        # Track engagement
        if lead_id not in self.engagement_history:
            self.engagement_history[lead_id] = []
        
        self.engagement_history[lead_id].append({
            'type': engagement_type,
            'timestamp': datetime.now().isoformat()
        })
        
        # Find active follow-ups for this lead
        active_followups = [
            f for f in self.scheduled_followups 
            if f['lead_id'] == lead_id 
            and f['status'] == 'scheduled'
            and (sequence_id is None or f.get('sequence_id') == sequence_id)
        ]
        
        if engagement_type == 'replied' or engagement_type == 'unsubscribed':
            # Cancel all future follow-ups
            for followup in active_followups:
                followup['status'] = 'cancelled'
                followup['cancelled_reason'] = f'Lead {engagement_type}'
            
            return {
                'success': True,
                'action': 'cancelled_all',
                'reason': f'Lead {engagement_type}',
                'cancelled_count': len(active_followups)
            }
        
        elif engagement_type == 'opened':
            # Adjust to "opened_not_responded" timing
            self._adjust_followup_timing(active_followups, 'opened_not_responded')
            
            return {
                'success': True,
                'action': 'adjusted_timing',
                'new_rule': 'opened_not_responded',
                'adjusted_count': len(active_followups)
            }
        
        elif engagement_type == 'clicked':
            # More aggressive follow-up
            self._adjust_followup_timing(active_followups, 'clicked_not_responded')
            
            return {
                'success': True,
                'action': 'adjusted_timing',
                'new_rule': 'clicked_not_responded',
                'adjusted_count': len(active_followups)
            }
        
        return {
            'success': True,
            'action': 'no_change',
            'message': 'Engagement recorded, no timing adjustment needed'
        }
    
    def _adjust_followup_timing(self, followups: List[Dict], new_rule_type: str):
        """Adjust follow-up timing based on new rule."""
        if new_rule_type not in self.follow_up_rules:
            return
        
        new_rule = self.follow_up_rules[new_rule_type]
        base_date = datetime.now()
        
        for i, followup in enumerate(followups):
            if i < len(new_rule['intervals']):
                new_scheduled = base_date + timedelta(days=new_rule['intervals'][i])
                followup['scheduled_for'] = new_scheduled.isoformat()
                followup['rule_type'] = new_rule_type
                followup['adjusted'] = True
                followup['adjusted_at'] = datetime.now().isoformat()
    
    def get_due_followups(self, hours_ahead: int = 24) -> Dict:
        """
        Get follow-ups due in the next N hours.
        
        Args:
            hours_ahead: Look ahead this many hours
            
        Returns:
            Dict with due follow-ups
        """
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)
        
        due_followups = []
        for followup in self.scheduled_followups:
            if followup['status'] != 'scheduled':
                continue
            
            scheduled_time = datetime.fromisoformat(followup['scheduled_for'])
            if scheduled_time <= cutoff_time:
                due_followups.append(followup)
        
        return {
            'success': True,
            'due_count': len(due_followups),
            'hours_ahead': hours_ahead,
            'followups': sorted(due_followups, key=lambda x: x['scheduled_for'])
        }
    
    def mark_followup_sent(self, followup_id: str) -> Dict:
        """Mark follow-up as sent."""
        for followup in self.scheduled_followups:
            if followup['id'] == followup_id:
                followup['status'] = 'sent'
                followup['sent_at'] = datetime.now().isoformat()
                return {
                    'success': True,
                    'message': 'Follow-up marked as sent'
                }
        
        return {
            'success': False,
            'error': 'Follow-up not found'
        }
    
    def cancel_sequence(self, sequence_id: str, reason: str = 'Manual cancellation') -> Dict:
        """Cancel entire follow-up sequence."""
        cancelled_count = 0
        
        for followup in self.scheduled_followups:
            if followup.get('sequence_id') == sequence_id and followup['status'] == 'scheduled':
                followup['status'] = 'cancelled'
                followup['cancelled_reason'] = reason
                followup['cancelled_at'] = datetime.now().isoformat()
                cancelled_count += 1
        
        return {
            'success': True,
            'sequence_id': sequence_id,
            'cancelled_count': cancelled_count,
            'reason': reason
        }
    
    def get_engagement_stats(self, lead_id: str) -> Dict:
        """Get engagement statistics for a lead."""
        if lead_id not in self.engagement_history:
            return {
                'success': True,
                'lead_id': lead_id,
                'total_engagements': 0,
                'engagements': []
            }
        
        engagements = self.engagement_history[lead_id]
        
        # Count by type
        engagement_counts = {}
        for engagement in engagements:
            eng_type = engagement['type']
            engagement_counts[eng_type] = engagement_counts.get(eng_type, 0) + 1
        
        # Calculate engagement score
        score = (
            engagement_counts.get('opened', 0) * 1 +
            engagement_counts.get('clicked', 0) * 3 +
            engagement_counts.get('replied', 0) * 10
        )
        
        return {
            'success': True,
            'lead_id': lead_id,
            'total_engagements': len(engagements),
            'engagement_counts': engagement_counts,
            'engagement_score': score,
            'last_engagement': engagements[-1] if engagements else None,
            'engagements': engagements
        }
    
    def optimize_timing_ml(self, lead_data: Dict, historical_data: List[Dict]) -> Dict:
        """
        ML-based timing optimization (simplified version).
        
        Args:
            lead_data: Current lead information
            historical_data: Historical follow-up data
            
        Returns:
            Dict with optimized timing recommendations
        """
        # Analyze historical success rates
        if not historical_data:
            return {
                'success': True,
                'recommendation': 'Use default timing',
                'confidence': 'low',
                'suggested_intervals': [3, 5, 7]
            }
        
        # Calculate average response times
        response_times = []
        for record in historical_data:
            if record.get('responded'):
                response_times.append(record.get('response_time_hours', 72))
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            
            # Suggest intervals based on average response time
            suggested_intervals = [
                int(avg_response_time / 24),  # Convert hours to days
                int(avg_response_time / 24) + 2,
                int(avg_response_time / 24) + 4
            ]
        else:
            suggested_intervals = [3, 5, 7]
        
        return {
            'success': True,
            'recommendation': 'ML-optimized timing',
            'confidence': 'medium' if len(historical_data) > 10 else 'low',
            'suggested_intervals': suggested_intervals,
            'based_on_samples': len(historical_data),
            'avg_response_time_hours': sum(response_times) / len(response_times) if response_times else None
        }
    
    def get_all_sequences(self, status: Optional[str] = None) -> Dict:
        """Get all follow-up sequences."""
        # Group by sequence_id
        sequences = {}
        
        for followup in self.scheduled_followups:
            seq_id = followup.get('sequence_id')
            if seq_id not in sequences:
                sequences[seq_id] = {
                    'sequence_id': seq_id,
                    'lead_id': followup['lead_id'],
                    'followups': []
                }
            sequences[seq_id]['followups'].append(followup)
        
        # Filter by status if provided
        if status:
            sequences = {
                k: v for k, v in sequences.items()
                if any(f['status'] == status for f in v['followups'])
            }
        
        return {
            'success': True,
            'sequence_count': len(sequences),
            'sequences': list(sequences.values())
        }
    
    def get_performance_metrics(self) -> Dict:
        """Get follow-up performance metrics."""
        total_sent = len([f for f in self.scheduled_followups if f['status'] == 'sent'])
        total_scheduled = len([f for f in self.scheduled_followups if f['status'] == 'scheduled'])
        total_cancelled = len([f for f in self.scheduled_followups if f['status'] == 'cancelled'])
        
        # Calculate engagement metrics
        total_engagements = sum(len(history) for history in self.engagement_history.values())
        leads_with_engagement = len(self.engagement_history)
        
        return {
            'success': True,
            'metrics': {
                'total_followups': len(self.scheduled_followups),
                'sent': total_sent,
                'scheduled': total_scheduled,
                'cancelled': total_cancelled,
                'total_engagements': total_engagements,
                'leads_with_engagement': leads_with_engagement,
                'avg_engagements_per_lead': round(total_engagements / max(leads_with_engagement, 1), 2)
            }
        }
    
    def custom_rule(self, 
                   rule_name: str,
                   intervals: List[int],
                   max_attempts: int,
                   stop_on_response: bool = True) -> Dict:
        """Create custom follow-up rule."""
        if rule_name in self.follow_up_rules:
            return {
                'success': False,
                'error': f'Rule "{rule_name}" already exists'
            }
        
        self.follow_up_rules[rule_name] = {
            'intervals': intervals,
            'max_attempts': max_attempts,
            'stop_on_response': stop_on_response
        }
        
        return {
            'success': True,
            'message': f'Custom rule "{rule_name}" created',
            'rule': self.follow_up_rules[rule_name]
        }
