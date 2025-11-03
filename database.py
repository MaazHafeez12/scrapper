"""Database manager for job storage and tracking."""
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import os


class JobDatabase:
    """Manage job data in SQLite database."""
    
    def __init__(self, db_path: str = 'output/jobs.db'):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure parent directory exists; handle bare filenames gracefully
        dir_name = os.path.dirname(db_path) or '.'
        os.makedirs(dir_name, exist_ok=True)
        self.conn = None
        self.create_tables()
        
    def connect(self):
        """Create database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def create_tables(self):
        """Create database tables if they don't exist."""
        self.connect()
        
        cursor = self.conn.cursor()
        
        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                salary TEXT,
                budget TEXT,
                date_posted TEXT,
                description TEXT,
                url TEXT,
                platform TEXT NOT NULL,
                remote BOOLEAN DEFAULT 0,
                job_type TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                notes TEXT
            )
        ''')
        
        # Job history table (track changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')
        
        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keywords TEXT,
                location TEXT,
                remote BOOLEAN,
                platforms TEXT,
                jobs_found INTEGER,
                new_jobs INTEGER,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Scraped sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                total_jobs INTEGER,
                new_jobs INTEGER,
                updated_jobs INTEGER,
                platforms TEXT,
                filters TEXT
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(job_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote)')
        
        self.conn.commit()

        # Outreach templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT,
                subject TEXT,
                body TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Outreach logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                job_id INTEGER,
                to_email TEXT NOT NULL,
                to_domain TEXT,
                subject TEXT,
                body TEXT,
                transport TEXT, -- sendgrid | smtp | mailgun
                status TEXT,    -- queued | scheduled | sent | delivered | bounced | opened | clicked | replied | failed
                provider_msg_id TEXT,
                sequence_name TEXT,
                sequence_step INTEGER,
                template_id TEXT,
                scheduled_for TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                delivered_at TIMESTAMP,
                opened_at TIMESTAMP,
                replied_at TIMESTAMP,
                error TEXT,
                metadata TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_logs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outreach_sent_at ON outreach_logs(sent_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outreach_sched ON outreach_logs(scheduled_for)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outreach_domain ON outreach_logs(to_domain)')
        self.conn.commit()

        # Ensure contact/lead columns exist on jobs table (migration-safe)
        cursor.execute("PRAGMA table_info(jobs)")
        cols = {row[1] for row in cursor.fetchall()}
        alter_needed = []
        if 'contact_emails' not in cols:
            alter_needed.append("ADD COLUMN contact_emails TEXT")
        if 'contact_sources' not in cols:
            alter_needed.append("ADD COLUMN contact_sources TEXT")
        if 'contact_checked_at' not in cols:
            alter_needed.append("ADD COLUMN contact_checked_at TIMESTAMP")
        if 'company_domain' not in cols:
            alter_needed.append("ADD COLUMN company_domain TEXT")
        if 'poster_name' not in cols:
            alter_needed.append("ADD COLUMN poster_name TEXT")
        if 'date_posted' not in cols:
            alter_needed.append("ADD COLUMN date_posted TEXT")
        if 'budget' not in cols:
            alter_needed.append("ADD COLUMN budget TEXT")
        # Crawl-related columns
        if 'source_listing' not in cols:
            alter_needed.append("ADD COLUMN source_listing TEXT")
        if 'crawled_at' not in cols:
            alter_needed.append("ADD COLUMN crawled_at TIMESTAMP")
        if 'lead_score' not in cols:
            alter_needed.append("ADD COLUMN lead_score INTEGER")
        for stmt in alter_needed:
            cursor.execute(f"ALTER TABLE jobs {stmt}")
        if alter_needed:
            self.conn.commit()

        # Contacts normalization tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                domain TEXT,
                mx_ok BOOLEAN,
                do_not_contact BOOLEAN DEFAULT 0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_contacts (
                job_id INTEGER NOT NULL,
                contact_id INTEGER NOT NULL,
                source TEXT,
                type TEXT,
                confidence REAL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (job_id, contact_id),
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_contacts_job ON job_contacts(job_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_contacts_conf ON job_contacts(confidence)')
        self.conn.commit()

        # Crawl logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                listing_url TEXT,
                status TEXT,
                found_count INTEGER,
                error_message TEXT,
                started_at TIMESTAMP,
                finished_at TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_logs_started ON crawl_logs(started_at)')
        self.conn.commit()
        
    def generate_job_hash(self, job: Dict) -> str:
        """Generate unique hash for a job.
        
        Args:
            job: Job dictionary
            
        Returns:
            Hash string
        """
        # Use title, company, and platform to create unique identifier
        key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('platform', '')}"
        return key.lower().strip()
        
    def job_exists(self, job_hash: str) -> Optional[int]:
        """Check if job already exists in database.
        
        Args:
            job_hash: Job hash to check
            
        Returns:
            Job ID if exists, None otherwise
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT id FROM jobs WHERE job_hash = ?', (job_hash,))
        result = cursor.fetchone()
        
        return result['id'] if result else None

    def job_exists_by_url(self, url: str) -> Optional[int]:
        """Check if a job exists by canonical URL.

        Args:
            url: Canonical URL to check
        Returns:
            Job ID if exists, None otherwise
        """
        if not url:
            return None
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM jobs WHERE url = ?', (url,))
        row = cursor.fetchone()
        return row['id'] if row else None

    def job_exists_by_title_company_date(self, title: str, company: str, date_posted: Optional[str]) -> Optional[int]:
        """Check for likely duplicates by title+company+date_posted.

        Returns Job ID if a match is found, else None.
        """
        self.connect()
        cursor = self.conn.cursor()
        if date_posted:
            cursor.execute('''
                SELECT id FROM jobs
                WHERE LOWER(title)=LOWER(?) AND LOWER(company)=LOWER(?) AND date_posted = ?
                ORDER BY first_seen DESC LIMIT 1
            ''', (title or '', company or '', date_posted))
        else:
            cursor.execute('''
                SELECT id FROM jobs
                WHERE LOWER(title)=LOWER(?) AND LOWER(company)=LOWER(?)
                ORDER BY first_seen DESC LIMIT 1
            ''', (title or '', company or ''))
        row = cursor.fetchone()
        return row['id'] if row else None
        
    def insert_job(self, job: Dict) -> int:
        """Insert new job into database.
        
        Args:
            job: Job dictionary
            
        Returns:
            Job ID
        """
        self.connect()
        cursor = self.conn.cursor()
        
        job_hash = self.generate_job_hash(job)
        
        # Normalize budget/salary and date_posted
        salary = job.get('salary', '') or job.get('salary_range', '') or job.get('budget', '')
        budget = job.get('budget', '') or job.get('salary', '') or job.get('salary_range', '')
        date_posted = job.get('date_posted', '') or job.get('posted_at', '')

        cursor.execute('''
            INSERT INTO jobs (
                job_hash, title, company, location, salary, budget, date_posted, description,
                url, platform, remote, job_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
        ''', (
            job_hash,
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            salary,
            budget,
            date_posted,
            job.get('description', ''),
            job.get('url', ''),
            job.get('platform', ''),
            1 if job.get('remote', False) else 0,
            job.get('job_type', '')
        ))
        
        self.conn.commit()
        return cursor.lastrowid
        
    def update_job_last_seen(self, job_id: int):
        """Update last_seen timestamp for existing job.
        
        Args:
            job_id: Job ID to update
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE jobs SET last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (job_id,))
        
        self.conn.commit()

    def update_job_extra(self, job_id: int, source_listing: Optional[str] = None,
                         crawled_at: Optional[str] = None, lead_score: Optional[int] = None):
        """Update extra fields for a job row.

        Args:
            job_id: Job ID to update
            source_listing: Listing page URL this job was discovered from
            crawled_at: ISO timestamp of crawl
            lead_score: Optional computed score
        """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE jobs
            SET source_listing = COALESCE(?, source_listing),
                crawled_at = COALESCE(?, crawled_at),
                lead_score = COALESCE(?, lead_score)
            WHERE id = ?
        ''', (source_listing, crawled_at, lead_score, job_id))
        self.conn.commit()
        
    def save_jobs(self, jobs: List[Dict]) -> Dict[str, int]:
        """Save jobs to database, tracking new vs existing.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Dictionary with counts: {new, updated, total}
        """
        new_count = 0
        updated_count = 0
        
        for job in jobs:
            job_hash = self.generate_job_hash(job)
            job_id = self.job_exists(job_hash)
            
            if job_id:
                # Job exists, update last_seen
                self.update_job_last_seen(job_id)
                updated_count += 1
            else:
                # New job
                self.insert_job(job)
                new_count += 1
                
        return {
            'new': new_count,
            'updated': updated_count,
            'total': len(jobs)
        }
        
    def get_new_jobs(self, since_hours: int = 24) -> List[Dict]:
        """Get jobs added in the last N hours.
        
        Args:
            since_hours: Number of hours to look back
            
        Returns:
            List of job dictionaries
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM jobs
            WHERE first_seen >= datetime('now', '-' || ? || ' hours')
            ORDER BY first_seen DESC
        ''', (since_hours,))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Fetch a single job row by id as dict."""
        self.connect()
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def save_job_contacts(self, job_id: int, emails: List[str], sources: Dict[str, Dict], company_domain: Optional[str] = None):
        """Persist contact info for a job.

        Args:
            job_id: Job ID
            emails: List of unique emails
            sources: Mapping email -> {source: str, verified: bool, type: 'extracted'|'guessed'}
            company_domain: Optional company domain
        """
        self.connect()
        cur = self.conn.cursor()
        cur.execute('''
            UPDATE jobs
            SET contact_emails = ?,
                contact_sources = ?,
                contact_checked_at = CURRENT_TIMESTAMP,
                company_domain = COALESCE(?, company_domain)
            WHERE id = ?
        ''', (
            json.dumps(emails or []),
            json.dumps(sources or {}),
            company_domain,
            job_id,
        ))
        self.conn.commit()

    def save_contacts_normalized(self, job_id: int, emails: List[str], sources: Dict[str, Dict],
                                 company_domain: Optional[str], mx_ok: Optional[bool],
                                 confidence: Optional[Dict[str, float]] = None):
        """Normalize contacts into contacts and job_contacts tables, with confidence.

        Upserts contacts by email; sets/updates domain and mx_ok if provided.
        Then upserts job_contacts with confidence and metadata.
        """
        self.connect()
        cur = self.conn.cursor()
        for e in emails:
            dom = (e.split('@')[-1]).lower() if '@' in e else None
            # Upsert contact
            cur.execute('INSERT OR IGNORE INTO contacts(email, domain, mx_ok) VALUES(?,?,?)', (e, dom, mx_ok if mx_ok is not None else None))
            # If exists, update domain/mx_ok/last_seen
            cur.execute('UPDATE contacts SET domain = COALESCE(?, domain), mx_ok = COALESCE(?, mx_ok), last_seen = CURRENT_TIMESTAMP WHERE email = ?', (dom, mx_ok if mx_ok is not None else None, e))
            # Get contact_id
            cur.execute('SELECT id FROM contacts WHERE email = ?', (e,))
            row = cur.fetchone()
            if not row:
                continue
            cid = row['id'] if isinstance(row, sqlite3.Row) else row[0]
            meta = sources.get(e, {})
            conf = (confidence or {}).get(e)
            # Upsert job_contacts
            cur.execute('''
                INSERT INTO job_contacts(job_id, contact_id, source, type, confidence)
                VALUES(?,?,?,?,?)
                ON CONFLICT(job_id, contact_id) DO UPDATE SET
                    source=excluded.source,
                    type=excluded.type,
                    confidence=COALESCE(excluded.confidence, job_contacts.confidence),
                    last_seen=CURRENT_TIMESTAMP
            ''', (job_id, cid, meta.get('source'), meta.get('type'), conf))
        self.conn.commit()

    def ensure_contacts_columns(self):
        """Add missing contacts columns (like do_not_contact) if not present."""
        self.connect()
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(contacts)")
        cols = {row[1] for row in cur.fetchall()}
        if 'do_not_contact' not in cols:
            try:
                cur.execute("ALTER TABLE contacts ADD COLUMN do_not_contact BOOLEAN DEFAULT 0")
                self.conn.commit()
            except Exception:
                pass

    def mark_do_not_contact(self, email: Optional[str] = None, domain: Optional[str] = None, lead_id: Optional[int] = None):
        """Mark a contact or domain as do-not-contact. Also updates business_leads status when possible."""
        self.ensure_contacts_columns()
        self.connect()
        cur = self.conn.cursor()
        if email:
            dom = (email.split('@')[-1]).lower() if '@' in email else None
            cur.execute('INSERT OR IGNORE INTO contacts(email, domain, do_not_contact) VALUES(?,?,1)', (email, dom,))
            cur.execute('UPDATE contacts SET do_not_contact = 1, last_seen = CURRENT_TIMESTAMP WHERE email = ?', (email,))
        if domain:
            cur.execute('UPDATE contacts SET do_not_contact = 1, last_seen = CURRENT_TIMESTAMP WHERE LOWER(domain)=LOWER(?)', (domain,))
        if lead_id:
            try:
                cur.execute("UPDATE business_leads SET contact_status = 'do_not_contact' WHERE id = ?", (lead_id,))
            except Exception:
                pass
        self.conn.commit()

    def is_do_not_contact(self, email: Optional[str] = None) -> bool:
        self.ensure_contacts_columns()
        if not email:
            return False
        self.connect()
        cur = self.conn.cursor()
        cur.execute('SELECT do_not_contact FROM contacts WHERE email = ?', (email,))
        row = cur.fetchone()
        if not row:
            return False
        val = row[0] if not isinstance(row, dict) else row.get('do_not_contact')
        try:
            return bool(val)
        except Exception:
            return False

    def query_contacts(self, min_confidence: float = 0.0, platform: Optional[str] = None,
                       keywords: Optional[str] = None, status: Optional[str] = None,
                       remote_only: bool = False) -> List[Dict]:
        """Return flattened joined contacts with job context, filtered by confidence and job filters."""
        self.connect()
        cur = self.conn.cursor()
        sql = '''
            SELECT j.id as job_id, j.title, j.company, j.platform, j.url,
                   c.email, c.domain, c.mx_ok,
                   jc.source, jc.type, jc.confidence,
                   j.first_seen, j.last_seen
            FROM job_contacts jc
            JOIN jobs j ON j.id = jc.job_id
            JOIN contacts c ON c.id = jc.contact_id
            WHERE (jc.confidence IS NULL OR jc.confidence >= ?)
        '''
        params: List = [min_confidence]
        if platform:
            sql += ' AND j.platform = ?'
            params.append(platform)
        if keywords:
            sql += ' AND (j.title LIKE ? OR j.company LIKE ? OR j.description LIKE ?)'
            pattern = f'%{keywords}%'
            params.extend([pattern, pattern, pattern])
        if status:
            sql += ' AND j.status = ?'
            params.append(status)
        if remote_only:
            sql += ' AND j.remote = 1'
        sql += ' ORDER BY jc.confidence DESC NULLS LAST, j.first_seen DESC'
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def query_contacts_for_jobs(self, job_ids: List[int], min_confidence: float = 0.0) -> List[Dict]:
        """Return flattened contacts for a specific set of job IDs."""
        if not job_ids:
            return []
        self.connect()
        cur = self.conn.cursor()
        placeholders = ','.join('?' * len(job_ids))
        sql = f'''
            SELECT j.id as job_id, j.title, j.company, j.platform, j.url,
                   c.email, c.domain, c.mx_ok,
                   jc.source, jc.type, jc.confidence,
                   j.first_seen, j.last_seen
            FROM job_contacts jc
            JOIN jobs j ON j.id = jc.job_id
            JOIN contacts c ON c.id = jc.contact_id
            WHERE (jc.confidence IS NULL OR jc.confidence >= ?)
              AND j.id IN ({placeholders})
            ORDER BY jc.confidence DESC NULLS LAST, j.first_seen DESC
        '''
        params: List = [min_confidence] + job_ids
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
        
    def get_jobs_by_status(self, status: str = 'new') -> List[Dict]:
        """Get jobs by status.
        
        Args:
            status: Job status (new, applied, interested, rejected, archived)
            
        Returns:
            List of job dictionaries
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM jobs WHERE status = ? ORDER BY first_seen DESC', (status,))
        return [dict(row) for row in cursor.fetchall()]
        
    def update_job_status(self, job_id: int, status: str, notes: str = None):
        """Update job status and notes.
        
        Args:
            job_id: Job ID
            status: New status (applied, interested, rejected, archived)
            notes: Optional notes
        """
        self.connect()
        cursor = self.conn.cursor()
        
        # Get old status for history
        cursor.execute('SELECT status FROM jobs WHERE id = ?', (job_id,))
        old_status = cursor.fetchone()['status']
        
        # Update job
        if notes:
            cursor.execute('''
                UPDATE jobs SET status = ?, notes = ?
                WHERE id = ?
            ''', (status, notes, job_id))
        else:
            cursor.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
            
        # Add to history
        cursor.execute('''
            INSERT INTO job_history (job_id, change_type, old_value, new_value)
            VALUES (?, 'status_change', ?, ?)
        ''', (job_id, old_status, status))
        
        self.conn.commit()
        
    def search_jobs(self, keywords: str = None, remote_only: bool = False,
                    platform: str = None, limit: int = 100) -> List[Dict]:
        """Search jobs in database.
        
        Args:
            keywords: Search keywords (searches title, company, description)
            remote_only: Filter for remote jobs only
            platform: Filter by platform
            limit: Maximum results
            
        Returns:
            List of job dictionaries
        """
        self.connect()
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM jobs WHERE 1=1'
        params = []
        
        if keywords:
            query += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ?)'
            keyword_pattern = f'%{keywords}%'
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
        if remote_only:
            query += ' AND remote = 1'
            
        if platform:
            query += ' AND platform = ?'
            params.append(platform)
            
        query += ' ORDER BY first_seen DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
        
    def get_statistics(self) -> Dict:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        self.connect()
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total jobs
        cursor.execute('SELECT COUNT(*) as count FROM jobs')
        stats['total_jobs'] = cursor.fetchone()['count']
        
        # Jobs by status
        cursor.execute('SELECT status, COUNT(*) as count FROM jobs GROUP BY status')
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Jobs by platform
        cursor.execute('SELECT platform, COUNT(*) as count FROM jobs GROUP BY platform')
        stats['by_platform'] = {row['platform']: row['count'] for row in cursor.fetchall()}
        
        # Remote vs non-remote
        cursor.execute('SELECT remote, COUNT(*) as count FROM jobs GROUP BY remote')
        remote_stats = {row['remote']: row['count'] for row in cursor.fetchall()}
        stats['remote_jobs'] = remote_stats.get(1, 0)
        stats['non_remote_jobs'] = remote_stats.get(0, 0)
        
        # New jobs (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) as count FROM jobs
            WHERE first_seen >= datetime('now', '-24 hours')
        ''')
        stats['new_last_24h'] = cursor.fetchone()['count']
        
        # New jobs (last 7 days)
        cursor.execute('''
            SELECT COUNT(*) as count FROM jobs
            WHERE first_seen >= datetime('now', '-7 days')
        ''')
        stats['new_last_7d'] = cursor.fetchone()['count']
        
        return stats
        
    def save_search_history(self, filters: Dict, results: Dict):
        """Save search history.
        
        Args:
            filters: Search filters used
            results: Results dictionary with counts
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (keywords, location, remote, platforms, jobs_found, new_jobs)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            filters.get('keywords', ''),
            filters.get('location', ''),
            1 if filters.get('remote', False) else 0,
            ','.join(filters.get('platforms', [])) if filters.get('platforms') else 'all',
            results.get('total', 0),
            results.get('new', 0)
        ))
        
        self.conn.commit()
        
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent search history.
        
        Args:
            limit: Number of searches to return
            
        Returns:
            List of search dictionaries
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM search_history
            ORDER BY searched_at DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
        
    def cleanup_old_jobs(self, days: int = 30):
        """Remove jobs older than specified days.
        
        Args:
            days: Number of days to keep
        """
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            DELETE FROM jobs
            WHERE last_seen < datetime('now', '-' || ? || ' days')
            AND status = 'new'
        ''', (days,))
        
        deleted = cursor.rowcount
        self.conn.commit()
        
        return deleted
        
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Business Intelligence Methods
    def save_business_lead(self, lead_data: Dict) -> bool:
        """Save business lead to database."""
        try:
            self.connect()
            cursor = self.conn.cursor()
            
            # First ensure business_leads table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    platform TEXT NOT NULL,
                    lead_score INTEGER DEFAULT 0,
                    company_size TEXT,
                    technologies TEXT,
                    contact_potential TEXT,
                    job_url TEXT,
                    date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contact_status TEXT DEFAULT 'New',
                    notes TEXT,
                    UNIQUE(company, title, platform)
                )
            ''')
            
            # Convert technologies list to JSON string
            technologies = json.dumps(lead_data.get('technologies', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO business_leads 
                (company, title, location, platform, lead_score, company_size,
                 technologies, contact_potential, job_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead_data.get('company'),
                lead_data.get('title'),
                lead_data.get('location'),
                lead_data.get('platform'),
                lead_data.get('lead_score', 0),
                lead_data.get('company_size'),
                technologies,
                lead_data.get('contact_potential'),
                lead_data.get('job_url'),
                lead_data.get('notes', '')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving business lead: {e}")
            return False

    def get_business_leads(self, limit: int = 50, min_score: int = 0) -> List[Dict]:
        """Retrieve business leads from database."""
        try:
            self.connect()
            cursor = self.conn.cursor()
            
            # First ensure table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    platform TEXT NOT NULL,
                    lead_score INTEGER DEFAULT 0,
                    company_size TEXT,
                    technologies TEXT,
                    contact_potential TEXT,
                    job_url TEXT,
                    date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contact_status TEXT DEFAULT 'New',
                    notes TEXT,
                    UNIQUE(company, title, platform)
                )
            ''')
            
            cursor.execute('''
                SELECT * FROM business_leads 
                WHERE lead_score >= ? 
                ORDER BY lead_score DESC, date_found DESC 
                LIMIT ?
            ''', (min_score, limit))
            
            rows = cursor.fetchall()
            leads = []
            
            for row in rows:
                lead = dict(row)
                # Parse technologies JSON back to list
                try:
                    lead['technologies'] = json.loads(lead['technologies'] or '[]')
                except:
                    lead['technologies'] = []
                leads.append(lead)
            
            return leads
        except Exception as e:
            print(f"Error retrieving business leads: {e}")
            return []

    def save_job(self, job_data: Dict) -> bool:
        """Save job data to database using existing structure."""
        try:
            # Use existing insert_job method with some adaptation
            job_hash = self.generate_job_hash(job_data)
            existing_id = self.job_exists(job_hash)
            
            if existing_id:
                self.update_job_last_seen(existing_id)
                return True
            else:
                self.insert_job(job_data)
                return True
        except Exception as e:
            print(f"Error saving job: {e}")
            return False

    def get_jobs(self, limit: int = 50, search: str = None, platform: str = None) -> List[Dict]:
        """Get jobs with enhanced filtering."""
        return self.search_jobs(keywords=search, platform=platform, limit=limit)

    def get_stats(self) -> Dict:
        """Get enhanced statistics including business leads."""
        try:
            stats = self.get_statistics()
            
            # Add business leads statistics
            self.connect()
            cursor = self.conn.cursor()
            
            # Check if business_leads table exists
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='business_leads'
            ''')
            if cursor.fetchone():
                # Total leads
                cursor.execute("SELECT COUNT(*) as count FROM business_leads")
                row = cursor.fetchone()
                stats['total_leads'] = row['count'] if row else 0
                
                # High value leads (score >= 70)
                cursor.execute("SELECT COUNT(*) as count FROM business_leads WHERE lead_score >= 70")
                row = cursor.fetchone()
                stats['high_value_leads'] = row['count'] if row else 0
                
                # Recent searches (last 7 days)
                cursor.execute('''
                    SELECT COUNT(*) as count FROM search_history 
                    WHERE searched_at >= datetime('now', '-7 days')
                ''')
                row = cursor.fetchone()
                stats['recent_searches'] = row['count'] if row else 0
                
                # Top platforms for leads
                cursor.execute('''
                    SELECT platform, COUNT(*) as count 
                    FROM business_leads 
                    GROUP BY platform 
                    ORDER BY count DESC 
                    LIMIT 5
                ''')
                stats['top_platforms'] = [dict(row) for row in cursor.fetchall()]
            else:
                stats['total_leads'] = 0
                stats['high_value_leads'] = 0
                stats['recent_searches'] = 0
                stats['top_platforms'] = []
            
            return stats
        except Exception as e:
            print(f"Error getting enhanced stats: {e}")
            return self.get_statistics()

        # ----------------------
        # Outreach helpers
        # ----------------------
        def record_outreach(self, *, to_email: str, subject: str, body: str, transport: str,
                            status: str = 'queued', lead_id: Optional[int] = None, job_id: Optional[int] = None,
                            sequence_name: Optional[str] = None, sequence_step: Optional[int] = None,
                            template_id: Optional[str] = None, scheduled_for: Optional[str] = None,
                            provider_msg_id: Optional[str] = None, error: Optional[str] = None,
                            metadata: Optional[Dict] = None) -> int:
            """Insert an outreach log row. Returns inserted id."""
            self.connect()
            cur = self.conn.cursor()
            to_domain = (to_email.split('@')[-1]).lower() if to_email and '@' in to_email else None
            cur.execute('''
                INSERT INTO outreach_logs(lead_id, job_id, to_email, to_domain, subject, body, transport, status,
                                          provider_msg_id, sequence_name, sequence_step, template_id, scheduled_for,
                                          error, metadata)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                lead_id, job_id, to_email, to_domain, subject, body, transport, status,
                provider_msg_id, sequence_name, sequence_step, template_id, scheduled_for,
                error, json.dumps(metadata or {})
            ))
            self.conn.commit()
            return cur.lastrowid

        def update_outreach_status(self, *, id: Optional[int] = None, provider_msg_id: Optional[str] = None,
                                   status: str, timestamp_field: Optional[str] = None,
                                   error: Optional[str] = None):
            """Update an outreach row status by id or provider_msg_id. Optionally set a timestamp field."""
            if not id and not provider_msg_id:
                return
            self.connect()
            cur = self.conn.cursor()
            ts_fields = {'sent': 'sent_at', 'delivered': 'delivered_at', 'opened': 'opened_at', 'replied': 'replied_at'}
            ts_col = timestamp_field or ts_fields.get(status)
            if id:
                if ts_col:
                    cur.execute(f'''UPDATE outreach_logs SET status = ?, {ts_col} = CURRENT_TIMESTAMP, error = COALESCE(?, error) WHERE id = ?''', (status, error, id))
                else:
                    cur.execute('UPDATE outreach_logs SET status = ?, error = COALESCE(?, error) WHERE id = ?', (status, error, id))
            else:
                if ts_col:
                    cur.execute(f'''UPDATE outreach_logs SET status = ?, {ts_col} = CURRENT_TIMESTAMP, error = COALESCE(?, error) WHERE provider_msg_id = ?''', (status, error, provider_msg_id))
                else:
                    cur.execute('UPDATE outreach_logs SET status = ?, error = COALESCE(?, error) WHERE provider_msg_id = ?', (status, error, provider_msg_id))
            self.conn.commit()

        def count_sent_today(self) -> int:
            """Return count of emails marked sent today (UTC)."""
            self.connect()
            cur = self.conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM outreach_logs
                WHERE date(COALESCE(sent_at, created_at)) = date('now')
                  AND status IN ('sent','delivered','opened','clicked','replied','bounced')
            """)
            row = cur.fetchone()
            return row[0] if row else 0

        def count_sent_today_by_domain(self, domain: str) -> int:
            self.connect()
            cur = self.conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM outreach_logs
                WHERE date(COALESCE(sent_at, created_at)) = date('now')
                  AND to_domain = ?
                  AND status IN ('sent','delivered','opened','clicked','replied','bounced')
            """, (domain.lower(),))
            row = cur.fetchone()
            return row[0] if row else 0

        def get_scheduled_outreach_due(self, limit: int = 20) -> List[Dict]:
            """Return scheduled outreach rows due now or earlier."""
            self.connect()
            cur = self.conn.cursor()
            cur.execute('''
                SELECT * FROM outreach_logs
                WHERE status = 'scheduled' AND scheduled_for IS NOT NULL
                  AND datetime(scheduled_for) <= datetime('now')
                ORDER BY datetime(scheduled_for) ASC
                LIMIT ?
            ''', (limit,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

        def save_template(self, *, id: str, name: str, subject: str, body: str):
            self.connect()
            cur = self.conn.cursor()
            cur.execute('''
                INSERT INTO templates(id, name, subject, body)
                VALUES(?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                  name = excluded.name,
                  subject = excluded.subject,
                  body = excluded.body
            ''', (id, name, subject, body))
            self.conn.commit()

        def list_templates(self) -> List[Dict]:
            self.connect()
            cur = self.conn.cursor()
            cur.execute('SELECT id, name, subject, body, created_at FROM templates ORDER BY created_at DESC')
            return [dict(r) for r in cur.fetchall()]

    # Crawl logs APIs
    def log_crawl(self, domain: str, listing_url: str, status: str,
                  found_count: int = 0, error_message: Optional[str] = None,
                  started_at: Optional[str] = None, finished_at: Optional[str] = None):
        """Insert a crawl log entry."""
        try:
            self.connect()
            cur = self.conn.cursor()
            cur.execute('''
                INSERT INTO crawl_logs(domain, listing_url, status, found_count, error_message, started_at, finished_at)
                VALUES(?,?,?,?,?,?,?)
            ''', (domain, listing_url, status, found_count, error_message, started_at, finished_at))
            self.conn.commit()
        except Exception as e:
            print(f"Error logging crawl: {e}")

    def get_crawl_logs(self, limit: int = 20) -> List[Dict]:
        """Return recent crawl logs."""
        try:
            self.connect()
            cur = self.conn.cursor()
            cur.execute('''
                SELECT * FROM crawl_logs ORDER BY COALESCE(finished_at, started_at) DESC LIMIT ?
            ''', (limit,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"Error retrieving crawl logs: {e}")
            return []

    def clear_crawl_results(self) -> int:
        """Delete jobs that were created by crawler (i.e., have source_listing). Returns deleted count."""
        try:
            self.connect()
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM jobs WHERE source_listing IS NOT NULL")
            before = cur.fetchone()[0]
            cur.execute("DELETE FROM jobs WHERE source_listing IS NOT NULL")
            self.conn.commit()
            return before
        except Exception as e:
            print(f"Error clearing crawl results: {e}")
            return 0
