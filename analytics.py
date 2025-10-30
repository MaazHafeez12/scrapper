"""
Job Search Analytics Engine

Provides insights and trends from job data:
- Job posting trends over time
- Salary distribution and insights
- Skills demand analysis
- Platform performance comparison
- Application funnel metrics
- Geographic distribution
- Company insights
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics
from database import JobDatabase


class JobAnalytics:
    """Analytics engine for job search insights"""
    
    def __init__(self, db: Optional[JobDatabase] = None):
        self.db = db or JobDatabase()
    
    def get_job_trends(self, days: int = 30) -> Dict:
        """
        Analyze job posting trends over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        # Get all jobs and filter by date
        all_jobs = self.db.search_jobs(limit=100000)
        jobs = [j for j in all_jobs if datetime.fromisoformat(j['scraped_at']) >= cutoff_date]
        
        # Group by date
        jobs_by_date = defaultdict(int)
        for job in jobs:
            date_str = job['scraped_at'][:10]  # YYYY-MM-DD
            jobs_by_date[date_str] += 1
        
        # Sort by date
        sorted_dates = sorted(jobs_by_date.items())
        
        # Calculate daily average
        total_jobs = sum(jobs_by_date.values())
        avg_per_day = total_jobs / days if days > 0 else 0
        
        # Find peak day
        peak_day = max(sorted_dates, key=lambda x: x[1]) if sorted_dates else (None, 0)
        
        return {
            'days_analyzed': days,
            'total_jobs': total_jobs,
            'avg_per_day': round(avg_per_day, 2),
            'peak_day': peak_day[0],
            'peak_count': peak_day[1],
            'daily_data': sorted_dates,
            'trend': self._calculate_trend(sorted_dates)
        }
    
    def _calculate_trend(self, daily_data: List[Tuple[str, int]]) -> str:
        """Calculate if trend is increasing, decreasing, or stable"""
        if len(daily_data) < 2:
            return 'insufficient_data'
        
        # Compare first half with second half
        mid = len(daily_data) // 2
        first_half_avg = sum(count for _, count in daily_data[:mid]) / mid
        second_half_avg = sum(count for _, count in daily_data[mid:]) / (len(daily_data) - mid)
        
        diff_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
        
        if diff_pct > 10:
            return 'increasing'
        elif diff_pct < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_salary_insights(self, min_jobs: int = 10) -> Dict:
        """
        Analyze salary data
        
        Args:
            min_jobs: Minimum jobs needed for meaningful insights
            
        Returns:
            Dictionary with salary insights
        """
        jobs = self.db.search_jobs(limit=10000)  # Get all jobs
        
        # Extract salaries
        salaries = []
        for job in jobs:
            salary_str = job.get('salary', '')
            if salary_str:
                # Parse salary (simple approach)
                salary_val = self._parse_salary(salary_str)
                if salary_val:
                    salaries.append(salary_val)
        
        if len(salaries) < min_jobs:
            return {
                'insufficient_data': True,
                'jobs_with_salary': len(salaries),
                'required_minimum': min_jobs
            }
        
        # Calculate statistics
        salaries.sort()
        
        return {
            'jobs_with_salary': len(salaries),
            'jobs_without_salary': len(jobs) - len(salaries),
            'min': min(salaries),
            'max': max(salaries),
            'median': statistics.median(salaries),
            'mean': round(statistics.mean(salaries)),
            'percentile_25': salaries[len(salaries) // 4],
            'percentile_75': salaries[3 * len(salaries) // 4],
            'ranges': self._salary_ranges(salaries)
        }
    
    def _parse_salary(self, salary_str: str) -> Optional[int]:
        """Parse salary string to yearly amount"""
        import re
        
        # Remove common words
        salary_str = salary_str.lower().replace('k', '000')
        
        # Find numbers
        numbers = re.findall(r'\d+,?\d*', salary_str)
        if not numbers:
            return None
        
        # Take first number as base salary
        salary = int(numbers[0].replace(',', ''))
        
        # Adjust for hourly (assume 40h/week, 52 weeks)
        if 'hour' in salary_str or '/hr' in salary_str:
            salary = salary * 40 * 52
        
        # Reasonable range check
        if 20000 <= salary <= 500000:
            return salary
        
        return None
    
    def _salary_ranges(self, salaries: List[int]) -> Dict:
        """Group salaries into ranges"""
        ranges = {
            '<50k': 0,
            '50k-75k': 0,
            '75k-100k': 0,
            '100k-125k': 0,
            '125k-150k': 0,
            '150k-200k': 0,
            '>200k': 0
        }
        
        for salary in salaries:
            if salary < 50000:
                ranges['<50k'] += 1
            elif salary < 75000:
                ranges['50k-75k'] += 1
            elif salary < 100000:
                ranges['75k-100k'] += 1
            elif salary < 125000:
                ranges['100k-125k'] += 1
            elif salary < 150000:
                ranges['125k-150k'] += 1
            elif salary < 200000:
                ranges['150k-200k'] += 1
            else:
                ranges['>200k'] += 1
        
        return ranges
    
    def get_skills_frequency(self, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        Analyze most in-demand skills
        
        Args:
            top_n: Number of top skills to return
            
        Returns:
            List of (skill, count) tuples
        """
        from ai_matcher import JobMatcher
        
        jobs = self.db.search_jobs(limit=10000)
        matcher = JobMatcher(self.db)
        
        # Count skills across all jobs
        skill_counter = Counter()
        
        for job in jobs:
            description = job.get('description', '')
            if description:
                skills = matcher.extract_skills(description)
                skill_counter.update(skills)
        
        return skill_counter.most_common(top_n)
    
    def get_platform_stats(self) -> List[Dict]:
        """
        Compare performance across platforms
        
        Returns:
            List of platform statistics
        """
        jobs = self.db.search_jobs(limit=10000)
        
        platform_data = defaultdict(lambda: {
            'total_jobs': 0,
            'remote_jobs': 0,
            'with_salary': 0,
            'avg_salary': [],
            'new_count': 0,
            'applied_count': 0
        })
        
        for job in jobs:
            platform = job.get('platform', 'unknown')
            data = platform_data[platform]
            
            data['total_jobs'] += 1
            
            if job.get('location', '').lower() in ['remote', 'anywhere']:
                data['remote_jobs'] += 1
            
            salary_str = job.get('salary', '')
            if salary_str:
                data['with_salary'] += 1
                salary_val = self._parse_salary(salary_str)
                if salary_val:
                    data['avg_salary'].append(salary_val)
            
            status = job.get('status', 'new')
            if status == 'new':
                data['new_count'] += 1
            elif status == 'applied':
                data['applied_count'] += 1
        
        # Calculate averages and format
        results = []
        for platform, data in platform_data.items():
            avg_salary = statistics.mean(data['avg_salary']) if data['avg_salary'] else 0
            
            results.append({
                'platform': platform,
                'total_jobs': data['total_jobs'],
                'remote_jobs': data['remote_jobs'],
                'remote_percentage': round(data['remote_jobs'] / data['total_jobs'] * 100, 1) if data['total_jobs'] > 0 else 0,
                'with_salary': data['with_salary'],
                'salary_percentage': round(data['with_salary'] / data['total_jobs'] * 100, 1) if data['total_jobs'] > 0 else 0,
                'avg_salary': round(avg_salary) if avg_salary > 0 else None,
                'new_count': data['new_count'],
                'applied_count': data['applied_count'],
                'application_rate': round(data['applied_count'] / data['total_jobs'] * 100, 1) if data['total_jobs'] > 0 else 0
            })
        
        # Sort by total jobs
        results.sort(key=lambda x: x['total_jobs'], reverse=True)
        
        return results
    
    def get_application_funnel(self) -> Dict:
        """
        Analyze application funnel metrics
        
        Returns:
            Dictionary with funnel statistics
        """
        jobs = self.db.search_jobs(limit=10000)
        
        funnel = {
            'new': 0,
            'interested': 0,
            'applied': 0,
            'interview': 0,
            'offer': 0,
            'rejected': 0,
            'archived': 0
        }
        
        for job in jobs:
            status = job.get('status', 'new')
            if status in funnel:
                funnel[status] += 1
        
        total = sum(funnel.values())
        
        # Calculate conversion rates
        conversions = {}
        if funnel['new'] > 0:
            conversions['new_to_interested'] = round(funnel['interested'] / funnel['new'] * 100, 1)
            conversions['new_to_applied'] = round(funnel['applied'] / funnel['new'] * 100, 1)
        
        if funnel['applied'] > 0:
            conversions['applied_to_interview'] = round(funnel['interview'] / funnel['applied'] * 100, 1)
        
        if funnel['interview'] > 0:
            conversions['interview_to_offer'] = round(funnel['offer'] / funnel['interview'] * 100, 1)
        
        return {
            'funnel': funnel,
            'total_jobs': total,
            'conversions': conversions,
            'success_rate': round(funnel['offer'] / total * 100, 2) if total > 0 else 0
        }
    
    def get_geographic_distribution(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Analyze job distribution by location
        
        Args:
            top_n: Number of top locations to return
            
        Returns:
            List of (location, count) tuples
        """
        jobs = self.db.search_jobs(limit=10000)
        
        location_counter = Counter()
        
        for job in jobs:
            location = job.get('location', 'Unknown')
            if location:
                # Normalize location
                location = location.strip().title()
                if location.lower() in ['remote', 'anywhere', 'worldwide']:
                    location = 'Remote'
                location_counter[location] += 1
        
        return location_counter.most_common(top_n)
    
    def get_company_insights(self, top_n: int = 10) -> List[Dict]:
        """
        Analyze top companies and hiring patterns
        
        Args:
            top_n: Number of top companies to return
            
        Returns:
            List of company statistics
        """
        jobs = self.db.search_jobs(limit=10000)
        
        company_data = defaultdict(lambda: {
            'job_count': 0,
            'remote_count': 0,
            'applied_count': 0,
            'avg_salary': []
        })
        
        for job in jobs:
            company = job.get('company', 'Unknown')
            if company and company != 'Unknown':
                data = company_data[company]
                
                data['job_count'] += 1
                
                if job.get('location', '').lower() in ['remote', 'anywhere']:
                    data['remote_count'] += 1
                
                if job.get('status') == 'applied':
                    data['applied_count'] += 1
                
                salary_val = self._parse_salary(job.get('salary', ''))
                if salary_val:
                    data['avg_salary'].append(salary_val)
        
        # Format results
        results = []
        for company, data in company_data.items():
            avg_salary = statistics.mean(data['avg_salary']) if data['avg_salary'] else 0
            
            results.append({
                'company': company,
                'job_count': data['job_count'],
                'remote_count': data['remote_count'],
                'applied_count': data['applied_count'],
                'avg_salary': round(avg_salary) if avg_salary > 0 else None
            })
        
        # Sort by job count
        results.sort(key=lambda x: x['job_count'], reverse=True)
        
        return results[:top_n]
    
    def get_time_to_apply_metrics(self) -> Dict:
        """
        Analyze how long it takes to apply to jobs after scraping
        
        Returns:
            Dictionary with time metrics
        """
        jobs = self.db.search_jobs(status='applied', limit=10000)
        
        time_diffs = []
        
        for job in jobs:
            scraped_at = datetime.fromisoformat(job['scraped_at'])
            updated_at = datetime.fromisoformat(job['updated_at'])
            
            diff_hours = (updated_at - scraped_at).total_seconds() / 3600
            
            if diff_hours >= 0:  # Sanity check
                time_diffs.append(diff_hours)
        
        if not time_diffs:
            return {'insufficient_data': True}
        
        time_diffs.sort()
        
        return {
            'total_applications': len(time_diffs),
            'avg_hours': round(statistics.mean(time_diffs), 1),
            'median_hours': round(statistics.median(time_diffs), 1),
            'min_hours': round(min(time_diffs), 1),
            'max_hours': round(max(time_diffs), 1),
            'within_24h': sum(1 for t in time_diffs if t <= 24),
            'within_48h': sum(1 for t in time_diffs if t <= 48),
            'within_week': sum(1 for t in time_diffs if t <= 168)
        }
    
    def get_comprehensive_report(self) -> Dict:
        """
        Generate comprehensive analytics report
        
        Returns:
            Dictionary with all analytics
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'job_trends': self.get_job_trends(30),
            'salary_insights': self.get_salary_insights(),
            'top_skills': self.get_skills_frequency(15),
            'platform_stats': self.get_platform_stats(),
            'application_funnel': self.get_application_funnel(),
            'top_locations': self.get_geographic_distribution(10),
            'top_companies': self.get_company_insights(10),
            'time_metrics': self.get_time_to_apply_metrics()
        }


def print_analytics_report(analytics: JobAnalytics):
    """Print a formatted analytics report to console"""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    console.print("\n[bold cyan]📊 JOB SEARCH ANALYTICS REPORT[/bold cyan]\n")
    
    # Job Trends
    trends = analytics.get_job_trends(30)
    console.print(Panel(f"""
[bold]Last 30 Days Trends:[/bold]
• Total Jobs: {trends['total_jobs']}
• Daily Average: {trends['avg_per_day']}
• Peak Day: {trends['peak_day']} ({trends['peak_count']} jobs)
• Trend: {trends['trend'].upper()}
    """.strip(), title="📈 Job Posting Trends"))
    
    # Salary Insights
    salary = analytics.get_salary_insights()
    if not salary.get('insufficient_data'):
        console.print(Panel(f"""
[bold]Salary Statistics:[/bold]
• Jobs with Salary: {salary['jobs_with_salary']}
• Median: ${salary['median']:,}
• Mean: ${salary['mean']:,}
• Range: ${salary['min']:,} - ${salary['max']:,}
• 25th Percentile: ${salary['percentile_25']:,}
• 75th Percentile: ${salary['percentile_75']:,}
        """.strip(), title="💰 Salary Insights"))
    
    # Top Skills
    console.print("\n[bold]🔥 Top Skills in Demand:[/bold]\n")
    skills_table = Table(show_header=True)
    skills_table.add_column("Rank", style="cyan", width=6)
    skills_table.add_column("Skill", style="green")
    skills_table.add_column("Count", style="yellow", justify="right")
    
    for i, (skill, count) in enumerate(analytics.get_skills_frequency(10), 1):
        skills_table.add_row(str(i), skill, str(count))
    
    console.print(skills_table)
    
    # Platform Stats
    console.print("\n[bold]🌐 Platform Performance:[/bold]\n")
    platform_table = Table(show_header=True)
    platform_table.add_column("Platform", style="cyan")
    platform_table.add_column("Jobs", justify="right")
    platform_table.add_column("Remote %", justify="right")
    platform_table.add_column("Avg Salary", justify="right")
    
    for platform in analytics.get_platform_stats()[:5]:
        platform_table.add_row(
            platform['platform'],
            str(platform['total_jobs']),
            f"{platform['remote_percentage']}%",
            f"${platform['avg_salary']:,}" if platform['avg_salary'] else "N/A"
        )
    
    console.print(platform_table)
    
    # Application Funnel
    funnel = analytics.get_application_funnel()
    console.print(Panel(f"""
[bold]Application Pipeline:[/bold]
• New: {funnel['funnel']['new']}
• Interested: {funnel['funnel']['interested']}
• Applied: {funnel['funnel']['applied']}
• Interview: {funnel['funnel']['interview']}
• Offer: {funnel['funnel']['offer']}
• Success Rate: {funnel['success_rate']}%
    """.strip(), title="🎯 Application Funnel"))
    
    console.print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Demo
    analytics = JobAnalytics()
    print_analytics_report(analytics)
