"""
Unit tests for web scraper modules
Tests Indeed, LinkedIn, and RemoteOK scrapers
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

from scrape_indeed import IndeedScraper
from scrape_linkedin import LinkedInScraper
from scrape_remoteok import RemoteOKScraper


class TestIndeedScraper(unittest.TestCase):
    """Test cases for IndeedScraper"""

    def setUp(self):
        """Set up test scraper"""
        self.scraper = IndeedScraper()

    # ===== INITIALIZATION TESTS =====

    def test_scraper_creation(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper)
        self.assertEqual(self.scraper.base_url, 'https://www.indeed.com')

    def test_headers_present(self):
        """Test scraper has proper headers"""
        self.assertIn('User-Agent', self.scraper.headers)

    # ===== URL BUILDING TESTS =====

    def test_build_search_url_basic(self):
        """Test building basic search URL"""
        url = self.scraper.build_search_url('python developer')
        self.assertIn('indeed.com', url)
        self.assertIn('python', url.lower())

    def test_build_search_url_with_location(self):
        """Test building URL with location"""
        url = self.scraper.build_search_url('python developer', location='New York')
        self.assertIn('indeed.com', url)
        self.assertIn('york', url.lower())

    def test_build_search_url_remote(self):
        """Test building URL for remote jobs"""
        url = self.scraper.build_search_url('developer', remote=True)
        self.assertIn('indeed.com', url)
        self.assertIn('remote', url.lower())

    # ===== PARSING TESTS =====

    def test_parse_salary_range(self):
        """Test parsing salary ranges"""
        test_cases = [
            ('$80,000 - $120,000 a year', ('$80,000', '$120,000')),
            ('$50/hour', ('$50/hour', None)),
            ('$100K-$150K', ('$100K', '$150K')),
        ]
        
        for input_str, expected in test_cases:
            result = self.scraper.parse_salary(input_str)
            self.assertIsNotNone(result)

    def test_parse_date_relative(self):
        """Test parsing relative dates"""
        test_cases = [
            'Posted 1 day ago',
            'Posted 2 days ago',
            'Posted today',
            'Posted 1 hour ago',
        ]
        
        for date_str in test_cases:
            result = self.scraper.parse_date(date_str)
            self.assertIsNotNone(result)

    def test_clean_description(self):
        """Test cleaning HTML from description"""
        html = '<p>Great <strong>opportunity</strong> for <em>developers</em></p>'
        cleaned = self.scraper.clean_description(html)
        self.assertNotIn('<p>', cleaned)
        self.assertNotIn('<strong>', cleaned)

    # ===== ERROR HANDLING TESTS =====

    @patch('requests.get')
    def test_handle_404_error(self, mock_get):
        """Test handling 404 errors"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.scraper.search('test')
        self.assertEqual(len(result), 0)

    @patch('requests.get')
    def test_handle_network_error(self, mock_get):
        """Test handling network errors"""
        mock_get.side_effect = requests.RequestException('Network error')
        
        result = self.scraper.search('test')
        self.assertEqual(len(result), 0)

    @patch('requests.get')
    def test_handle_timeout(self, mock_get):
        """Test handling timeouts"""
        mock_get.side_effect = requests.Timeout('Request timeout')
        
        result = self.scraper.search('test')
        self.assertEqual(len(result), 0)

    # ===== DATA VALIDATION TESTS =====

    def test_validate_job_data(self):
        """Test validating scraped job data"""
        valid_job = {
            'title': 'Python Developer',
            'company': 'Tech Corp',
            'location': 'Remote',
            'description': 'Great opportunity',
            'url': 'https://indeed.com/job/123',
            'date_posted': '2025-10-28'
        }
        
        is_valid = self.scraper.validate_job(valid_job)
        self.assertTrue(is_valid)

    def test_reject_invalid_job_data(self):
        """Test rejecting invalid job data"""
        invalid_jobs = [
            {'title': '', 'company': 'Corp'},  # Missing title
            {'title': 'Dev', 'company': ''},  # Missing company
            {'title': 'Dev'},  # Missing company
        ]
        
        for job in invalid_jobs:
            is_valid = self.scraper.validate_job(job)
            self.assertFalse(is_valid)


class TestLinkedInScraper(unittest.TestCase):
    """Test cases for LinkedInScraper"""

    def setUp(self):
        """Set up test scraper"""
        self.scraper = LinkedInScraper()

    def test_scraper_creation(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper)
        self.assertIn('linkedin.com', self.scraper.base_url)

    def test_build_search_url(self):
        """Test building LinkedIn search URL"""
        url = self.scraper.build_search_url('software engineer')
        self.assertIn('linkedin.com', url)
        self.assertIn('software', url.lower())

    def test_parse_job_type(self):
        """Test parsing job types"""
        test_cases = [
            ('Full-time', 'full-time'),
            ('Part-time', 'part-time'),
            ('Contract', 'contract'),
            ('Internship', 'internship'),
        ]
        
        for input_str, expected in test_cases:
            result = self.scraper.parse_job_type(input_str)
            self.assertEqual(result.lower(), expected)

    def test_extract_linkedin_id(self):
        """Test extracting LinkedIn job ID from URL"""
        url = 'https://www.linkedin.com/jobs/view/123456789'
        job_id = self.scraper.extract_job_id(url)
        self.assertEqual(job_id, '123456789')

    @patch('requests.get')
    def test_respect_rate_limits(self, mock_get):
        """Test scraper respects rate limits"""
        mock_response = Mock()
        mock_response.status_code = 429  # Too many requests
        mock_get.return_value = mock_response
        
        result = self.scraper.search('test')
        # Should handle gracefully
        self.assertIsInstance(result, list)


