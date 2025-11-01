"""
A/B Testing Framework
Test subject lines, email bodies, send times with statistical analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import json
from collections import defaultdict

class ABTestingFramework:
    """A/B testing for email campaigns with statistical analysis."""
    
    def __init__(self):
        self.active_tests = {}
        self.test_results = {}
        self.variant_performance = defaultdict(lambda: {
            'sent': 0,
            'opened': 0,
            'clicked': 0,
            'replied': 0,
            'converted': 0
        })
    
    def create_test(self,
                   test_name: str,
                   test_type: str,
                   variants: List[Dict],
                   traffic_split: Optional[List[float]] = None,
                   duration_days: int = 7,
                   min_sample_size: int = 100) -> Dict:
        """
        Create A/B test.
        
        Args:
            test_name: Unique test name
            test_type: 'subject_line', 'email_body', 'send_time', 'cta_button', 'template'
            variants: List of variant configs (e.g., [{'name': 'A', 'content': '...'}, ...])
            traffic_split: Optional custom traffic split (e.g., [0.5, 0.5] for 50/50)
            duration_days: Test duration in days
            min_sample_size: Minimum sample size per variant for statistical significance
            
        Returns:
            Dict with test configuration
        """
        if test_name in self.active_tests:
            return {
                'success': False,
                'error': f'Test "{test_name}" already exists'
            }
        
        # Validate variants
        if len(variants) < 2:
            return {
                'success': False,
                'error': 'At least 2 variants required'
            }
        
        # Default equal traffic split
        if not traffic_split:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        # Validate traffic split
        if len(traffic_split) != len(variants):
            return {
                'success': False,
                'error': 'Traffic split length must match variants length'
            }
        
        if abs(sum(traffic_split) - 1.0) > 0.01:
            return {
                'success': False,
                'error': 'Traffic split must sum to 1.0'
            }
        
        test_id = f"test_{int(datetime.now().timestamp())}"
        
        test_config = {
            'test_id': test_id,
            'test_name': test_name,
            'test_type': test_type,
            'variants': variants,
            'traffic_split': traffic_split,
            'duration_days': duration_days,
            'min_sample_size': min_sample_size,
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=duration_days)).isoformat(),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        self.active_tests[test_name] = test_config
        
        # Initialize performance tracking for each variant
        for variant in variants:
            variant_key = f"{test_name}_{variant['name']}"
            self.variant_performance[variant_key] = {
                'sent': 0,
                'opened': 0,
                'clicked': 0,
                'replied': 0,
                'converted': 0
            }
        
        return {
            'success': True,
            'test_id': test_id,
            'test_name': test_name,
            'variants': [v['name'] for v in variants],
            'traffic_split': traffic_split,
            'end_date': test_config['end_date'],
            'message': f'A/B test "{test_name}" created successfully'
        }
    
    def assign_variant(self, test_name: str, user_id: str) -> Dict:
        """
        Assign variant to user based on traffic split.
        
        Args:
            test_name: Name of the test
            user_id: Unique user identifier
            
        Returns:
            Dict with assigned variant
        """
        if test_name not in self.active_tests:
            return {
                'success': False,
                'error': f'Test "{test_name}" not found'
            }
        
        test = self.active_tests[test_name]
        
        # Check if test is still active
        if test['status'] != 'active':
            return {
                'success': False,
                'error': f'Test "{test_name}" is {test["status"]}'
            }
        
        # Check if test has ended
        end_date = datetime.fromisoformat(test['end_date'])
        if datetime.now() > end_date:
            test['status'] = 'ended'
            return {
                'success': False,
                'error': 'Test has ended'
            }
        
        # Use user_id hash for consistent assignment
        random.seed(hash(user_id + test_name))
        rand_value = random.random()
        
        # Assign variant based on traffic split
        cumulative = 0
        assigned_variant = None
        
        for i, variant in enumerate(test['variants']):
            cumulative += test['traffic_split'][i]
            if rand_value < cumulative:
                assigned_variant = variant
                break
        
        # Fallback to last variant
        if not assigned_variant:
            assigned_variant = test['variants'][-1]
        
        # Reset random seed
        random.seed()
        
        return {
            'success': True,
            'test_name': test_name,
            'variant': assigned_variant,
            'user_id': user_id
        }
    
    def track_event(self,
                   test_name: str,
                   variant_name: str,
                   event_type: str) -> Dict:
        """
        Track event for variant.
        
        Args:
            test_name: Test name
            variant_name: Variant name
            event_type: 'sent', 'opened', 'clicked', 'replied', 'converted'
            
        Returns:
            Dict with tracking confirmation
        """
        if test_name not in self.active_tests:
            return {
                'success': False,
                'error': f'Test "{test_name}" not found'
            }
        
        variant_key = f"{test_name}_{variant_name}"
        
        if event_type not in self.variant_performance[variant_key]:
            return {
                'success': False,
                'error': f'Invalid event type: {event_type}'
            }
        
        self.variant_performance[variant_key][event_type] += 1
        
        return {
            'success': True,
            'test_name': test_name,
            'variant': variant_name,
            'event_type': event_type,
            'total_events': self.variant_performance[variant_key][event_type]
        }
    
    def get_test_results(self, test_name: str) -> Dict:
        """
        Get test results with statistical analysis.
        
        Args:
            test_name: Test name
            
        Returns:
            Dict with comprehensive results and winner determination
        """
        if test_name not in self.active_tests:
            return {
                'success': False,
                'error': f'Test "{test_name}" not found'
            }
        
        test = self.active_tests[test_name]
        
        # Calculate metrics for each variant
        variant_results = []
        
        for variant in test['variants']:
            variant_key = f"{test_name}_{variant['name']}"
            perf = self.variant_performance[variant_key]
            
            # Calculate rates
            open_rate = (perf['opened'] / perf['sent'] * 100) if perf['sent'] > 0 else 0
            click_rate = (perf['clicked'] / perf['sent'] * 100) if perf['sent'] > 0 else 0
            reply_rate = (perf['replied'] / perf['sent'] * 100) if perf['sent'] > 0 else 0
            conversion_rate = (perf['converted'] / perf['sent'] * 100) if perf['sent'] > 0 else 0
            
            # Click-through rate (of opens)
            ctr = (perf['clicked'] / perf['opened'] * 100) if perf['opened'] > 0 else 0
            
            variant_results.append({
                'variant': variant['name'],
                'variant_config': variant,
                'metrics': {
                    'sent': perf['sent'],
                    'opened': perf['opened'],
                    'clicked': perf['clicked'],
                    'replied': perf['replied'],
                    'converted': perf['converted']
                },
                'rates': {
                    'open_rate': round(open_rate, 2),
                    'click_rate': round(click_rate, 2),
                    'ctr': round(ctr, 2),
                    'reply_rate': round(reply_rate, 2),
                    'conversion_rate': round(conversion_rate, 2)
                },
                'sample_size': perf['sent']
            })
        
        # Determine winner
        winner = self._determine_winner(variant_results, test['min_sample_size'])
        
        # Calculate statistical significance
        significance = self._calculate_significance(variant_results)
        
        return {
            'success': True,
            'test_name': test_name,
            'test_type': test['test_type'],
            'status': test['status'],
            'start_date': test['start_date'],
            'end_date': test['end_date'],
            'duration_days': test['duration_days'],
            'min_sample_size': test['min_sample_size'],
            'variants': variant_results,
            'winner': winner,
            'statistical_significance': significance,
            'recommendation': self._generate_recommendation(winner, significance)
        }
    
    def _determine_winner(self, variant_results: List[Dict], min_sample_size: int) -> Dict:
        """Determine winning variant based on conversion rate."""
        # Check if all variants have minimum sample size
        all_variants_valid = all(v['sample_size'] >= min_sample_size for v in variant_results)
        
        if not all_variants_valid:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {min_sample_size} samples per variant'
            }
        
        # Find variant with highest conversion rate
        best_variant = max(variant_results, key=lambda x: x['rates']['conversion_rate'])
        
        # Calculate improvement over other variants
        other_variants = [v for v in variant_results if v['variant'] != best_variant['variant']]
        if other_variants:
            avg_other_conversion = sum(v['rates']['conversion_rate'] for v in other_variants) / len(other_variants)
            improvement = ((best_variant['rates']['conversion_rate'] - avg_other_conversion) / 
                          max(avg_other_conversion, 0.01) * 100)
        else:
            improvement = 0
        
        return {
            'status': 'winner_determined',
            'winning_variant': best_variant['variant'],
            'conversion_rate': best_variant['rates']['conversion_rate'],
            'improvement_percentage': round(improvement, 2),
            'metrics': best_variant['rates']
        }
    
    def _calculate_significance(self, variant_results: List[Dict]) -> Dict:
        """
        Calculate statistical significance (simplified z-test).
        
        In production, would use proper statistical tests like:
        - Chi-square test
        - T-test
        - Bayesian analysis
        """
        if len(variant_results) < 2:
            return {'significant': False, 'confidence': 0}
        
        # Get top 2 variants by conversion rate
        sorted_variants = sorted(variant_results, key=lambda x: x['rates']['conversion_rate'], reverse=True)
        variant_a = sorted_variants[0]
        variant_b = sorted_variants[1]
        
        # Calculate sample sizes
        n_a = variant_a['sample_size']
        n_b = variant_b['sample_size']
        
        if n_a < 30 or n_b < 30:
            return {
                'significant': False,
                'confidence': 0,
                'message': 'Sample size too small for statistical analysis'
            }
        
        # Calculate conversion rates
        p_a = variant_a['rates']['conversion_rate'] / 100
        p_b = variant_b['rates']['conversion_rate'] / 100
        
        # Calculate pooled standard error (simplified)
        p_pool = (variant_a['metrics']['converted'] + variant_b['metrics']['converted']) / (n_a + n_b)
        se = (p_pool * (1 - p_pool) * (1/n_a + 1/n_b)) ** 0.5
        
        if se == 0:
            return {'significant': False, 'confidence': 0}
        
        # Calculate z-score
        z_score = abs(p_a - p_b) / se
        
        # Determine confidence level (simplified)
        if z_score > 2.576:
            confidence = 99
            significant = True
        elif z_score > 1.96:
            confidence = 95
            significant = True
        elif z_score > 1.645:
            confidence = 90
            significant = True
        else:
            confidence = round((1 - (1.96 - z_score) / 1.96) * 100)
            significant = False
        
        return {
            'significant': significant,
            'confidence': confidence,
            'z_score': round(z_score, 3),
            'message': f'Results are {"" if significant else "not "}statistically significant at {confidence}% confidence'
        }
    
    def _generate_recommendation(self, winner: Dict, significance: Dict) -> str:
        """Generate actionable recommendation."""
        if winner['status'] == 'insufficient_data':
            return "Continue test - need more data for conclusive results"
        
        if not significance.get('significant', False):
            return f"Results inconclusive - confidence only {significance.get('confidence', 0)}%. Consider running test longer."
        
        improvement = winner.get('improvement_percentage', 0)
        
        if improvement > 20:
            return f"Clear winner! Variant {winner['winning_variant']} shows {improvement:.1f}% improvement. Roll out immediately."
        elif improvement > 10:
            return f"Variant {winner['winning_variant']} is better by {improvement:.1f}%. Consider gradual rollout."
        else:
            return f"Marginal difference ({improvement:.1f}%). Consider testing other variables."
    
    def stop_test(self, test_name: str) -> Dict:
        """Stop test early."""
        if test_name not in self.active_tests:
            return {
                'success': False,
                'error': f'Test "{test_name}" not found'
            }
        
        test = self.active_tests[test_name]
        test['status'] = 'stopped'
        test['stopped_at'] = datetime.now().isoformat()
        
        # Get final results
        results = self.get_test_results(test_name)
        
        return {
            'success': True,
            'test_name': test_name,
            'status': 'stopped',
            'final_results': results
        }
    
    def get_all_tests(self, status: Optional[str] = None) -> Dict:
        """Get all tests, optionally filtered by status."""
        tests = list(self.active_tests.values())
        
        if status:
            tests = [t for t in tests if t['status'] == status]
        
        return {
            'success': True,
            'test_count': len(tests),
            'tests': tests
        }
    
    def get_best_performing_variants(self, metric: str = 'conversion_rate') -> Dict:
        """
        Get best performing variants across all tests.
        
        Args:
            metric: 'open_rate', 'click_rate', 'reply_rate', 'conversion_rate'
            
        Returns:
            Dict with top performing variants
        """
        all_variants = []
        
        for test_name, test in self.active_tests.items():
            results = self.get_test_results(test_name)
            if results['success']:
                for variant in results['variants']:
                    all_variants.append({
                        'test_name': test_name,
                        'variant': variant['variant'],
                        'metric_value': variant['rates'].get(metric, 0),
                        'sample_size': variant['sample_size']
                    })
        
        # Sort by metric value
        all_variants.sort(key=lambda x: x['metric_value'], reverse=True)
        
        return {
            'success': True,
            'metric': metric,
            'top_variants': all_variants[:10],  # Top 10
            'total_analyzed': len(all_variants)
        }
