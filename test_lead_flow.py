import os
import tempfile
import unittest
from datetime import datetime

os.environ.setdefault('DB_PATH', tempfile.mkstemp(prefix='test_leads_', suffix='.db')[1])

from api.index import enhance_job_data, app, db


class TestLeadFlow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_job_to_lead(self):
        job = {
            'title': 'Senior Python Developer',
            'company': 'Example Inc',
            'location': 'Remote',
            'platform': 'WeWorkRemotely',
            'url': 'https://example.com/jobs/xyz',
            'description': 'We are hiring a Python developer with AWS and Docker',
            'date_posted': datetime.utcnow().strftime('%Y-%m-%d')
        }
        enhanced = enhance_job_data(job)
        self.assertIn('lead_score', enhanced)
        # Fetch leads endpoint for min_score=40
        r = self.client.get('/api/read-leads?min_score=40&limit=10')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get('success'))
        results = data.get('results') or []
        # At least one lead present in either DB or in-memory fallback
        self.assertGreaterEqual(len(results), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
