import os
import tempfile
import unittest

os.environ.setdefault('DB_PATH', tempfile.mkstemp(prefix='test_alias_', suffix='.db')[1])
os.environ.setdefault('APP_SECRET', 'test-secret')

from api.index import app


class TestAliasRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_enqueue_alias_without_worker_config(self):
        # No WORKER_WEBHOOK_URL/SECRET set -> expect 501
        r = self.client.post('/api/enqueue', json={'urls': ['https://example.com/jobs']})
        self.assertEqual(r.status_code, 501)
        d = r.get_json(); self.assertFalse(d.get('success'))

    def test_jobs_and_leads_alias_exist(self):
        rj = self.client.get('/api/jobs')
        rl = self.client.get('/api/leads')
        # endpoints should exist; may return 200 with empty/fallback data
        self.assertIn(rj.status_code, (200, 500))
        self.assertIn(rl.status_code, (200, 500))


if __name__ == '__main__':
    unittest.main(verbosity=2)