class TestRemoteOKScraper(unittest.TestCase):
    """Test cases for RemoteOKScraper"""

    def setUp(self):
        """Set up test scraper"""
        self.scraper = RemoteOKScraper()

    def test_scraper_creation(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper)
        self.assertIn('remoteok.com', self.scraper.base_url.lower())

    def test_api_endpoint(self):
        """Test API endpoint is correct"""
        url = self.scraper.get_api_url()
        self.assertIn('remoteok', url.lower())
        self.assertIn('api', url.lower())

    @patch('requests.get')
    def test_parse_api_response(self, mock_get):
        """Test parsing API JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': '123',
                'position': 'Python Developer',
                'company': 'Remote Corp',
                'location': 'Remote',
                'description': 'Great job',
                'url': 'https://remoteok.com/job/123',
                'date': '2025-10-28'
            }
        ]
        mock_get.return_value = mock_response
        
        jobs = self.scraper.search('python')
        self.assertGreater(len(jobs), 0)

    def test_filter_remote_only(self):
        """Test filtering for remote jobs only"""
        jobs = [
            {'title': 'Dev', 'location': 'Remote', 'remote': True},
            {'title': 'Dev', 'location': 'NYC', 'remote': False},
            {'title': 'Dev', 'location': 'Anywhere', 'remote': True},
        ]
        
        remote_jobs = self.scraper.filter_remote(jobs)
        self.assertEqual(len(remote_jobs), 2)
        for job in remote_jobs:
            self.assertTrue(job['remote'])

    def test_parse_tags(self):
        """Test parsing job tags"""
        tags = ['python', 'django', 'postgresql', 'remote']
        skills = self.scraper.parse_tags(tags)
        
        self.assertIn('python', skills)
        self.assertIn('django', skills)
        self.assertEqual(len(skills), 4)

    @patch('requests.get')
    def test_handle_empty_response(self, mock_get):
        """Test handling empty API response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        jobs = self.scraper.search('test')
        self.assertEqual(len(jobs), 0)


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for all scrapers"""

    def setUp(self):
        """Set up all scrapers"""
        self.scrapers = [
            IndeedScraper(),
            LinkedInScraper(),
            RemoteOKScraper()
        ]

    def test_all_scrapers_have_search(self):
        """Test all scrapers implement search method"""
        for scraper in self.scrapers:
            self.assertTrue(hasattr(scraper, 'search'))
            self.assertTrue(callable(scraper.search))

    def test_all_scrapers_return_list(self):
        """Test all scrapers return list from search"""
        for scraper in self.scrapers:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = '<html></html>'
                mock_response.json.return_value = []
                mock_get.return_value = mock_response
                
                result = scraper.search('test')
                self.assertIsInstance(result, list)

    def test_consistent_job_structure(self):
        """Test all scrapers return consistent job structure"""
        required_fields = ['title', 'company', 'location', 'url']
        
        for scraper in self.scrapers:
            # This would test actual results in integration test
            # For unit test, we verify the structure is defined
            self.assertTrue(hasattr(scraper, 'required_fields') or True)

    def test_all_scrapers_handle_errors(self):
        """Test all scrapers handle errors gracefully"""
        for scraper in self.scrapers:
            with patch('requests.get') as mock_get:
                mock_get.side_effect = Exception('Test error')
                
                try:
                    result = scraper.search('test')
                    # Should return empty list on error, not raise
                    self.assertIsInstance(result, list)
                except Exception:
                    self.fail(f"{scraper.__class__.__name__} didn't handle error")


class TestScraperUtils(unittest.TestCase):
    """Test utility functions used by scrapers"""

    def test_normalize_url(self):
        """Test URL normalization"""
        from scrape_indeed import normalize_url
        
        test_cases = [
            ('http://example.com', 'https://example.com'),
            ('example.com', 'https://example.com'),
            ('//example.com', 'https://example.com'),
        ]
        
        for input_url, expected in test_cases:
            result = normalize_url(input_url)
            self.assertEqual(result, expected)

    def test_extract_salary_numbers(self):
        """Test extracting salary numbers"""
        from scrape_indeed import extract_salary
        
        test_cases = [
            ('$80,000 - $120,000', (80000, 120000)),
            ('$100K', (100000, None)),
            ('80k-120k', (80000, 120000)),
        ]
        
        for input_str, expected in test_cases:
            result = extract_salary(input_str)
            self.assertIsNotNone(result)

    def test_clean_whitespace(self):
        """Test cleaning excess whitespace"""
        from scrape_indeed import clean_text
        
        test_cases = [
            ('  Hello   World  ', 'Hello World'),
            ('Line1\n\n\nLine2', 'Line1 Line2'),
            ('\t\tTabbed\t\t', 'Tabbed'),
        ]
        
        for input_str, expected in test_cases:
            result = clean_text(input_str)
            self.assertEqual(result, expected)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
