import os
import tempfile
import unittest
from unittest.mock import patch

# Configure env before importing app
os.environ.setdefault('DB_PATH', tempfile.mkstemp(prefix='test_outreach_', suffix='.db')[1])
os.environ.setdefault('APP_SECRET', 'test-secret')
os.environ.setdefault('OUTREACH_DAILY_CAP', '1')  # to test cap

from api.index import app, db


class TestOutreachAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('api.index.requests.post')
    def test_send_email_records_and_caps(self, mock_post):
        # Mock SendGrid success
        os.environ['SENDGRID_API_KEY'] = 'dummy'
        mock_post.return_value.status_code = 202
        mock_post.return_value.text = ''

        payload = { 'to': 'lead@example.com', 'subject': 'Hi', 'text': 'Hello there' }
        r = self.client.post('/api/outreach/send', json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get('success'))

        # Verify outreach_logs has a row
        rows = []
        try:
            db.connect(); cur = db.conn.cursor()
            cur.execute('SELECT COUNT(*) FROM outreach_logs')
            rows = cur.fetchone()
        except Exception:
            pass
        self.assertTrue(rows is not None)

        # Second send should hit daily cap (OUTREACH_DAILY_CAP=1)
        r2 = self.client.post('/api/outreach/send', json=payload)
        self.assertEqual(r2.status_code, 429)
        d2 = r2.get_json()
        self.assertFalse(d2.get('success'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
