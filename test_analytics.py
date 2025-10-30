"""
Unit tests for analytics module
Tests JobAnalytics class and analysis functions
"""

import unittest
import os
import tempfile
from datetime import datetime, timedelta
from database import JobDatabase
from analytics import JobAnalytics


class TestJobAnalytics(unittest.TestCase):
    """Test cases for JobAnalytics class"""

    def setUp(self):
        """Set up test database and analytics"""
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.db = JobDatabase(self.test_db_path)
        self.analytics = JobAnalytics(self.test_db_path)
        
        # Add sample jobs
        self._add_sample_jobs()

    def tearDown(self):
        """Clean up after each test"""
        self.db.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    def _add_sample_jobs(self):
        """Add sample jobs for testing"""
        # Job 1: Recent, high salary, with skills
        job1 = {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'description': 'Python Django PostgreSQL AWS Docker',
            'url': 'https://example.com/job/1',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'platform': 'Indeed',
            'salary': '$140,000',
            'remote': True
        }
        job1_id = self.db.add_job(**job1)
        self.db.add_skills_to_job(job1_id, ['python', 'django', 'postgresql', 'aws', 'docker'])
        
        # Job 2: Recent, medium salary
        job2 = {
            'title': 'Full Stack Developer',
            'company': 'StartUp Inc',
            'location': 'New York, NY',
            'description': 'JavaScript React Node.js MongoDB',
            'url': 'https://example.com/job/2',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'platform': 'LinkedIn',
            'salary': '$110,000',
            'remote': False
        }
        job2_id = self.db.add_job(**job2)
        self.db.add_skills_to_job(job2_id, ['javascript', 'react', 'nodejs', 'mongodb'])
        
        # Job 3: Old job, low salary
        old_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        job3 = {
            'title': 'Junior Developer',
            'company': 'Small Co',
            'location': 'Austin, TX',
            'description': 'Python JavaScript',
            'url': 'https://example.com/job/3',
            'date_posted': old_date,
            'platform': 'RemoteOK',
            'salary': '$70,000',
            'remote': True
        }
        job3_id = self.db.add_job(**job3)
        self.db.add_skills_to_job(job3_id, ['python', 'javascript'])
        self.db.update_status(job3_id, 'applied')
        
        # Job 4: Recent, no salary
        job4 = {
            'title': 'DevOps Engineer',
            'company': 'Cloud Corp',
            'location': 'Seattle, WA',
            'description': 'Kubernetes Docker AWS Terraform',
            'url': 'https://example.com/job/4',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'platform': 'Indeed',
            'remote': True
        }
        job4_id = self.db.add_job(**job4)
        self.db.add_skills_to_job(job4_id, ['kubernetes', 'docker', 'aws', 'terraform'])
        self.db.update_status(job4_id, 'interview')

    # ===== JOB TRENDS TESTS =====

    def test_get_job_trends_basic(self):
        """Test getting basic job trends"""
        trends = self.analytics.get_job_trends(days=30)
        
        self.assertIn('total_jobs', trends)
        self.assertIn('daily_trends', trends)
        self.assertIn('average_per_day', trends)
        self.assertGreater(trends['total_jobs'], 0)

    def test_job_trends_different_periods(self):
        """Test job trends for different time periods"""
        trends_7 = self.analytics.get_job_trends(days=7)
        trends_30 = self.analytics.get_job_trends(days=30)
        
        # 30-day should have more or equal jobs than 7-day
        self.assertGreaterEqual(
            trends_30['total_jobs'],
            trends_7['total_jobs']
        )

    def test_job_trends_trend_direction(self):
        """Test trend direction calculation"""
        trends = self.analytics.get_job_trends(days=30)
        
        self.assertIn('trend', trends)
        self.assertIn(trends['trend'], ['increasing', 'stable', 'decreasing'])

    def test_job_trends_peak_day(self):
        """Test peak day identification"""
        trends = self.analytics.get_job_trends(days=30)
        
        if trends['total_jobs'] > 0:
            self.assertIn('peak_day', trends)
            self.assertIsNotNone(trends['peak_day'])

    # ===== SALARY INSIGHTS TESTS =====

    def test_get_salary_insights_basic(self):
        """Test getting basic salary insights"""
        insights = self.analytics.get_salary_insights()
        
        self.assertIn('total_jobs_with_salary', insights)
        self.assertIn('median', insights)
        self.assertIn('mean', insights)
        self.assertIn('min', insights)
        self.assertIn('max', insights)

    def test_salary_statistics(self):
        """Test salary statistics calculations"""
        insights = self.analytics.get_salary_insights()
        
        if insights['total_jobs_with_salary'] > 0:
            # Median should be between min and max
            self.assertGreaterEqual(insights['median'], insights['min'])
            self.assertLessEqual(insights['median'], insights['max'])
            
            # Mean should be reasonable
            self.assertGreater(insights['mean'], 0)

    def test_salary_percentiles(self):
        """Test salary percentile calculations"""
        insights = self.analytics.get_salary_insights()
        
        if insights['total_jobs_with_salary'] > 0:
            self.assertIn('percentile_25', insights)
            self.assertIn('percentile_75', insights)
            
            # 25th should be <= 75th
            self.assertLessEqual(
                insights['percentile_25'],
                insights['percentile_75']
            )

    def test_salary_distribution(self):
        """Test salary distribution by ranges"""
        insights = self.analytics.get_salary_insights()
        
        self.assertIn('distribution', insights)
        dist = insights['distribution']
        
        # Should have standard salary ranges
        expected_ranges = [
            'Under $50K',
            '$50K-75K',
            '$75K-100K',
            '$100K-125K',
            '$125K-150K',
            '$150K-200K',
            'Over $200K'
        ]
        
        for range_name in expected_ranges:
            self.assertIn(range_name, dist)

    # ===== SKILLS FREQUENCY TESTS =====

    def test_get_skills_frequency_basic(self):
        """Test getting basic skills frequency"""
        skills = self.analytics.get_skills_frequency(top_n=10)
        
        self.assertIsInstance(skills, list)
        self.assertGreater(len(skills), 0)

    def test_skills_frequency_format(self):
        """Test skills frequency return format"""
        skills = self.analytics.get_skills_frequency(top_n=10)
        
        for skill, count in skills:
            self.assertIsInstance(skill, str)
            self.assertIsInstance(count, int)
            self.assertGreater(count, 0)

    def test_skills_frequency_ordering(self):
        """Test skills are ordered by frequency"""
        skills = self.analytics.get_skills_frequency(top_n=10)
        
        # Check descending order
        for i in range(len(skills) - 1):
            self.assertGreaterEqual(skills[i][1], skills[i+1][1])

    def test_skills_frequency_top_n(self):
        """Test top_n parameter limits results"""
        skills_5 = self.analytics.get_skills_frequency(top_n=5)
        skills_10 = self.analytics.get_skills_frequency(top_n=10)
        
        self.assertLessEqual(len(skills_5), 5)
        self.assertLessEqual(len(skills_10), 10)

    def test_skills_frequency_common_skills(self):
        """Test that common skills appear"""
        skills = self.analytics.get_skills_frequency(top_n=20)
        skill_names = [s[0] for s in skills]
        
        # Based on our sample data
        self.assertIn('python', skill_names)
        self.assertIn('docker', skill_names)

    # ===== PLATFORM STATS TESTS =====

    def test_get_platform_stats_basic(self):
        """Test getting basic platform stats"""
        stats = self.analytics.get_platform_stats()
        
        self.assertIsInstance(stats, list)
        self.assertGreater(len(stats), 0)

    def test_platform_stats_structure(self):
        """Test platform stats structure"""
        stats = self.analytics.get_platform_stats()
        
        for platform in stats:
            self.assertIn('platform', platform)
            self.assertIn('total_jobs', platform)
            self.assertIn('remote_jobs', platform)
            self.assertIn('remote_percentage', platform)

    def test_platform_stats_calculations(self):
        """Test platform statistics calculations"""
        stats = self.analytics.get_platform_stats()
        
        for platform in stats:
            # Remote percentage should be valid
            self.assertGreaterEqual(platform['remote_percentage'], 0)
            self.assertLessEqual(platform['remote_percentage'], 100)
            
            # Remote jobs <= total jobs
            self.assertLessEqual(
                platform['remote_jobs'],
                platform['total_jobs']
            )

    def test_platform_stats_platforms(self):
        """Test expected platforms appear"""
        stats = self.analytics.get_platform_stats()
        platforms = [p['platform'] for p in stats]
        
        # Based on sample data
        self.assertIn('Indeed', platforms)
        self.assertIn('LinkedIn', platforms)

    # ===== APPLICATION FUNNEL TESTS =====

    def test_get_application_funnel_basic(self):
        """Test getting basic application funnel"""
        funnel = self.analytics.get_application_funnel()
        
        self.assertIn('stages', funnel)
        self.assertIn('total_jobs', funnel)

    def test_application_funnel_stages(self):
        """Test funnel has all stages"""
        funnel = self.analytics.get_application_funnel()
        stages = funnel['stages']
        
        expected_stages = ['new', 'interested', 'applied', 'interview', 'offer', 'rejected']
        
        for stage in expected_stages:
            self.assertIn(stage, stages)
            self.assertIsInstance(stages[stage], int)
            self.assertGreaterEqual(stages[stage], 0)

    def test_application_funnel_conversions(self):
        """Test funnel conversion rates"""
        funnel = self.analytics.get_application_funnel()
        
        if 'conversion_rates' in funnel:
            rates = funnel['conversion_rates']
            
            for stage, rate in rates.items():
                self.assertGreaterEqual(rate, 0)
                self.assertLessEqual(rate, 100)

    # ===== GEOGRAPHIC DISTRIBUTION TESTS =====

    def test_get_geographic_distribution_basic(self):
        """Test getting basic geographic distribution"""
        locations = self.analytics.get_geographic_distribution(top_n=10)
        
        self.assertIsInstance(locations, list)

    def test_geographic_distribution_format(self):
        """Test geographic distribution format"""
        locations = self.analytics.get_geographic_distribution(top_n=10)
        
        for location, count in locations:
            self.assertIsInstance(location, str)
            self.assertIsInstance(count, int)
            self.assertGreater(count, 0)

    def test_geographic_distribution_ordering(self):
        """Test locations ordered by count"""
        locations = self.analytics.get_geographic_distribution(top_n=10)
        
        for i in range(len(locations) - 1):
            self.assertGreaterEqual(locations[i][1], locations[i+1][1])

    # ===== COMPANY INSIGHTS TESTS =====

    def test_get_company_insights_basic(self):
        """Test getting basic company insights"""
        companies = self.analytics.get_company_insights(top_n=10)
        
        self.assertIsInstance(companies, list)

    def test_company_insights_format(self):
        """Test company insights format"""
        companies = self.analytics.get_company_insights(top_n=10)
        
        for company_data in companies:
            self.assertIn('company', company_data)
            self.assertIn('total_jobs', company_data)
            self.assertIsInstance(company_data['total_jobs'], int)

    def test_company_insights_ordering(self):
        """Test companies ordered by job count"""
        companies = self.analytics.get_company_insights(top_n=10)
        
        for i in range(len(companies) - 1):
            self.assertGreaterEqual(
                companies[i]['total_jobs'],
                companies[i+1]['total_jobs']
            )

    # ===== COMPREHENSIVE REPORT TESTS =====

    def test_get_comprehensive_report(self):
        """Test getting comprehensive report"""
        report = self.analytics.get_comprehensive_report()
        
        # Should include all major sections
        self.assertIn('trends', report)
        self.assertIn('salary', report)
        self.assertIn('skills', report)
        self.assertIn('platforms', report)
        self.assertIn('funnel', report)
        self.assertIn('locations', report)
        self.assertIn('companies', report)
        self.assertIn('generated_at', report)

    def test_comprehensive_report_timestamp(self):
        """Test report includes timestamp"""
        report = self.analytics.get_comprehensive_report()
        
        self.assertIn('generated_at', report)
        # Should be recent timestamp
        timestamp = datetime.fromisoformat(report['generated_at'])
        self.assertLess(
            (datetime.now() - timestamp).seconds,
            5  # Generated within last 5 seconds
        )

    # ===== EDGE CASES =====

    def test_empty_database(self):
        """Test analytics with empty database"""
        # Create new empty database
        empty_db_fd, empty_db_path = tempfile.mkstemp()
        empty_analytics = JobAnalytics(empty_db_path)
        
        try:
            # Should not crash, return zeros
            trends = empty_analytics.get_job_trends()
            self.assertEqual(trends['total_jobs'], 0)
            
            salary = empty_analytics.get_salary_insights()
            self.assertEqual(salary['total_jobs_with_salary'], 0)
            
            skills = empty_analytics.get_skills_frequency()
            self.assertEqual(len(skills), 0)
        finally:
            os.close(empty_db_fd)
            os.unlink(empty_db_path)

    def test_single_job(self):
        """Test analytics with single job"""
        # Create database with single job
        single_db_fd, single_db_path = tempfile.mkstemp()
        single_db = JobDatabase(single_db_path)
        
        job = {
            'title': 'Developer',
            'company': 'Corp',
            'location': 'Remote',
            'description': 'Python',
            'url': 'https://example.com/1',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'platform': 'Indeed',
            'salary': '$100,000'
        }
        single_db.add_job(**job)
        
        single_analytics = JobAnalytics(single_db_path)
        
        try:
            trends = single_analytics.get_job_trends()
            self.assertEqual(trends['total_jobs'], 1)
            
            salary = single_analytics.get_salary_insights()
            self.assertEqual(salary['total_jobs_with_salary'], 1)
        finally:
            single_db.close()
            os.close(single_db_fd)
            os.unlink(single_db_path)

    def test_very_old_jobs(self):
        """Test handling very old jobs"""
        old_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        job = {
            'title': 'Old Job',
            'company': 'Old Corp',
            'location': 'Nowhere',
            'description': 'Ancient tech',
            'url': 'https://example.com/old',
            'date_posted': old_date,
            'platform': 'Indeed'
        }
        self.db.add_job(**job)
        
        # Should still process without errors
        trends = self.analytics.get_job_trends(days=400)
        self.assertGreater(trends['total_jobs'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
