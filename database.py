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
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
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
        
        cursor.execute('''
            INSERT INTO jobs (
                job_hash, title, company, location, salary, description,
                url, platform, remote, job_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
        ''', (
            job_hash,
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            job.get('salary', ''),
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
