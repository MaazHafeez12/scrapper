import os
import tempfile
import unittest
from database import JobDatabase


class TestDedupeMinimal(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(prefix='test_dedupe_', suffix='.db')
        self.db = JobDatabase(self.db_path)

    def tearDown(self):
        try:
            os.close(self.db_fd)
            os.unlink(self.db_path)
        except Exception:
            pass

    def test_insert_duplicate_title_company_platform(self):
        job = {
            'title': 'Backend Engineer',
            'company': 'Acme Co',
            'platform': 'WeWorkRemotely',
            'url': 'https://acme.example/jobs/1',
            'description': 'Build services',
        }
        self.db.insert_job(job)
        # inserting again should update last_seen, not create a new entry via save_jobs
        res = self.db.save_jobs([job])
        self.assertEqual(res['new'], 0)
        self.assertEqual(res['updated'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
