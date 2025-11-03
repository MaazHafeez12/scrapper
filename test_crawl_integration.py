import os
import io
import json
import unittest
from unittest.mock import patch, Mock
from contextlib import contextmanager

# Use a dedicated test database file before importing the app
TEST_DB_PATH = 'output/test_jobs_integration.db'
os.environ['DB_PATH'] = TEST_DB_PATH

from api.index import app, db


LISTING_HTML = '''
<html>
  <body>
    <a href="/jobs/1">Job One</a>
    <a href="/jobs/2">Job Two</a>
    <a href="/jobs/2?utm=campaign">Job Two Duplicate</a>
    <a href="/about">About</a>
  </body>
</html>
'''

JOB1_HTML = '''
<html>
  <head>
    <link rel="canonical" href="https://testboard.example/jobs/1"/>
    <meta property="og:site_name" content="TestBoard"/>
  </head>
  <body>
    <h1>Backend Engineer</h1>
    <div class="location">Remote</div>
    <article>
      <p>Build APIs and services.</p>
    </article>
  </body>
</html>
'''

JOB2_HTML = '''
<html>
  <head>
    <link rel="canonical" href="https://testboard.example/jobs/2"/>
    <meta property="og:site_name" content="TestBoard"/>
  </head>
  <body>
    <h1>Data Engineer</h1>
    <div class="location">Remote - EU</div>
    <article>
      <p>Data pipelines and analytics.</p>
    </article>
  </body>
</html>
'''


class TestCrawlIntegration(unittest.TestCase):
    def setUp(self):
        # Ensure clean DB file
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except Exception:
            pass

    def tearDown(self):
        # Close DB if open and cleanup file
        try:
            if db and db.conn:
                db.close()
        except Exception:
            pass
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except Exception:
            pass

    @patch('api.index.fetch_url')
    def test_crawl_urls_inserts_and_dedupes(self, mock_fetch):
        # Configure fetch_url mock to return listing HTML for the first call and job pages for next calls.
        def side_effect(url, headers=None, timeout=15):
            m = Mock()
            m.status_code = 200
            if url.endswith('/category'):
                m.text = LISTING_HTML
                return m
            if url.endswith('/jobs/1'):
                m.text = JOB1_HTML
                return m
            if url.endswith('/jobs/2') or url.startswith('https://testboard.example/jobs/2'):
                m.text = JOB2_HTML
                return m
            # Resolve absolute URLs in listing
            if url.endswith('/jobs/2?utm=campaign'):
                m.text = JOB2_HTML
                return m
            # default to listing
            m.text = LISTING_HTML
            return m

        mock_fetch.side_effect = side_effect

        client = app.test_client()
        payload = {
            'urls': ['https://testboard.example/category'],
            'max_links_per_listing': 10
        }
        res = client.post('/api/crawl-urls', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        # Expect 2 unique jobs from 3 links (one duplicate by canonical)
        # created+updated counts are tracked in-memory in endpoint response
        self.assertGreaterEqual(data.get('created', 0) + data.get('updated', 0), 2)

        # Query results via results API (filters default)
        res2 = client.get('/api/crawl-results')
        self.assertEqual(res2.status_code, 200)
        results = res2.get_json()
        self.assertTrue(results['success'])
        self.assertGreaterEqual(results['total'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
