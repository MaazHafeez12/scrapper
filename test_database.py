"""
Unit tests for database module
Tests JobDatabase class functionality
"""

import unittest
import os
import tempfile
from datetime import datetime, timedelta
from database import JobDatabase


class TestJobDatabase(unittest.TestCase):
    """Test cases for JobDatabase class"""

    def setUp(self):
        """Set up test database before each test"""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.db = JobDatabase(self.test_db_path)

        # Sample job data
        self.sample_job = {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'description': 'Looking for Python expert with 5+ years experience',
            'url': 'https://example.com/job/123',
            'date_posted': '2025-10-28',
            'platform': 'Indeed',
            'salary': '$120,000 - $150,000',
            'remote': True
        }

    def tearDown(self):
        """Clean up after each test"""
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    # ===== INITIALIZATION TESTS =====

    def test_database_creation(self):
        """Test database file is created"""
        self.assertTrue(os.path.exists(self.test_db_path))

    def test_tables_created(self):
        """Test all required tables exist"""
        cursor = self.db.conn.cursor()
        
        # Check jobs table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check skills table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skills'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check job_skills table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_skills'")
        self.assertIsNotNone(cursor.fetchone())

    # ===== ADD JOB TESTS =====

    def test_add_job_basic(self):
        """Test adding a basic job"""
        job_id = self.db.add_job(**self.sample_job)
        self.assertIsNotNone(job_id)
        self.assertIsInstance(job_id, int)

    def test_add_job_duplicate(self):
        """Test adding duplicate job returns existing ID"""
        job_id1 = self.db.add_job(**self.sample_job)
        job_id2 = self.db.add_job(**self.sample_job)
        self.assertEqual(job_id1, job_id2)

    def test_add_job_minimal(self):
        """Test adding job with minimal required fields"""
        minimal_job = {
            'title': 'Developer',
            'company': 'Company',
            'location': 'Remote',
            'description': 'Job description',
            'url': 'https://example.com/job/456',
            'date_posted': '2025-10-28',
            'platform': 'LinkedIn'
        }
        job_id = self.db.add_job(**minimal_job)
        self.assertIsNotNone(job_id)

    def test_add_job_with_skills(self):
        """Test adding job with skills"""
        job_id = self.db.add_job(**self.sample_job)
        skills = ['python', 'django', 'postgresql']
        self.db.add_skills_to_job(job_id, skills)
        
        # Verify skills were added
        job_skills = self.db.get_job_skills(job_id)
        self.assertEqual(len(job_skills), 3)
        self.assertIn('python', job_skills)

    # ===== GET JOB TESTS =====

    def test_get_job_by_id(self):
        """Test retrieving job by ID"""
        job_id = self.db.add_job(**self.sample_job)
        job = self.db.get_job_by_id(job_id)
        
        self.assertIsNotNone(job)
        self.assertEqual(job['title'], self.sample_job['title'])
        self.assertEqual(job['company'], self.sample_job['company'])

    def test_get_nonexistent_job(self):
        """Test retrieving non-existent job returns None"""
        job = self.db.get_job_by_id(99999)
        self.assertIsNone(job)

    def test_get_all_jobs(self):
        """Test getting all jobs"""
        self.db.add_job(**self.sample_job)
        
        job2 = self.sample_job.copy()
        job2['url'] = 'https://example.com/job/789'
        job2['title'] = 'Junior Developer'
        self.db.add_job(**job2)
        
        jobs = self.db.get_all_jobs()
        self.assertGreaterEqual(len(jobs), 2)

    # ===== UPDATE JOB TESTS =====

    def test_update_status(self):
        """Test updating job status"""
        job_id = self.db.add_job(**self.sample_job)
        self.db.update_status(job_id, 'applied')
        
        job = self.db.get_job_by_id(job_id)
        self.assertEqual(job['status'], 'applied')

    def test_update_notes(self):
        """Test updating job notes"""
        job_id = self.db.add_job(**self.sample_job)
        notes = 'Great company culture'
        self.db.update_notes(job_id, notes)
        
        job = self.db.get_job_by_id(job_id)
        self.assertEqual(job['notes'], notes)

    def test_update_multiple_fields(self):
        """Test updating multiple job fields"""
        job_id = self.db.add_job(**self.sample_job)
        self.db.update_status(job_id, 'interview')
        self.db.update_notes(job_id, 'Interview scheduled')
        
        job = self.db.get_job_by_id(job_id)
        self.assertEqual(job['status'], 'interview')
        self.assertEqual(job['notes'], 'Interview scheduled')

    # ===== SEARCH TESTS =====

    def test_search_by_keyword(self):
        """Test searching jobs by keyword"""
        self.db.add_job(**self.sample_job)
        results = self.db.search_jobs(keyword='Python')
        self.assertGreater(len(results), 0)

    def test_search_by_company(self):
        """Test searching jobs by company"""
        self.db.add_job(**self.sample_job)
        results = self.db.search_jobs(company='Tech Corp')
        self.assertGreater(len(results), 0)

    def test_search_by_location(self):
        """Test searching jobs by location"""
        self.db.add_job(**self.sample_job)
        results = self.db.search_jobs(location='San Francisco')
        self.assertGreater(len(results), 0)

    def test_search_by_status(self):
        """Test searching jobs by status"""
        job_id = self.db.add_job(**self.sample_job)
        self.db.update_status(job_id, 'applied')
        
        results = self.db.search_jobs(status='applied')
        self.assertGreater(len(results), 0)

    def test_search_remote_only(self):
        """Test searching for remote jobs only"""
        self.db.add_job(**self.sample_job)
        results = self.db.search_jobs(remote_only=True)
        self.assertGreater(len(results), 0)
        for job in results:
            self.assertTrue(job['remote'])

    def test_search_no_results(self):
        """Test search with no matching results"""
        self.db.add_job(**self.sample_job)
        results = self.db.search_jobs(keyword='NonexistentKeyword12345')
        self.assertEqual(len(results), 0)

    # ===== DELETE TESTS =====

    def test_delete_job(self):
        """Test deleting a job"""
        job_id = self.db.add_job(**self.sample_job)
        self.db.delete_job(job_id)
        
        job = self.db.get_job_by_id(job_id)
        self.assertIsNone(job)

    def test_delete_nonexistent_job(self):
        """Test deleting non-existent job doesn't raise error"""
        try:
            self.db.delete_job(99999)
        except Exception as e:
            self.fail(f"delete_job raised {type(e).__name__} unexpectedly")

    # ===== SKILLS TESTS =====

    def test_add_skills(self):
        """Test adding skills to job"""
        job_id = self.db.add_job(**self.sample_job)
        skills = ['python', 'django', 'rest api']
        self.db.add_skills_to_job(job_id, skills)
        
        job_skills = self.db.get_job_skills(job_id)
        self.assertEqual(len(job_skills), 3)

    def test_add_duplicate_skills(self):
        """Test adding duplicate skills is handled"""
        job_id = self.db.add_job(**self.sample_job)
        skills = ['python', 'python', 'django']
        self.db.add_skills_to_job(job_id, skills)
        
        job_skills = self.db.get_job_skills(job_id)
        # Should only have 2 unique skills
        self.assertEqual(len(job_skills), 2)

    def test_get_skills_from_empty_job(self):
        """Test getting skills from job with no skills"""
        job_id = self.db.add_job(**self.sample_job)
        job_skills = self.db.get_job_skills(job_id)
        self.assertEqual(len(job_skills), 0)

    # ===== STATISTICS TESTS =====

    def test_get_stats_empty(self):
        """Test getting stats from empty database"""
        stats = self.db.get_stats()
        self.assertEqual(stats['total_jobs'], 0)
        self.assertEqual(stats['by_status']['new'], 0)

    def test_get_stats_with_jobs(self):
        """Test getting stats with jobs"""
        self.db.add_job(**self.sample_job)
        
        job2 = self.sample_job.copy()
        job2['url'] = 'https://example.com/job/999'
        job_id2 = self.db.add_job(**job2)
        self.db.update_status(job_id2, 'applied')
        
        stats = self.db.get_stats()
        self.assertEqual(stats['total_jobs'], 2)
        self.assertEqual(stats['by_status']['new'], 1)
        self.assertEqual(stats['by_status']['applied'], 1)

    def test_get_platform_stats(self):
        """Test getting platform statistics"""
        self.db.add_job(**self.sample_job)
        
        job2 = self.sample_job.copy()
        job2['url'] = 'https://example.com/job/888'
        job2['platform'] = 'LinkedIn'
        self.db.add_job(**job2)
        
        stats = self.db.get_stats()
        self.assertIn('by_platform', stats)
        self.assertGreater(stats['by_platform']['Indeed'], 0)
        self.assertGreater(stats['by_platform']['LinkedIn'], 0)

    # ===== EDGE CASES =====

    def test_empty_description(self):
        """Test job with empty description"""
        job = self.sample_job.copy()
        job['description'] = ''
        job_id = self.db.add_job(**job)
        self.assertIsNotNone(job_id)

    def test_very_long_description(self):
        """Test job with very long description"""
        job = self.sample_job.copy()
        job['description'] = 'A' * 10000  # 10K characters
        job_id = self.db.add_job(**job)
        self.assertIsNotNone(job_id)

    def test_special_characters(self):
        """Test job with special characters"""
        job = self.sample_job.copy()
        job['title'] = "C++ Developer (Senior) - $$$"
        job['company'] = "O'Reilly & Associates"
        job_id = self.db.add_job(**job)
        self.assertIsNotNone(job_id)

    def test_unicode_characters(self):
        """Test job with unicode characters"""
        job = self.sample_job.copy()
        job['company'] = 'Café Résumé 日本 🚀'
        job_id = self.db.add_job(**job)
        retrieved = self.db.get_job_by_id(job_id)
        self.assertEqual(retrieved['company'], job['company'])

    # ===== DATE HANDLING TESTS =====

    def test_date_posted_formats(self):
        """Test different date formats"""
        job = self.sample_job.copy()
        
        # ISO format
        job['date_posted'] = '2025-10-28'
        job['url'] = 'https://example.com/1'
        job_id = self.db.add_job(**job)
        self.assertIsNotNone(job_id)
        
        # US format
        job['date_posted'] = '10/28/2025'
        job['url'] = 'https://example.com/2'
        job_id = self.db.add_job(**job)
        self.assertIsNotNone(job_id)

    def test_old_job_posting(self):
        """Test job with old posting date"""
        job = self.sample_job.copy()
        job['date_posted'] = '2020-01-01'
        job_id = self.db.add_job(**job)
        self.assertIsNotNone(job_id)

    # ===== BULK OPERATIONS TESTS =====

    def test_bulk_add_jobs(self):
        """Test adding multiple jobs efficiently"""
        jobs = []
        for i in range(10):
            job = self.sample_job.copy()
            job['url'] = f'https://example.com/job/{i}'
            job['title'] = f'Developer {i}'
            jobs.append(job)
        
        for job in jobs:
            self.db.add_job(**job)
        
        all_jobs = self.db.get_all_jobs()
        self.assertGreaterEqual(len(all_jobs), 10)

    def test_bulk_update_status(self):
        """Test updating multiple job statuses"""
        job_ids = []
        for i in range(5):
            job = self.sample_job.copy()
            job['url'] = f'https://example.com/bulk/{i}'
            job_id = self.db.add_job(**job)
            job_ids.append(job_id)
        
        for job_id in job_ids:
            self.db.update_status(job_id, 'applied')
        
        stats = self.db.get_stats()
        self.assertEqual(stats['by_status']['applied'], 5)

    # ===== CLEANUP TESTS =====

    def test_connection_close(self):
        """Test database connection closes properly"""
        try:
            self.db.close()
        except Exception as e:
            self.fail(f"close() raised {type(e).__name__} unexpectedly")

    def test_reopen_connection(self):
        """Test reopening database after close"""
        self.db.close()
        new_db = JobDatabase(self.test_db_path)
        jobs = new_db.get_all_jobs()
        self.assertIsInstance(jobs, list)
        new_db.close()


if __name__ == '__main__':
    unittest.main()
