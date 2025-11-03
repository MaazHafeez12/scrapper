import os
import unittest
from urllib.parse import urlencode

# Ensure app uses a temp DB path if imported by other tests later
os.environ.setdefault('DB_PATH', 'output/test_jobs.db')

from api.index import compute_canonical_hash, is_probable_job_link, parse_job_page, extract_domain


class TestCanonicalization(unittest.TestCase):
    def test_hash_ignores_query_and_fragment(self):
        base = 'https://example.com/jobs/12345'
        u1 = base + '?utm_source=newsletter#top'
        u2 = base + '?a=1&b=2'
        self.assertEqual(compute_canonical_hash(u1), compute_canonical_hash(u2))

    def test_hash_differs_for_different_paths(self):
        u1 = 'https://example.com/jobs/12345'
        u2 = 'https://example.com/jobs/12346'
        self.assertNotEqual(compute_canonical_hash(u1), compute_canonical_hash(u2))

    def test_hash_keeps_scheme_and_host(self):
        # Different hosts => different hashes
        u1 = 'https://example.com/jobs/12345'
        u2 = 'https://example.org/jobs/12345'
        self.assertNotEqual(compute_canonical_hash(u1), compute_canonical_hash(u2))

        # Different scheme => different hashes (function preserves scheme)
        u3 = 'http://example.com/jobs/12345'
        self.assertNotEqual(compute_canonical_hash(u1), compute_canonical_hash(u3))


class TestJobLinkHeuristics(unittest.TestCase):
    def test_keywords_detect_job_links(self):
        base_domain = 'example.com'
        self.assertTrue(is_probable_job_link('https://example.com/jobs/123', base_domain))
        self.assertTrue(is_probable_job_link('https://example.com/careers/backend-dev', base_domain))
        self.assertTrue(is_probable_job_link('https://board.example.com/position/42', base_domain))

    def test_same_domain_non_root_path(self):
        base_domain = 'example.com'
        # Same domain, non-empty path -> True
        self.assertTrue(is_probable_job_link('https://example.com/listings', base_domain))
        # Root path only -> False
        self.assertFalse(is_probable_job_link('https://example.com/', base_domain))

    def test_non_job_external_link(self):
        base_domain = 'example.com'
        self.assertFalse(is_probable_job_link('https://blog.other.com/article', base_domain))


class TestParseJobPage(unittest.TestCase):
    def test_parse_basic_html(self):
        html = '''
        <html>
          <head>
            <link rel="canonical" href="https://jobs.example.com/postings/abc"/>
            <meta property="og:site_name" content="Example Inc"/>
            <title>Ignored Title</title>
          </head>
          <body>
            <h1>Senior Python Developer</h1>
            <div class="location">Remote - US</div>
            <article>
              <p>We are hiring a Python developer to build services.</p>
            </article>
          </body>
        </html>
        '''
        url = 'https://jobs.example.com/postings/abc?ref=homepage'
        job = parse_job_page(url, html)
        self.assertEqual(job['url'], 'https://jobs.example.com/postings/abc')
        self.assertEqual(job['title'], 'Senior Python Developer')
        self.assertEqual(job['company'], 'Example Inc')
        self.assertIn('Remote', job['location'])
        self.assertIn('Python developer', job['description'])
        self.assertEqual(job['platform'], extract_domain(url))


if __name__ == '__main__':
    unittest.main(verbosity=2)
