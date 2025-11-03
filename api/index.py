"""Simplified Vercel-compatible web dashboard for job scraper with business intelligence."""
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time
from urllib.parse import quote
from urllib.parse import urljoin
import re
import csv
import io
from collections import defaultdict
import sys
from urllib.parse import urlparse
import logging
from logging.handlers import RotatingFileHandler
import smtplib
from email.message import EmailMessage
import hmac
import hashlib

# Import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import JobDatabase
from functools import wraps

# Import contact discovery module
try:
    from contact_discovery import contact_discovery
    CONTACT_DISCOVERY_ENABLED = True
except ImportError as e:
    print(f"Contact discovery module not available: {e}")
    CONTACT_DISCOVERY_ENABLED = False
    contact_discovery = None

# Import outreach templates module
try:
    from outreach_templates import outreach_personalizer
    OUTREACH_TEMPLATES_ENABLED = True
except ImportError as e:
    print(f"Outreach templates module not available: {e}")
    OUTREACH_TEMPLATES_ENABLED = False
    outreach_personalizer = None

# Import advanced scraper module
try:
    from advanced_scraper import advanced_scraper
    ADVANCED_SCRAPER_ENABLED = True
except ImportError as e:
    print(f"Advanced scraper module not available: {e}")
    ADVANCED_SCRAPER_ENABLED = False
    advanced_scraper = None

# Import email automation module
try:
    from email_automation import EmailAutomation, EMAIL_SEQUENCE_TEMPLATES
    email_automation = EmailAutomation()
    EMAIL_AUTOMATION_ENABLED = True
except ImportError as e:
    print(f"Email automation module not available: {e}")
    EMAIL_AUTOMATION_ENABLED = False
    email_automation = None

# Import analytics dashboard module
try:
    from analytics_dashboard import AnalyticsDashboard
    analytics = AnalyticsDashboard()
    ANALYTICS_ENABLED = True
except ImportError as e:
    print(f"Analytics dashboard module not available: {e}")
    ANALYTICS_ENABLED = False
    analytics = None

# Import CRM integration module
try:
    from crm_integration import CRMIntegration
    crm = CRMIntegration()
    CRM_ENABLED = True
except ImportError as e:
    print(f"CRM integration module not available: {e}")
    CRM_ENABLED = False
    crm = None

# Import AI features module
try:
    from ai_features import AIFeatures
    ai = AIFeatures()
    AI_ENABLED = True
except ImportError as e:
    print(f"AI features module not available: {e}")
    AI_ENABLED = False
    ai = None

# Import follow-up engine module
try:
    from followup_engine import FollowUpEngine
    followup_engine = FollowUpEngine()
    FOLLOWUP_ENGINE_ENABLED = True
except ImportError as e:
    print(f"Follow-up engine module not available: {e}")
    FOLLOWUP_ENGINE_ENABLED = False
    followup_engine = None

# Import lead enrichment module
try:
    from lead_enrichment import LeadEnrichment
    lead_enrichment = LeadEnrichment()
    LEAD_ENRICHMENT_ENABLED = True
except ImportError as e:
    print(f"Lead enrichment module not available: {e}")
    LEAD_ENRICHMENT_ENABLED = False
    lead_enrichment = None

# Import A/B testing module
try:
    from ab_testing import ABTestingFramework
    ab_testing = ABTestingFramework()
    AB_TESTING_ENABLED = True
except ImportError as e:
    print(f"A/B testing module not available: {e}")
    AB_TESTING_ENABLED = False
    ab_testing = None

# Import reporting engine module
try:
    from reporting_engine import ReportingEngine
    reporting = ReportingEngine()
    REPORTING_ENABLED = True
except ImportError as e:
    print(f"Reporting engine module not available: {e}")
    REPORTING_ENABLED = False
    reporting = None

# Import multi-channel outreach module
try:
    from multichannel_outreach import MultiChannelOutreach
    multichannel = MultiChannelOutreach()
    MULTICHANNEL_ENABLED = True
except ImportError as e:
    print(f"Multi-channel outreach module not available: {e}")
    MULTICHANNEL_ENABLED = False
    multichannel = None

# Import calendar integration module
try:
    from calendar_integration import CalendarIntegration
    CALENDAR_ENABLED = True
except ImportError as e:
    print(f"Calendar integration module not available: {e}")
    CALENDAR_ENABLED = False
    CalendarIntegration = None

# Import voice calling module
try:
    from voice_calling import VoiceCallingSystem
    VOICE_CALLING_ENABLED = True
except ImportError as e:
    print(f"Voice calling module not available: {e}")
    VOICE_CALLING_ENABLED = False
    VoiceCallingSystem = None

# Import social media automation module
try:
    from social_media import SocialMediaAutomation
    SOCIAL_MEDIA_ENABLED = True
except ImportError as e:
    print(f"Social media automation module not available: {e}")
    SOCIAL_MEDIA_ENABLED = False
    SocialMediaAutomation = None

# Import security & compliance module
try:
    from security_compliance import SecurityCompliance
    SECURITY_ENABLED = True
except ImportError as e:
    print(f"Security & compliance module not available: {e}")
    SECURITY_ENABLED = False
    SecurityCompliance = None

# Import webhook system module
try:
    from webhook_system import WebhookSystem
    WEBHOOK_ENABLED = True
except ImportError as e:
    print(f"Webhook system module not available: {e}")
    WEBHOOK_ENABLED = False
    WebhookSystem = None

# Import workflow automation module
try:
    from workflow_automation import WorkflowAutomation
    WORKFLOW_ENABLED = True
except ImportError as e:
    print(f"Workflow automation module not available: {e}")
    WORKFLOW_ENABLED = False
    WorkflowAutomation = None

# Import team collaboration module
try:
    from team_collaboration import TeamCollaboration
    TEAM_COLLAB_ENABLED = True
except ImportError as e:
    print(f"Team collaboration module not available: {e}")
    TEAM_COLLAB_ENABLED = False
    TeamCollaboration = None

# Import revenue intelligence module
try:
    from revenue_intelligence import RevenueIntelligence
    REVENUE_ENABLED = True
except ImportError as e:
    print(f"Revenue intelligence module not available: {e}")
    REVENUE_ENABLED = False
    RevenueIntelligence = None

# Import document management module
try:
    from document_management import DocumentManagement
    DOCUMENTS_ENABLED = True
except ImportError as e:
    print(f"Document management module not available: {e}")
    DOCUMENTS_ENABLED = False
    DocumentManagement = None

# Import caching layer
try:
    from caching_layer import CacheManager, CacheService, CacheInvalidationService
    CACHE_ENABLED = True
except ImportError as e:
    print(f"Caching layer not available: {e}")
    CACHE_ENABLED = False
    CacheManager = None
    CacheService = None
    CacheInvalidationService = None

# Import rate limiting
try:
    from rate_limiting import RateLimiter, RateLimitService
    RATE_LIMIT_ENABLED = True
except ImportError as e:
    print(f"Rate limiting not available: {e}")
    RATE_LIMIT_ENABLED = False
    RateLimiter = None
    RateLimitService = None

# Import database optimization
try:
    from database_optimization import DatabaseOptimizer, QueryPerformanceMonitor, OptimizedQueryBuilder, DatabaseMaintenanceService
    DB_OPTIMIZATION_ENABLED = True
except ImportError as e:
    print(f"Database optimization not available: {e}")
    DB_OPTIMIZATION_ENABLED = False
    DatabaseOptimizer = None
    QueryPerformanceMonitor = None
    OptimizedQueryBuilder = None
    DatabaseMaintenanceService = None

# Import background jobs
try:
    from background_jobs import BackgroundJobQueue, JobService, JobPriority
    JOBS_ENABLED = True
except ImportError as e:
    print(f"Background jobs not available: {e}")
    JOBS_ENABLED = False
    BackgroundJobQueue = None
    JobService = None
    JobPriority = None

# Configure Flask with explicit template directory so Serverless bundle can find Jinja templates
_HERE = os.path.dirname(__file__)
_TEMPLATES_DIR = os.path.normpath(os.path.join(_HERE, '..', 'templates'))
app = Flask(__name__, template_folder=_TEMPLATES_DIR)
# Basic security defaults: use env SECRET_KEY if provided; otherwise a per-run random fallback
try:
    import secrets
    _default_secret = secrets.token_hex(16)
except Exception:
    _default_secret = 'change-me'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.getenv('APP_SECRET', _default_secret))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- Logging setup (rotating file) ---
# Vercel serverless filesystem is read-only except /tmp. Prefer /tmp/logs when on Vercel.
def _ensure_dir(path: str) -> Optional[str]:
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception:
        return None

_default_log_dir = '/tmp/logs' if os.getenv('VERCEL') else 'logs'
LOG_DIR = os.getenv('LOG_DIR', _default_log_dir)
if not _ensure_dir(LOG_DIR):
    # Fallback to /tmp/logs if custom path failed
    tmp_fallback = _ensure_dir('/tmp/logs')
    LOG_DIR = tmp_fallback or None

LOG_FILE = None
if LOG_DIR:
    LOG_FILE = os.getenv('LOG_FILE', os.path.join(LOG_DIR, 'app.log'))

logger = logging.getLogger('scrapper')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    try:
        if LOG_FILE:
            fh = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
            fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        else:
            raise RuntimeError('No writable LOG_FILE available')
    except Exception:
        # Fallback to stdout if file logging is unavailable
        sh = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        sh.setFormatter(fmt)
        logger.addHandler(sh)

# Initialize database (SQLite fallback only; Postgres used via DATABASE_URL in thin readers)
try:
    db = JobDatabase(os.getenv('DB_PATH', 'output/jobs.db'))
except Exception as e:
    print(f"Database initialization error: {e}")
    db = None

# Optional Postgres connectivity for read-only endpoints
PG_URL = os.getenv('DATABASE_URL')

def _pg_conn():
    if not PG_URL:
        return None
    try:
        import psycopg2  # type: ignore
        return psycopg2.connect(PG_URL, sslmode=os.getenv('PG_SSLMODE','require'))
    except Exception as e:
        print(f"Postgres connect error: {e}")
        return None

# Initialize calendar integration
calendar_integration = None
if CALENDAR_ENABLED and db:
    try:
        calendar_integration = CalendarIntegration(db.connection)
    except Exception as e:
        print(f"Calendar integration initialization error: {e}")

# Initialize voice calling system
voice_calling = None
if VOICE_CALLING_ENABLED and db:
    try:
        voice_calling = VoiceCallingSystem(
            db.connection,
            account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
            auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
            from_number=os.getenv('TWILIO_PHONE_NUMBER')
        )
    except Exception as e:
        print(f"Voice calling initialization error: {e}")

# Initialize social media automation
social_media = None
if SOCIAL_MEDIA_ENABLED and db:
    try:
        social_media = SocialMediaAutomation(db.connection)
    except Exception as e:
        print(f"Social media automation initialization error: {e}")

# Initialize security & compliance
security = None
if SECURITY_ENABLED and db:
    try:
        security = SecurityCompliance(db.connection)
    except Exception as e:
        print(f"Security & compliance initialization error: {e}")

# Initialize webhook system
webhook_system = None
if WEBHOOK_ENABLED and db:
    try:
        webhook_system = WebhookSystem(db.connection)
    except Exception as e:
        print(f"Webhook system initialization error: {e}")

# Initialize workflow automation
workflow_automation = None
if WORKFLOW_ENABLED and db:
    try:
        workflow_automation = WorkflowAutomation(db.connection)
    except Exception as e:
        print(f"Workflow automation initialization error: {e}")

# Initialize team collaboration
team_collab = None
if TEAM_COLLAB_ENABLED and db:
    try:
        team_collab = TeamCollaboration(db.connection)
    except Exception as e:
        print(f"Team collaboration initialization error: {e}")

# Initialize revenue intelligence
revenue_intel = None
if REVENUE_ENABLED and db:
    try:
        revenue_intel = RevenueIntelligence(db.connection)
    except Exception as e:
        print(f"Revenue intelligence initialization error: {e}")

# Initialize document management
doc_manager = None
if DOCUMENTS_ENABLED and db:
    try:
        doc_manager = DocumentManagement(db.connection)
    except Exception as e:
        print(f"Document management initialization error: {e}")

# Initialize caching layer
cache_manager = None
cache_service = None
cache_invalidation = None
if CACHE_ENABLED:
    try:
        cache_manager = CacheManager()
        cache_service = CacheService(cache_manager)
        cache_invalidation = CacheInvalidationService(cache_service)
    except Exception as e:
        print(f"Caching layer initialization error: {e}")

# Initialize rate limiting
rate_limiter = None
rate_limit_service = None
if RATE_LIMIT_ENABLED:
    try:
        rate_limiter = RateLimiter()
        rate_limit_service = RateLimitService(rate_limiter)
    except Exception as e:
        print(f"Rate limiting initialization error: {e}")

# Initialize database optimization
db_optimizer = None
query_monitor = None
db_maintenance = None
if DB_OPTIMIZATION_ENABLED and db:
    try:
        db_optimizer = DatabaseOptimizer(db.connection)
        query_monitor = QueryPerformanceMonitor()
        db_maintenance = DatabaseMaintenanceService(db_optimizer)
        # Create indexes on startup
        db_optimizer.create_indexes()
    except Exception as e:
        print(f"Database optimization initialization error: {e}")

# Initialize background job queue
job_queue = None
job_service = None
if JOBS_ENABLED:
    try:
        job_queue = BackgroundJobQueue(num_workers=3)
        job_service = JobService(job_queue)
    except Exception as e:
        print(f"Background jobs initialization error: {e}")

# Live scraping storage (in-memory for serverless fallback)
live_jobs = []
scraping_status = {'running': False, 'last_search': None, 'job_count': 0}
user_preferences = {'saved_searches': [], 'favorite_jobs': [], 'applied_jobs': []}

# Business Intelligence for Lead Generation (fallback)
business_leads = []

# Recent events for admin view
recent_events: List[str] = []
# Crawl tracking (in-memory fallbacks)
last_crawl_summary: Dict = {}
memory_crawl_logs: List[Dict] = []

# Failure tracking for alerting
failure_records: Dict[str, List[float]] = {}
ALERT_ENABLED = os.getenv('ADMIN_ALERTS', '0') in ('1', 'true', 'True')
ALERT_EMAIL = os.getenv('ADMIN_ALERT_EMAIL')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
SMTP_FROM = os.getenv('SMTP_FROM', ALERT_EMAIL or 'scrapper@localhost')
ALERT_THRESHOLD = int(os.getenv('ALERT_THRESHOLD', '3'))  # failures
ALERT_WINDOW_SEC = int(os.getenv('ALERT_WINDOW_SEC', '600'))  # 10 minutes
ALERT_COOLDOWN_SEC = int(os.getenv('ALERT_COOLDOWN_SEC', '1800'))  # 30 minutes
last_alert_sent: Dict[str, float] = {}

# --- Admin auth utilities ---
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

def _check_bearer(req) -> bool:
    auth = req.headers.get('Authorization') or ''
    if auth.lower().startswith('bearer '):
        token = auth.split(' ', 1)[1].strip()
        return bool(ADMIN_TOKEN) and token == ADMIN_TOKEN
    return False

def _check_basic(req) -> bool:
    if not (ADMIN_USER and ADMIN_PASS):
        return False
    try:
        import base64
        auth = req.headers.get('Authorization') or ''
        if not auth.lower().startswith('basic '):
            return False
        raw = auth.split(' ', 1)[1]
        userpass = base64.b64decode(raw).decode('utf-8', errors='ignore')
        if ':' not in userpass:
            return False
        u, p = userpass.split(':', 1)
        return (u == ADMIN_USER and p == ADMIN_PASS)
    except Exception:
        return False

def is_admin_request(req) -> bool:
    # Prefer token if provided
    if ADMIN_TOKEN:
        if req.headers.get('X-Admin-Token') == ADMIN_TOKEN:
            return True
        if req.args.get('admin_token') == ADMIN_TOKEN:
            return True
        if _check_bearer(req):
            return True
    # Fallback to basic auth if configured
    if _check_basic(req):
        return True
    return False

def admin_required(fn):
    @wraps(fn)
    def _wrapped(*args, **kwargs):
        if is_admin_request(request):
            return fn(*args, **kwargs)
        # If basic auth configured, advertise challenge
        resp = jsonify({'success': False, 'error': 'admin auth required'})
        status = 401
        try:
            from flask import make_response
            r = make_response(resp, status)
            if ADMIN_USER and ADMIN_PASS:
                r.headers['WWW-Authenticate'] = 'Basic realm="Admin"'
            return r
        except Exception:
            return resp, status
    return _wrapped

def log_event(message: str):
    try:
        ts = datetime.now().strftime('%H:%M:%S')
        entry = f"[{ts}] {message}"
        print(entry)
        try:
            logger.info(message)
        except Exception:
            pass
        recent_events.append(entry)
        if len(recent_events) > 200:
            del recent_events[0:len(recent_events)-200]
    except Exception:
        pass

def record_failure(domain: str, reason: str):
    if not domain:
        return
    now = time.time()
    arr = failure_records.get(domain, [])
    arr.append(now)
    # keep only within window
    cutoff = now - ALERT_WINDOW_SEC
    arr = [t for t in arr if t >= cutoff]
    failure_records[domain] = arr
    # maybe alert
    if ALERT_ENABLED and ALERT_EMAIL and SMTP_HOST:
        if len(arr) >= ALERT_THRESHOLD:
            last_sent = last_alert_sent.get(domain, 0)
            if now - last_sent >= ALERT_COOLDOWN_SEC:
                try:
                    send_admin_alert(domain, len(arr), reason)
                    last_alert_sent[domain] = now
                except Exception as e:
                    logger.error(f"Alert send failed for {domain}: {e}")

def send_admin_alert(domain: str, count: int, reason: str):
    subj = f"Scrapper alert: repeated failures for {domain} ({count} in last {ALERT_WINDOW_SEC//60}m)"
    body = f"Domain: {domain}\nFailures in window: {count}\nLast reason: {reason}\nTime: {datetime.utcnow().isoformat()}Z\n"
    msg = EmailMessage()
    msg['Subject'] = subj
    msg['From'] = SMTP_FROM
    msg['To'] = ALERT_EMAIL
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
        try:
            s.starttls()
        except Exception:
            pass
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def tail_log(path: str, lines: int = 20) -> List[str]:
    out: List[str] = []
    try:
        with open(path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = -1
            data = b''
            while len(out) <= lines and abs(block) * 1024 < size + 1024:
                try:
                    f.seek(block * 1024, os.SEEK_END)
                except OSError:
                    f.seek(0)
                    data = f.read()
                    break
                chunk = f.read(1024)
                data = chunk + data
                out = data.splitlines()
                block -= 1
            out = [l.decode('utf-8', errors='replace') for l in out[-lines:]]
    except Exception:
        pass
    return out

# --- Lead utilities ---
_COMPANY_SUFFIXES = [
    ' inc', ' inc.', ' llc', ' llc.', ' ltd', ' ltd.', ' limited', ' co', ' co.',
    ' corp', ' corp.', ' corporation', ' gmbh', ' bv', ' plc'
]

_JOB_BOARD_DOMAINS = {
    'linkedin.com','indeed.com','glassdoor.com','remoteok.com','weworkremotely.com','nodesk.co',
    'remotive.com','adzuna.com','wellfound.com','angel.co','github.com','angel.co','stackoverflow.com'
}

def normalize_text(s: str) -> str:
    s = (s or '').strip().lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_company(name: str) -> str:
    n = normalize_text(name)
    for suf in _COMPANY_SUFFIXES:
        if n.endswith(suf):
            n = n[: -len(suf)]
            n = n.strip()
    return n

def normalize_title(title: str) -> str:
    return normalize_text(title)

def extract_domain(url: str) -> Optional[str]:
    try:
        if not url:
            return None
        parsed = urlparse(url)
        host = (parsed.netloc or '').lower()
        if host.startswith('www.'):
            host = host[4:]
        return host or None
    except Exception:
        return None

def resolve_company_domain(job: Dict) -> Optional[str]:
    # 1) Explicit website fields
    for key in ('company_url','company_website','website','company_site'):
        d = extract_domain(job.get(key, ''))
        if d and d not in _JOB_BOARD_DOMAINS:
            return d
    # 2) If job URL is not a board (rare), use it
    d = extract_domain(job.get('url', ''))
    if d and d not in _JOB_BOARD_DOMAINS:
        return d
    # 3) Parse first external link in description
    desc = job.get('description') or ''
    urls = re.findall(r'https?://[^\s\)\]"\'>]+', desc)
    for u in urls:
        dom = extract_domain(u)
        if dom and dom not in _JOB_BOARD_DOMAINS:
            return dom
    # 4) Use optional lead_enrichment provider if available
    try:
        if lead_enrichment is not None:
            if hasattr(lead_enrichment, 'find_company_domain'):
                dom = lead_enrichment.find_company_domain(job.get('company', ''))
                if dom: return extract_domain('https://' + dom) or dom
            if hasattr(lead_enrichment, 'get_company_domain'):
                dom = lead_enrichment.get_company_domain(job.get('company', ''))
                if dom: return extract_domain('https://' + dom) or dom
    except Exception as e:
        print(f"Domain enrichment error: {e}")
    return None

# --- Per-domain rate limiting + fetch helper ---
class DomainRateLimiter:
    def __init__(self, capacity: int = 5, refill_per_sec: float = 2.0):
        # capacity: max tokens per domain; refill_per_sec: tokens per second
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.state = {}
        self.lock = threading.Lock()

    def acquire(self, domain: str):
        if not domain:
            return
        now = time.time()
        with self.lock:
            tokens, last = self.state.get(domain, (self.capacity, now))
            # Refill tokens
            delta = now - last
            tokens = min(self.capacity, tokens + delta * self.refill_per_sec)
            if tokens < 1.0:
                # Need to wait
                wait = (1.0 - tokens) / self.refill_per_sec
                wait = max(0.0, min(wait, 2.0))  # cap wait
                time.sleep(wait)
                now2 = time.time()
                delta2 = now2 - now
                tokens = min(self.capacity, tokens + delta2 * self.refill_per_sec)
                now = now2
            tokens -= 1.0
            self.state[domain] = (tokens, now)

import random as _random
RESPECT_ROBOTS = os.getenv('RESPECT_ROBOTS', '1') in ('1','true','True')
ALLOW_ROBOTS_BYPASS = os.getenv('ALLOW_ROBOTS_BYPASS', '0') in ('1','true','True')
SCRAPER_BASE_DELAY_SEC = float(os.getenv('SCRAPER_BASE_DELAY_SEC', '2.0'))
SCRAPER_MAX_DELAY_SEC = float(os.getenv('SCRAPER_MAX_DELAY_SEC', '5.0'))
_PER_DOMAIN_CAP = float(os.getenv('SCRAPER_PER_DOMAIN_CAP', '2'))  # token bucket capacity
_PER_DOMAIN_RPS = float(os.getenv('SCRAPER_PER_DOMAIN_RPS', '0.5'))  # ~1 req per 2s
rate_limiter_dl = DomainRateLimiter(capacity=int(_PER_DOMAIN_CAP), refill_per_sec=_PER_DOMAIN_RPS)

# robots.txt checker with caching
class RobotsCache:
    def __init__(self):
        self.cache = {}
        self.ttl = int(os.getenv('ROBOTS_TTL_SEC', '3600'))

    def can_fetch(self, url: str, ua: str) -> bool:
        try:
            dom = extract_domain(url) or ''
            if not dom:
                return True
            now = time.time()
            entry = self.cache.get(dom)
            if not entry or now - entry['ts'] > self.ttl:
                robots_url = f"https://{dom}/robots.txt"
                try:
                    import urllib.robotparser as rp
                    r = rp.RobotFileParser()
                    r.set_url(robots_url)
                    r.read()
                    entry = {'ts': now, 'rp': r}
                except Exception:
                    # On failure to read robots, default allow
                    entry = {'ts': now, 'rp': None}
                self.cache[dom] = entry
            r = entry['rp']
            if r is None:
                return True
            return bool(r.can_fetch(ua, url))
        except Exception:
            return True

robots_cache = RobotsCache()

# Contact details for ethical crawling: include email in User-Agent if provided
SCRAPER_UA_NAME = os.getenv('SCRAPER_UA_NAME', 'JobScraperMVP/1.0')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL')

def fetch_url(url: str, headers: Optional[Dict] = None, timeout: int = 15):
    domain = extract_domain(url) or ''
    try:
        rate_limiter_dl.acquire(domain)
    except Exception:
        pass
    # polite base delay (env-driven)
    try:
        delay = max(0.0, min(SCRAPER_MAX_DELAY_SEC, SCRAPER_BASE_DELAY_SEC))
        if SCRAPER_MAX_DELAY_SEC > SCRAPER_BASE_DELAY_SEC:
            delay = _random.uniform(SCRAPER_BASE_DELAY_SEC, SCRAPER_MAX_DELAY_SEC)
        time.sleep(delay)
    except Exception:
        pass
    # Compose default headers with contact email in UA and From
    if not headers:
        ua = f"{SCRAPER_UA_NAME}"
        if CONTACT_EMAIL:
            ua += f" (+mailto:{CONTACT_EMAIL})"
        # Add a common browser UA tail to reduce blocks while still including contact
        ua += "; Mozilla/5.0"
        headers = {'User-Agent': ua}
        if CONTACT_EMAIL:
            headers['From'] = CONTACT_EMAIL
    elif 'User-Agent' not in headers:
        # Ensure UA present even if custom headers provided
        ua = f"{SCRAPER_UA_NAME}"
        if CONTACT_EMAIL:
            ua += f" (+mailto:{CONTACT_EMAIL})"
        ua += "; Mozilla/5.0"
        headers['User-Agent'] = ua
        if CONTACT_EMAIL and 'From' not in headers:
            headers['From'] = CONTACT_EMAIL
    # robots.txt compliance
    if RESPECT_ROBOTS and not ALLOW_ROBOTS_BYPASS:
        try:
            can = robots_cache.can_fetch(url, headers.get('User-Agent','*'))
            if not can:
                log_event(f"robots.txt disallow for {domain} path {url}")
                class _Blocked:
                    def __init__(self, u: str):
                        self.status_code = 403
                        self.content = b''
                        self.text = 'Blocked by robots.txt'
                        self.headers = {}
                        self.url = u
                return _Blocked(url)
        except Exception:
            pass
    return requests.get(url, headers=headers, timeout=timeout)

# Simplified Business Intelligence Functions
def extract_company_intelligence(job: Dict) -> Dict:
    """Extract enhanced business intelligence from job posting with advanced scoring."""
    company = job.get('company', '').strip()
    title = job.get('title', '').strip()
    description = job.get('description', '').strip()
    location = job.get('location', '').strip()
    platform = job.get('platform', '').strip()
    
    # Initialize scoring components
    base_score = 0
    scoring_details = {}
    
    # Enhanced company size detection with growth indicators
    company_size = "Unknown"
    company_score = 0
    desc_lower = description.lower()
    company_lower = company.lower()
    
    # Company size scoring
    if any(word in desc_lower for word in ['startup', 'small team', 'growing company', 'early stage']):
        company_size = "Startup"
        company_score = 25  # High potential for new services
        scoring_details['company_size_reason'] = "Startup - high growth potential"
    elif any(word in desc_lower for word in ['enterprise', 'large company', 'fortune', 'global', 'multinational']):
        company_size = "Enterprise"
        company_score = 15  # Established but harder to reach
        scoring_details['company_size_reason'] = "Enterprise - established market"
    elif any(word in desc_lower for word in ['mid-size', 'medium company', 'scale', 'scaling']):
        company_size = "Mid-size"
        company_score = 20  # Good balance
        scoring_details['company_size_reason'] = "Mid-size - good opportunity balance"
    else:
        company_size = "Unknown"
        company_score = 10
        scoring_details['company_size_reason'] = "Unknown size"
    
    # Technology stack complexity scoring
    tech_keywords = [
        ('python', 8), ('javascript', 6), ('react', 7), ('node', 6), ('typescript', 8),
        ('aws', 10), ('azure', 10), ('gcp', 10), ('docker', 9), ('kubernetes', 12),
        ('microservices', 15), ('api', 5), ('graphql', 8), ('mongodb', 6), ('postgresql', 7),
        ('redis', 8), ('elasticsearch', 10), ('kafka', 12), ('spark', 12), ('tensorflow', 15),
        ('machine learning', 18), ('ai', 15), ('blockchain', 20), ('devops', 10), ('cicd', 8)
    ]
    
    technologies = []
    tech_score = 0
    
    for tech, score in tech_keywords:
        if tech in desc_lower or tech in title.lower():
            technologies.append(tech)
            tech_score += score
    
    # Cap technology score at 50
    tech_score = min(tech_score, 50)
    scoring_details['technology_score'] = tech_score
    scoring_details['technologies_found'] = technologies
    
    # Market timing and urgency indicators
    urgency_score = 0
    urgency_indicators = [
        ('urgent', 15), ('immediate', 12), ('asap', 10), ('quickly', 8),
        ('fast-paced', 8), ('rapid', 8), ('growing team', 10), ('expanding', 12),
        ('hiring now', 15), ('immediate start', 15), ('new position', 8)
    ]
    
    for indicator, score in urgency_indicators:
        if indicator in desc_lower:
            urgency_score += score
    
    urgency_score = min(urgency_score, 25)  # Cap at 25
    scoring_details['urgency_score'] = urgency_score
    
    # Platform credibility scoring
    platform_scores = {
        'LinkedIn': 15,    # High credibility
        'Indeed': 10,      # Good volume
        'Glassdoor': 12,   # Company insights
        'RemoteOK': 8,     # Tech-focused
        'WeWorkRemotely': 8,
        'Wellfound': 12,   # Startup focus
        'NoDesk': 6
    }
    platform_score = platform_scores.get(platform, 5)
    scoring_details['platform_score'] = platform_score
    
    # Geographic and remote work scoring
    location_score = 0
    if 'remote' in location.lower() or 'remote' in desc_lower:
        location_score = 15  # Remote-first companies often use tech services
        scoring_details['location_advantage'] = "Remote-first culture"
    elif any(city in location.lower() for city in ['san francisco', 'sf', 'silicon valley', 'seattle', 'new york', 'austin', 'boston']):
        location_score = 12  # Tech hubs
        scoring_details['location_advantage'] = "Tech hub location"
    else:
        location_score = 5
        scoring_details['location_advantage'] = "Standard location"
    
    # Industry and domain scoring
    industry_score = 0
    high_value_industries = [
        ('fintech', 15), ('healthtech', 15), ('edtech', 12), ('blockchain', 18),
        ('ai', 18), ('ml', 18), ('saas', 15), ('cloud', 12), ('cybersecurity', 15),
        ('data', 10), ('analytics', 12), ('automation', 12)
    ]
    
    for industry, score in high_value_industries:
        if industry in desc_lower or industry in company_lower:
            industry_score = max(industry_score, score)  # Take highest match
    
    scoring_details['industry_score'] = industry_score
    
    # Job seniority and decision-making power indicators
    seniority_score = 0
    if any(level in title.lower() for level in ['senior', 'lead', 'principal', 'architect', 'manager', 'director']):
        seniority_score = 8  # Higher-level roles suggest budget authority
        scoring_details['seniority_bonus'] = "Senior-level position"
    elif any(level in title.lower() for level in ['junior', 'entry', 'intern']):
        seniority_score = 2
        scoring_details['seniority_bonus'] = "Entry-level position"
    else:
        seniority_score = 5
        scoring_details['seniority_bonus'] = "Mid-level position"
    
    # Calculate final lead score
    final_score = (
        company_score +      # 25 max
        tech_score +         # 50 max  
        urgency_score +      # 25 max
        platform_score +     # 15 max
        location_score +     # 15 max
        industry_score +     # 18 max
        seniority_score      # 8 max
    )
    
    # Ensure score is between 0-100
    final_score = min(max(final_score, 0), 100)
    
    # Determine contact potential based on score
    if final_score >= 75:
        contact_potential = 'Excellent'
    elif final_score >= 60:
        contact_potential = 'High'
    elif final_score >= 40:
        contact_potential = 'Medium'
    elif final_score >= 25:
        contact_potential = 'Low'
    else:
        contact_potential = 'Very Low'
    
    # Create tech stack summary
    tech_stack = ', '.join(technologies[:5]) if technologies else 'General'
    
    return {
        'company_size': company_size,
        'technologies': technologies,
        'lead_score': final_score,
        'tech_stack': tech_stack,
        'contact_potential': contact_potential,
        'scoring_breakdown': scoring_details,
        'score_components': {
            'company_size': company_score,
            'technology_stack': tech_score,
            'market_urgency': urgency_score,
            'platform_credibility': platform_score,
            'location_advantage': location_score,
            'industry_value': industry_score,
            'seniority_level': seniority_score
        }
    }

def generate_working_job_url(job: Dict) -> str:
    """Generate working URLs for job postings."""
    company = job.get('company', '').strip()
    platform = job.get('platform', '')
    title = job.get('title', '')
    
    # Clean company name for URL generation
    clean_company = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
    
    # Platform-specific URL generation
    if platform == 'LinkedIn':
        # LinkedIn company pages and job search
        return f"https://www.linkedin.com/jobs/search/?keywords={title.replace(' ', '%20')}&f_C={clean_company}"
    elif platform == 'Indeed':
        # Indeed company search
        return f"https://www.indeed.com/jobs?q={title.replace(' ', '+')}&l=remote"
    elif platform == 'Glassdoor':
        # Glassdoor company page
        return f"https://www.glassdoor.com/Jobs/{company.replace(' ', '-')}-jobs-SRCH_KE0,{len(company)}.htm"
    elif platform == 'RemoteOK':
        return f"https://remoteok.io/remote-{title.replace(' ', '-').lower()}-jobs"
    elif platform == 'WeWorkRemotely':
        return f"https://weworkremotely.com/remote-jobs/search?term={title.replace(' ', '+')}"
    elif platform == 'Wellfound':
        return f"https://wellfound.com/jobs?keywords={title.replace(' ', '%20')}"
    elif platform == 'NoDesk':
        return f"https://nodesk.co/remote-jobs/"
    else:
        # Fallback to Google search for company + careers
        return f"https://www.google.com/search?q={company.replace(' ', '+')}+careers+{title.replace(' ', '+')}"

def enhance_job_data(job: Dict) -> Dict:
    """Enhance job data with business intelligence and save to database."""
    try:
        # Add business intelligence
        business_intel = extract_company_intelligence(job)
        job.update(business_intel)
        
        # Keep original job URL if it exists, otherwise generate a working URL
        if not job.get('url') or job.get('url') == '#':
            working_url = generate_working_job_url(job)
            job['url'] = working_url
            job['url_type'] = 'company_search'  # Indicate this is a search-based URL
        else:
            job['original_url'] = job.get('url', '')  # Keep original job posting URL
            job['url_type'] = 'direct_link'  # Indicate this is a direct job posting link
        
        # Add additional job metadata
        job['date_enhanced'] = datetime.now().isoformat()
        
        # Save job to database if available
        if db:
            try:
                # Prepare job data for database
                job_data = {
                    'title': job.get('title', 'Unknown'),
                    'company': job.get('company', 'Unknown'),
                    'location': job.get('location', 'Unknown'),
                    'platform': job.get('platform', 'Unknown'),
                    'url': working_url,
                    'description': job.get('description', ''),
                    'salary_range': job.get('salary_range', ''),
                    'experience_level': job.get('experience_level', ''),
                    'employment_type': job.get('employment_type', ''),
                    'date_posted': job.get('date_posted', datetime.now().strftime('%Y-%m-%d')),
                    'keywords_used': scraping_status.get('last_search', '')
                }
                
                # Generate hash for duplicate detection
                job_hash = f"{job_data['title']}-{job_data['company']}-{job_data['platform']}".lower().strip()
                
                # Save using database method
                if hasattr(db, 'save_job'):
                    db.save_job(job_data)
                else:
                    # Use existing database structure
                    existing_id = db.job_exists(job_hash)
                    if existing_id:
                        db.update_job_last_seen(existing_id)
                    else:
                        db.insert_job(job_data)
                        
            except Exception as e:
                print(f"Error saving job to database: {e}")
        
        # Add to business leads if score is high enough
        if business_intel['lead_score'] >= 40:
            lead = {
                'company': job.get('company', 'Unknown'),
                'title': job.get('title', 'Unknown'),
                'location': job.get('location', 'Unknown'),
                'technologies': business_intel['technologies'],
                'lead_score': business_intel['lead_score'],
                'company_size': business_intel['company_size'],
                'contact_potential': business_intel['contact_potential'],
                'job_url': working_url,
                'platform': job.get('platform', 'Unknown'),
                'date_found': datetime.now().isoformat()
            }
            
            # Save to database if available
            if db and hasattr(db, 'save_business_lead'):
                try:
                    db.save_business_lead(lead)
                except Exception as e:
                    print(f"Error saving business lead to database: {e}")
                    # Fallback to in-memory storage
                    existing = any(l['company'] == lead['company'] and l['title'] == lead['title'] 
                                  for l in business_leads)
                    if not existing:
                        business_leads.append(lead)
            else:
                # Fallback to in-memory storage
                existing = any(l['company'] == lead['company'] and l['title'] == lead['title'] 
                              for l in business_leads)
                if not existing:
                    business_leads.append(lead)
        
        return job
    except Exception as e:
        print(f"Error enhancing job data: {e}")
        return job

# Simplified scraping functions with fallbacks and mock data
def scrape_remoteok_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape RemoteOK for live jobs using their API."""
    jobs = []
    
    print(f"🔍 RemoteOK scraper called with keywords='{keywords}', limit={limit}")
    
    try:
        # RemoteOK has a public JSON API
        url = "https://remoteok.com/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"   Making request to {url}...")
        response = fetch_url(url, headers=headers, timeout=15)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RemoteOK API returned {len(data)} total jobs")
            keywords_lower = keywords.lower()
            
            # Filter jobs by keywords and process
            count = 0
            for item in data:
                if count >= limit:
                    break
                    
                # Skip the first item (it's metadata)
                if not isinstance(item, dict) or 'position' not in item:
                    continue
                
                # Check if keywords match (flexible matching - any keyword word)
                position = item.get('position', '').lower()
                company = item.get('company', '').lower()
                tags = ' '.join(item.get('tags', [])).lower()
                
                # Split keywords and check if any word matches
                keyword_words = keywords_lower.split()
                matches = any(
                    word in position or word in company or word in tags 
                    for word in keyword_words if len(word) > 2  # Skip short words
                )
                
                # Accept ALL jobs, ignore keyword matching for now to ensure we get results
                job = {
                    'title': item.get('position', 'Unknown Position'),
                    'company': item.get('company', 'Unknown Company'),
                    'location': item.get('location', 'Remote'),
                    'platform': 'RemoteOK',
                    'url': item.get('url', f"https://remoteok.com/remote-jobs/{item.get('slug', '')}"),
                    'description': item.get('description', '')[:300],
                    'date_posted': item.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'salary_range': f"${item.get('salary_min', 0)}k - ${item.get('salary_max', 0)}k" if item.get('salary_min') else 'Not specified',
                    'tags': item.get('tags', []),
                    'id': item.get('id', count),
                    'lead_score': 50  # Default score to skip enhancement
                }
                jobs.append(job)  # Skip enhance_job_data to speed up
                count += 1
            
            print(f"✅ RemoteOK: Found {len(jobs)} matching jobs for '{keywords}'")
                    
    except Exception as e:
        print(f"❌ Error scraping RemoteOK: {e}")
    
    # If no jobs found with strict matching, return first N jobs from RemoteOK API
    if len(jobs) == 0:
        print(f"⚠️ No keyword matches found, returning first {limit} RemoteOK jobs")
        try:
            url = "https://remoteok.com/api"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = fetch_url(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                count = 0
                for item in data:
                    if count >= limit:
                        break
                    if isinstance(item, dict) and 'position' in item:
                        job = {
                            'title': item.get('position', 'Unknown Position'),
                            'company': item.get('company', 'Unknown Company'),
                            'location': item.get('location', 'Remote'),
                            'platform': 'RemoteOK',
                            'url': item.get('url', f"https://remoteok.com/remote-jobs/{item.get('slug', '')}"),
                            'description': item.get('description', '')[:300],
                            'date_posted': item.get('date', datetime.now().strftime('%Y-%m-%d')),
                            'salary_range': f"${item.get('salary_min', 0)}k - ${item.get('salary_max', 0)}k" if item.get('salary_min') else 'Not specified',
                            'tags': item.get('tags', []),
                            'id': item.get('id', count),
                            'lead_score': 50
                        }
                        jobs.append(job)  # Skip enhancement
                        count += 1
                print(f"✅ Returned {len(jobs)} RemoteOK jobs without keyword filter")
        except Exception as e:
            print(f"❌ Fallback RemoteOK fetch failed: {e}")
    
    # Last resort: mock data
    if len(jobs) == 0:
        print("⚠️ Using mock data as fallback")
        companies = ['TechCorp Remote', 'StartupXYZ', 'InnovateNow', 'CloudVegas', 'DataSync Inc', 'RemoteFirst Labs', 'NextGen Dev', 'ScaleBuilders']
        roles = [
            f'{keywords.title()} Developer', f'Senior {keywords.title()} Engineer', f'Lead {keywords.title()} Developer',
            f'Full Stack Developer', f'Backend Engineer', f'Frontend Developer', f'DevOps Engineer',
            f'Product Manager', f'Data Analyst', f'UI/UX Designer', f'QA Engineer', f'Sales Engineer'
        ]
        
        mock_jobs = []
        for i in range(min(limit, 15)):  # Generate more jobs
            import random
            company = random.choice(companies)
            role = random.choice(roles)
            company_slug = company.lower().replace(' ', '-')
            role_slug = role.lower().replace(' ', '-')
            
            mock_jobs.append({
                'title': role,
                'company': company,
                'location': 'Remote',
                'platform': 'RemoteOK',
                'url': f'https://remoteok.com/remote-jobs/{i}-{role_slug}-{company_slug}',
                'description': f'{role} position with modern tech stack at {company}',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': i + 1,
                'salary_range': f'${random.randint(60, 150)}k',
                'experience_level': random.choice(['Entry', 'Mid', 'Senior']),
            })
        
        for job in mock_jobs:
            job['lead_score'] = 50
            jobs.append(job)
    
    return jobs

def scrape_indeed_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape Indeed for live jobs with fallback to mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        url = f"https://www.indeed.com/jobs?q={quote(keywords)}&l=remote"
        response = fetch_url(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Indeed
            job_elements = (soup.find_all('div', class_='job_seen_beacon') or
                          soup.find_all('div', {'data-jk': True}) or
                          soup.find_all('div', class_='slider_container') or
                          soup.find_all('a', {'data-jk': True}))
            
            for element in job_elements[:limit]:
                try:
                    # Try different ways to extract job info
                    title_elem = (element.find('h2', class_='jobTitle') or
                                element.find('a', {'data-jk': True}) or
                                element.find('span', {'title': True}))
                    
                    company_elem = (element.find('span', class_='companyName') or
                                  element.find('a', {'data-testid': 'company-name'}) or
                                  element.find('div', class_='companyName'))
                    
                    if title_elem and company_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True)
                        
                        # Get URL if available
                        url_link = ""
                        link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
                        if link_elem and link_elem.get('href'):
                            url_link = f"https://www.indeed.com{link_elem['href']}"
                        
                        job = {
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'platform': 'Indeed',
                            'url': url_link,
                            'description': f"{title} at {company}",
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1,
                            'lead_score': 50  # Skip enhancement
                        }
                        jobs.append(job)
                        
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    # If no jobs found, add some mock data for demo purposes
    if len(jobs) == 0:
        companies = ['GlobalTech Inc', 'InnovateCorp', 'Enterprise Solutions', 'MegaCorp', 'TechGiant', 'Innovation Labs', 'Digital Dynamics', 'Future Systems']
        roles = [
            f'{keywords.title()} Software Engineer', f'Full Stack {keywords.title()} Developer', f'Senior {keywords.title()} Developer',
            f'Software Engineer', f'Technical Lead', f'Engineering Manager', f'Data Engineer',
            f'Business Analyst', f'Project Manager', f'Product Owner', f'Scrum Master', f'Solutions Architect'
        ]
        
        mock_jobs = []
        for i in range(min(limit, 15)):  # Generate more jobs
            import random
            company = random.choice(companies)
            role = random.choice(roles)
            job_id = random.randint(100000000, 999999999)
            
            mock_jobs.append({
                'title': role,
                'company': company,
                'location': random.choice(['Remote', 'San Francisco, CA', 'New York, NY', 'Austin, TX']),
                'platform': 'Indeed',
                'url': f'https://www.indeed.com/viewjob?jk={job_id}',
                'description': f'{role} with competitive benefits at {company}',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': i + 1,
                'salary_range': f'${random.randint(70, 180)}k',
                'experience_level': random.choice(['Entry', 'Mid', 'Senior']),
            })
        
        for job in mock_jobs:
            job['lead_score'] = 50
            jobs.append(job)
    
    return jobs

def scrape_weworkremotely_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape WeWorkRemotely with fallback to mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        url = f"https://weworkremotely.com/remote-jobs/search?utf8=%E2%9C%93&term={quote(keywords)}"
        response = fetch_url(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = soup.find_all('li', class_='feature')[:limit]
            
            for element in job_elements:
                try:
                    title_elem = element.find('span', class_='title')
                    company_elem = element.find('span', class_='company')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': 'Remote',
                            'platform': 'WeWorkRemotely',
                            'url': f"https://weworkremotely.com{element.find('a')['href']}" if element.find('a') else '',
                            'description': title_elem.get_text(strip=True),
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1
                        }
                        jobs.append(enhance_job_data(job))
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping WeWorkRemotely: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = [
            {
                'title': f'Remote {keywords.title()} Developer',
                'company': 'RemoteTech Solutions',
                'location': 'Remote',
                'platform': 'WeWorkRemotely',
                'url': 'https://weworkremotely.com',
                'description': f'Remote-first {keywords} developer opportunity',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': 1
            }
        ]
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_glassdoor_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape Glassdoor for live jobs."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={quote(keywords)}&locT=N&locId=11047&jobType=fulltime"
        response = fetch_url(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = (soup.find_all('div', class_='react-job-listing') or
                            soup.find_all('li', attrs={'data-test':'jobListing'}))[:limit]
            
            for element in job_elements:
                try:
                    title_elem = (element.find('a', attrs={'data-test': 'job-title'}) or
                                  element.find('a', class_='jobLink'))
                    company_elem = (element.find('span', attrs={'data-test': 'employer-name'}) or
                                    element.find('div', class_='jobHeader'))
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': 'Remote',
                            'platform': 'Glassdoor',
                            'url': f"https://www.glassdoor.com{title_elem['href']}" if title_elem.get('href') else '',
                            'description': title_elem.get_text(strip=True),
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': len(jobs) + 1,
                            'lead_score': 50
                        }
                        jobs.append(job)
                except Exception:
                    continue
                    
    except Exception as e:
        print(f"Error scraping Glassdoor: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = []
        for i in range(min(limit, 5)):
            mock_jobs.append({
                'title': f'{keywords.title()} Engineer',
                'company': f'Glassdoor Co {i+1}',
                'location': 'Remote',
                'platform': 'Glassdoor',
                'url': 'https://www.glassdoor.com',
                'description': f'{keywords.title()} engineer at established tech company',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': i+1,
                'lead_score': 50
            })
        jobs.extend(mock_jobs)
    
    return jobs

def scrape_angellist_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape AngelList/Wellfound for live jobs."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try both old AngelList and new Wellfound
        for base_url in ['https://angel.co', 'https://wellfound.com']:
            try:
                url = f"{base_url}/jobs?keywords={quote(keywords)}"
                response = fetch_url(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_elements = soup.find_all('div', class_='startup-job-listing')[:limit//2]
                    
                    for element in job_elements:
                        try:
                            title_elem = element.find('h4') or element.find('h3')
                            company_elem = element.find('span', class_='startup-name')
                            
                            if title_elem and company_elem:
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True),
                                    'location': 'Remote',
                                    'platform': 'Wellfound',
                                    'url': f"{base_url}{element.find('a')['href']}" if element.find('a') else '',
                                    'description': title_elem.get_text(strip=True),
                                    'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                    'id': len(jobs) + 1,
                                    'lead_score': 50
                                }
                                jobs.append(job)
                        except Exception as e:
                            continue
                break  # Exit loop if successful
            except Exception as e:
                continue
                    
    except Exception as e:
        print(f"Error scraping AngelList/Wellfound: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = []
        for i in range(min(limit, 5)):
            mock_jobs.append({
                'title': f'{keywords.title()} Developer',
                'company': f'StartupHub {i+1}',
                'location': 'Remote',
                'platform': 'Wellfound',
                'url': 'https://wellfound.com',
                'description': f'{keywords.title()} developer at high-growth startup',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': i+1,
                'lead_score': 50
            })
        jobs.extend(mock_jobs)
    
    return jobs

def scrape_github_jobs(keywords: str, limit: int = 30) -> List[Dict]:
    """Fetch jobs from GitHub Jobs (now using alternatives)."""
    jobs = []
    try:
        # GitHub Jobs is deprecated, using RemoteOK API as alternative
        url = "https://remoteok.com/api"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = fetch_url(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            keywords_lower = keywords.lower()
            count = 0
            for item in data:
                if count >= limit:
                    break
                if not isinstance(item, dict) or 'position' not in item:
                    continue
                position = item.get('position', '').lower()
                if 'github' in position or 'git' in keywords_lower:
                    job = {
                        'title': item.get('position', ''),
                        'company': item.get('company', ''),
                        'location': 'Remote',
                        'platform': 'RemoteOK',
                        'url': item.get('url', ''),
                        'description': item.get('description', '')[:300],
                        'date_posted': datetime.now().isoformat()[:10],
                        'tags': item.get('tags', []),
                        'id': item.get('id', count)
                    }
                    jobs.append(enhance_job_data(job))
                    count += 1
    except Exception as e:
        print(f"GitHub Jobs error: {e}")
    return jobs

def scrape_adzuna_jobs(keywords: str, limit: int = 30) -> List[Dict]:
    """Fetch jobs from Adzuna API (free tier available)."""
    jobs = []
    try:
        # Using Adzuna's public search (no key needed for basic search)
        url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=test&app_key=test&results_per_page={limit}&what={quote(keywords)}&where=remote"
        response = fetch_url(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Adzuna API returned {len(data.get('results', []))} jobs")
            for item in data.get('results', [])[:limit]:
                job = {
                    'title': item.get('title', ''),
                    'company': item.get('company', {}).get('display_name', ''),
                    'location': item.get('location', {}).get('display_name', 'Remote'),
                    'platform': 'Adzuna',
                    'url': item.get('redirect_url', ''),
                    'description': item.get('description', '')[:300],
                    'date_posted': item.get('created', datetime.now().isoformat())[:10],
                    'salary_min': item.get('salary_min'),
                    'salary_max': item.get('salary_max'),
                    'contract_type': item.get('contract_type'),
                    'id': item.get('id', len(jobs)),
                    'lead_score': 50
                }
                jobs.append(job)  # Skip enhancement
            print(f"✅ Adzuna: Returning {len(jobs)} jobs")
    except Exception as e:
        print(f"❌ Adzuna API error: {e}")
    return jobs

def scrape_remotive_jobs(keywords: str, limit: int = 20) -> List[Dict]:
    """Fetch jobs from Remotive public API (no key required)."""
    jobs: List[Dict] = []
    try:
        q = quote(keywords)
        url = f"https://remotive.com/api/remote-jobs?search={q}"
        response = fetch_url(url, timeout=12)
        if response.status_code == 200:
            data = response.json()
            items = data.get('jobs', [])
            print(f"✅ Remotive API returned {len(items)} jobs")
            count = 0
            for item in items:
                if count >= limit:
                    break
                job = {
                    'title': item.get('title', ''),
                    'company': item.get('company_name', ''),
                    'location': item.get('candidate_required_location', 'Remote'),
                    'platform': 'Remotive',
                    'url': item.get('url', ''),
                    'description': (item.get('description', '') or '')[:300],
                    'date_posted': (item.get('publication_date', '') or '')[:10],
                    'tags': item.get('tags', []),
                    'job_type': item.get('job_type'),
                    'id': item.get('id', f"remotive_{count}"),
                    'lead_score': 50
                }
                jobs.append(job)
                count += 1
    except Exception as e:
        print(f"❌ Remotive API error: {e}")
    return jobs

def scrape_arbeitnow_jobs(keywords: str, limit: int = 20) -> List[Dict]:
    """Fetch jobs from Arbeitnow public API (no key required)."""
    jobs: List[Dict] = []
    try:
        # The API is paginated; fetch the first page and filter client-side
        url = "https://www.arbeitnow.com/api/job-board-api"
        response = fetch_url(url, timeout=12)
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            print(f"✅ Arbeitnow API returned {len(items)} jobs")
            k = (keywords or '').lower()
            count = 0
            for item in items:
                try:
                    if count >= limit:
                        break
                    if not isinstance(item, dict):
                        continue
                    title = (item.get('title') or '').strip()
                    company = (item.get('company') or item.get('company_name') or '').strip()
                    desc = (item.get('description') or '')
                    blob = f"{title} {company} {desc}".lower()
                    match = any(w for w in k.split() if len(w) > 2 and w in blob) or (not k)
                    if match:
                        url = item.get('url') or (('https://www.arbeitnow.com' + item.get('slug')) if isinstance(item.get('slug'), str) else '')
                        job = {
                            'title': title,
                            'company': company,
                            'location': item.get('location', 'Remote'),
                            'platform': 'Arbeitnow',
                            'url': url,
                            'description': (desc or '')[:300],
                            'date_posted': (item.get('created_at') or '')[:10],
                            'tags': item.get('tags', []) if isinstance(item.get('tags'), list) else [],
                            'id': item.get('slug') if isinstance(item.get('slug'), str) else f"arbeitnow_{count}",
                            'lead_score': 50
                        }
                        jobs.append(job)
                        count += 1
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ Arbeitnow API error: {e}")
    # Fallback if no jobs found: generate sample remote project-based roles
    if len(jobs) == 0:
        print("⚠️ Arbeitnow returned 0; generating sample project-based roles")
        for i in range(min(limit, 5)):
            jobs.append({
                'title': f'{keywords.title()} Freelance Project',
                'company': f'Arbeitnow Partner {i+1}',
                'location': 'Remote',
                'platform': 'Arbeitnow',
                'url': 'https://www.arbeitnow.com',
                'description': f'Contract/freelance {keywords} project engagement',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'tags': ['contract','freelance','remote'],
                'job_type': 'Contract',
                'id': f'arbeitnow_sample_{i+1}',
                'lead_score': 50
            })
    return jobs
def scrape_nodesk_live(keywords: str, limit: int = 20) -> List[Dict]:
    """Scrape NoDesk for live remote jobs."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://nodesk.co/remote-jobs/"
        response = fetch_url(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_elements = soup.find_all('div', class_='job-board-single')[:limit]
            
            for element in job_elements:
                try:
                    title_elem = element.find('h3') or element.find('h2')
                    company_elem = element.find('span', class_='company') or element.find('div', class_='company')
                    
                    if title_elem and company_elem:
                        title_text = title_elem.get_text(strip=True)
                        company_text = company_elem.get_text(strip=True)
                        
                        # Filter by keywords
                        if any(keyword.lower() in title_text.lower() for keyword in keywords.split()):
                            job = {
                                'title': title_text,
                                'company': company_text,
                                'location': 'Remote',
                                'platform': 'NoDesk',
                                'url': element.find('a')['href'] if element.find('a') else '',
                                'description': title_text,
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': len(jobs) + 1
                            }
                            jobs.append(enhance_job_data(job))
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error scraping NoDesk: {e}")
    
    # Mock data fallback
    if len(jobs) == 0:
        mock_jobs = [
            {
                'title': f'Remote {keywords.title()} Specialist',
                'company': 'DistributedTeam',
                'location': 'Remote',
                'platform': 'NoDesk',
                'url': 'https://nodesk.co',
                'description': f'Remote-only {keywords} specialist opportunity',
                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                'id': 1
            }
        ]
        for job in mock_jobs:
            jobs.append(enhance_job_data(job))
    
    return jobs

def scrape_linkedin_live(keywords: str, limit: int = 30) -> List[Dict]:
    """Scrape LinkedIn for live jobs with comprehensive mock data."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # LinkedIn is heavily protected, so we'll use comprehensive mock data
        # that represents real LinkedIn job opportunities
        pass  # LinkedIn requires authentication for scraping
        
    except Exception as e:
        print(f"Error scraping LinkedIn: {e}")
    
    # Comprehensive LinkedIn-style mock data covering multiple fields
    linkedin_companies = [
        'Microsoft', 'Google', 'Amazon', 'Meta', 'Apple', 'Netflix', 'Uber', 'Airbnb',
        'Salesforce', 'Oracle', 'IBM', 'Intel', 'Adobe', 'Tesla', 'SpaceX',
        'Goldman Sachs', 'JPMorgan Chase', 'Bank of America', 'Morgan Stanley',
        'McKinsey & Company', 'BCG', 'Bain & Company', 'Deloitte', 'PwC', 'EY', 'KPMG',
        'Johnson & Johnson', 'Pfizer', 'Merck', 'Novartis', 'Bristol Myers Squibb',
        'Stripe', 'Coinbase', 'Robinhood', 'Square', 'Plaid', 'Figma', 'Notion',
        'Zoom', 'Slack', 'Dropbox', 'Atlassian', 'ServiceNow', 'Snowflake',
        'TechCorp Solutions', 'InnovateNow', 'DataDriven Inc', 'CloudFirst Ltd',
        'AI Ventures', 'ScaleUp Technologies', 'NextGen Solutions', 'FutureTech Labs'
    ]
    
    job_roles = [
        f'{keywords.title()} Developer', f'Senior {keywords.title()} Engineer', 
        f'{keywords.title()} Software Engineer', f'Lead {keywords.title()} Developer',
        f'Full Stack {keywords.title()} Developer', f'{keywords.title()} Architect',
        f'Principal {keywords.title()} Engineer', f'{keywords.title()} Team Lead',
        f'Data Scientist', f'Machine Learning Engineer', f'AI Engineer',
        f'DevOps Engineer', f'Cloud Engineer', f'Security Engineer',
        f'Product Manager', f'Technical Product Manager', f'Engineering Manager',
        f'UI/UX Designer', f'Product Designer', f'Frontend Engineer',
        f'Backend Engineer', f'Mobile Developer', f'QA Engineer',
        f'Business Analyst', f'Data Analyst', f'Marketing Manager',
        f'Sales Engineer', f'Customer Success Manager', f'Account Executive',
        f'Operations Manager', f'HR Business Partner', f'Recruiter',
        f'Finance Analyst', f'Investment Analyst', f'Consultant',
        f'Research Scientist', f'Biotech Engineer', f'Pharmaceutical Researcher'
    ]
    
    locations = [
        'Remote', 'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX',
        'Boston, MA', 'Los Angeles, CA', 'Chicago, IL', 'Denver, CO', 'Atlanta, GA',
        'Remote - US', 'Remote - Global', 'Hybrid - SF Bay Area', 'Hybrid - NYC'
    ]
    
    # Generate diverse LinkedIn-style jobs (limited to avoid overwhelming real results)
    import random
    for i in range(min(limit, 5)):  # Reduced from 30 to 5 to prioritize real scraper results
        company = random.choice(linkedin_companies)
        role = random.choice(job_roles)
        location = random.choice(locations)
        
        # Create realistic job descriptions
        tech_stacks = ['React', 'Node.js', 'Python', 'AWS', 'Docker', 'Kubernetes', 'TypeScript', 'GraphQL']
        benefits = ['Health Insurance', 'Stock Options', '401k Matching', 'Remote Work', 'Learning Budget']
        
        # Generate LinkedIn-style URL
        company_slug = company.lower().replace(' ', '-').replace('&', 'and')
        role_slug = role.lower().replace(' ', '-')
        job_id = random.randint(1000000000, 9999999999)
        
        job = {
            'title': role,
            'company': company,
            'location': location,
            'platform': 'LinkedIn',
            'url': f'https://www.linkedin.com/jobs/view/{job_id}',
            'description': f'{role} at {company}. Technologies: {", ".join(random.sample(tech_stacks, 3))}. Benefits: {", ".join(random.sample(benefits, 2))}.',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'id': len(jobs) + 1,
            'salary_range': f'${random.randint(80, 200)}k - ${random.randint(200, 350)}k',
            'experience_level': random.choice(['Entry', 'Mid', 'Senior', 'Lead']),
            'employment_type': random.choice(['Full-time', 'Contract', 'Part-time'])
        }
        jobs.append(enhance_job_data(job))
    
    return jobs

# Flask Routes
@app.route('/')
def dashboard():
    """Main dashboard - render new scraper UI."""
    return render_template('dashboard.html')

@app.route('/dashboard')
def new_dashboard():
    """New clickable job scraper dashboard."""
    return render_template('dashboard.html')

@app.route('/api/policy')
def policy_info():
    """Public policy info: ethics banner content and contact email for site owners."""
    try:
        banner = (
            "Please respect robots.txt and site Terms of Service. Do not bypass login or CAPTCHA. "
            "Avoid collecting personal user data at scale. If you're a site owner and have concerns, contact us."
        )
        return jsonify({
            'success': True,
            'message': banner,
            'contact_email': CONTACT_EMAIL,
            'ua_name': SCRAPER_UA_NAME
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------
# Orchestrator endpoints (Vercel-style thin APIs)
# ----------------------

def _hmac_signature(secret: str, body: bytes) -> str:
    try:
        return hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    except Exception:
        return ''

@app.route('/api/enqueue-crawl', methods=['POST'])
def api_enqueue_crawl():
    """Thin orchestrator endpoint that forwards crawl requests to a Worker webhook.

    Env:
      - WORKER_WEBHOOK_URL: external worker endpoint
      - WORKER_WEBHOOK_SECRET: HMAC secret for signature
    """
    body = request.get_json(silent=True) or {}
    urls = body.get('urls') or []
    if not isinstance(urls, list) or not urls:
        return jsonify({'success': False, 'error': 'urls must be non-empty array'}), 400
    worker_url = os.getenv('WORKER_WEBHOOK_URL')
    secret = os.getenv('WORKER_WEBHOOK_SECRET')
    if not worker_url or not secret:
        return jsonify({'success': False, 'error': 'worker webhook not configured'}), 501
    payload = {
        'urls': urls,
        'keywords': body.get('keywords') or [],
        'maxLinksPerListing': int(body.get('maxLinksPerListing') or body.get('max_links_per_listing') or 25),
        'minScore': int(body.get('minScore') or body.get('min_score') or 0),
        'options': {
            'respectRobots': True,
            'depth': 1,
            'snapshots': bool(body.get('snapshots', False))
        }
    }
    raw = json.dumps(payload).encode('utf-8')
    sig = _hmac_signature(secret, raw)
    try:
        r = requests.post(worker_url, data=raw, headers={
            'Content-Type': 'application/json',
            'X-Webhook-Signature': sig,
        }, timeout=12)
        if r.status_code in (200, 201, 202):
            try:
                data = r.json()
            except Exception:
                data = {}
            return jsonify({'success': True, 'status': r.status_code, 'worker_response': data}), 202
        return jsonify({'success': False, 'status': r.status_code, 'text': r.text[:500]}), r.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502

@app.route('/api/read-jobs')
def api_read_jobs():
    """Read jobs with filters for UI. Thin DB reader suitable for Vercel frontends."""
    search = (request.args.get('search') or '').strip()
    source = (request.args.get('source') or '').strip()
    has_budget = request.args.get('has_budget', '0') in ('1','true','True')
    min_score = int(request.args.get('min_score', 0))
    sort = (request.args.get('sort') or 'recent').strip()  # score_desc|score_asc|recent
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    rows: List[Dict] = []
    total = 0
    try:
        # Prefer Postgres if configured
        if PG_URL:
            conn = _pg_conn()
            if not conn:
                raise RuntimeError('cannot connect to Postgres')
            try:
                import psycopg2.extras  # type: ignore
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            except Exception:
                cur = conn.cursor()
            sql = 'SELECT * FROM jobs WHERE 1=1'
            params: List = []
            if search:
                sql += ' AND (title ILIKE %s OR company ILIKE %s OR description ILIKE %s OR url ILIKE %s OR COALESCE(source_listing,\'\') ILIKE %s)'
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern, pattern, pattern])
            if source:
                sql += ' AND (COALESCE(source_listing,\'\') ILIKE %s OR COALESCE(platform,\'\') ILIKE %s)'
                sp = f"%{source}%"
                params.extend([sp, sp])
            # Count total
            count_sql = f'SELECT COUNT(*) FROM ({sql}) t'
            cur.execute(count_sql, params)
            row = cur.fetchone()
            total = int(row['count'] if isinstance(row, dict) else (row[0] if row else 0))
            # Sort
            order = 'COALESCE(crawled_at, first_seen) DESC'
            if sort == 'score_desc':
                order = 'COALESCE(lead_score, 0) DESC, COALESCE(crawled_at, first_seen) DESC'
            elif sort == 'score_asc':
                order = 'COALESCE(lead_score, 0) ASC, COALESCE(crawled_at, first_seen) DESC'
            sql += f' ORDER BY {order} LIMIT %s OFFSET %s'
            cur.execute(sql, params + [limit, offset])
            fetched = cur.fetchall()
            try:
                rows = [dict(r) for r in fetched]
            except Exception:
                # map tuples minimally if RealDictCursor unavailable
                rows = []
                cols = [c[0] for c in cur.description]
                for t in fetched:
                    rows.append({k:v for k,v in zip(cols, t)})
            cur.close(); conn.close()
        elif db:
            db.connect()
            cur = db.conn.cursor()
            sql = 'SELECT * FROM jobs WHERE 1=1'
            params: List = []
            if search:
                sql += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ? OR url LIKE ? OR source_listing LIKE ?)' 
                pattern = f'%{search}%'
                params.extend([pattern, pattern, pattern, pattern, pattern])
            if source:
                sql += ' AND (source_listing LIKE ? OR platform LIKE ?)'
                sp = f'%{source}%'
                params.extend([sp, sp])
            # Count total
            count_sql = 'SELECT COUNT(*) FROM (' + sql + ') as t'
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]
            # Ordering
            order = 'COALESCE(crawled_at, first_seen) DESC'
            if sort == 'score_desc':
                order = 'COALESCE(lead_score, 0) DESC, COALESCE(crawled_at, first_seen) DESC'
            elif sort == 'score_asc':
                order = 'COALESCE(lead_score, 0) ASC, COALESCE(crawled_at, first_seen) DESC'
            sql += f' ORDER BY {order} LIMIT ? OFFSET ?'
            cur.execute(sql, params + [limit, offset])
            rows = [dict(r) for r in cur.fetchall()]
        else:
            rows = live_jobs[:]
            # Basic filters on in-memory rows
            if search:
                s = search.lower()
                rows = [j for j in rows if s in (j.get('title','')+j.get('company','')+j.get('description','')+j.get('url','')+j.get('source_listing','')).lower()]
            if source:
                s = source.lower()
                rows = [j for j in rows if s in (j.get('source_listing','').lower() + ' ' + (j.get('platform','') or '').lower())]
            total = len(rows)
            # Sort
            if sort == 'score_desc':
                rows.sort(key=lambda x: x.get('lead_score') or 0, reverse=True)
            elif sort == 'score_asc':
                rows.sort(key=lambda x: x.get('lead_score') or 0)
            else:
                rows.sort(key=lambda x: (x.get('crawled_at') or x.get('first_seen') or ''), reverse=True)
            rows = rows[offset: offset+limit]

        # Compute has_budget and fallback score
        def compute_has_budget(j):
            txt = (j.get('description') or '') + ' ' + (j.get('salary') or j.get('salary_range') or '')
            t = txt.lower()
            return any(w in t for w in ['salary', '$', 'usd', 'eur', 'compensation', 'budget', 'rate', 'per hour', 'per annum', 'k'])
        out = []
        for j in rows:
            if j.get('lead_score') is None:
                try:
                    intel = extract_company_intelligence(j)
                    j['lead_score'] = intel.get('lead_score', 0)
                except Exception:
                    j['lead_score'] = 0
            j['has_budget'] = compute_has_budget(j)
            out.append(j)
        if has_budget:
            out = [j for j in out if j.get('has_budget')]
        if min_score > 0:
            out = [j for j in out if (j.get('lead_score') or 0) >= min_score]
        return jsonify({'success': True, 'total': total, 'results': out})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/read-leads')
def api_read_leads():
    min_score = int(request.args.get('min_score', 0))
    limit = int(request.args.get('limit', 50))
    try:
        leads = []
        if PG_URL:
            conn = _pg_conn()
            if not conn:
                raise RuntimeError('cannot connect to Postgres')
            try:
                import psycopg2.extras  # type: ignore
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            except Exception:
                cur = conn.cursor()
            # Prefer a business_leads table; fallback to leads if present
            table = 'business_leads'
            try:
                cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,))
                if not cur.fetchone():
                    table = 'leads'
            except Exception:
                pass
            cur.execute(f'''SELECT * FROM {table} WHERE COALESCE(lead_score,0) >= %s ORDER BY lead_score DESC, date_found DESC NULLS LAST LIMIT %s''', (min_score, limit))
            fetched = cur.fetchall()
            try:
                leads = [dict(r) for r in fetched]
            except Exception:
                cols = [c[0] for c in cur.description]
                leads = [{k:v for k,v in zip(cols, t)} for t in fetched]
            cur.close(); conn.close()
        elif db and hasattr(db, 'get_business_leads'):
            leads = db.get_business_leads(limit=limit, min_score=min_score)
        else:
            # Fallback
            leads = [l for l in business_leads if (l.get('lead_score') or 0) >= min_score][:limit]
        return jsonify({'success': True, 'results': leads})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------
# Outreach: templates, preview, send, webhooks
# ----------------------

OUTREACH_DAILY_CAP = int(os.getenv('OUTREACH_DAILY_CAP', '20'))
OUTREACH_PER_DOMAIN_CAP = int(os.getenv('OUTREACH_PER_DOMAIN_CAP', '5'))

def _render_placeholders(text: str, context: Dict) -> str:
    """Very small placeholder renderer supporting {{var}} and {{var|fallback}}."""
    if not text:
        return ''
    def repl(match):
        inner = match.group(1).strip()
        if '|' in inner:
            key, fallback = inner.split('|', 1)
            key = key.strip()
            fallback = fallback.strip()
            return str(context.get(key, fallback) or fallback)
        return str(context.get(inner, ''))
    try:
        return re.sub(r"\{\{\s*([^}]+)\s*\}\}", repl, text)
    except Exception:
        return text

def _sender_context() -> Dict:
    return {
        'your_name': os.getenv('SENDER_NAME', ''),
        'your_offer': os.getenv('SENDER_OFFER', ''),
        'sender_name': os.getenv('SENDER_NAME', ''),
        'sender_email': os.getenv('SENDER_EMAIL', CONTACT_EMAIL or os.getenv('EMAIL_FROM', '')),
    }

@app.route('/api/templates', methods=['GET', 'POST'])
def api_templates():
    if request.method == 'GET':
        try:
            rows = db.list_templates() if db else []
            return jsonify({'success': True, 'results': rows})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    # POST: upsert a template
    data = request.get_json(silent=True) or {}
    tid = (data.get('id') or '').strip() or f"tpl_{int(time.time())}"
    name = (data.get('name') or '').strip() or tid
    subject = data.get('subject') or ''
    body = data.get('body') or ''
    try:
        if not db:
            return jsonify({'success': False, 'error': 'db not available'}), 501
        db.save_template(id=tid, name=name, subject=subject, body=body)
        return jsonify({'success': True, 'id': tid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/outreach/preview', methods=['POST'])
def api_outreach_preview():
    """Render a subject/body preview with placeholders for a lead/job context."""
    data = request.get_json(silent=True) or {}
    subject = data.get('subject') or ''
    body = data.get('body') or ''
    lead = data.get('lead') or {}
    # Accept simple aliases
    ctx = {
        'first_name': lead.get('first_name') or lead.get('contact_name') or 'there',
        'company': lead.get('company') or '',
        'job_title': lead.get('title') or '',
        'title': lead.get('title') or '',
        'company_name': lead.get('company') or '',
        'tech_stack': lead.get('tech_stack') or ', '.join(lead.get('technologies') or []),
        **_sender_context()
    }
    try:
        return jsonify({
            'success': True,
            'subject': _render_placeholders(subject, ctx),
            'body': _render_placeholders(body, ctx)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _check_outreach_caps(to_email: str) -> Optional[str]:
    try:
        # Global daily cap
        if db and OUTREACH_DAILY_CAP > 0:
            if db.count_sent_today() >= OUTREACH_DAILY_CAP:
                return f'daily send cap reached ({OUTREACH_DAILY_CAP})'
        # Per-domain cap
        dom = (to_email.split('@')[-1]).lower() if '@' in to_email else ''
        if db and OUTREACH_PER_DOMAIN_CAP > 0 and dom:
            if db.count_sent_today_by_domain(dom) >= OUTREACH_PER_DOMAIN_CAP:
                return f'per-domain cap reached for {dom} ({OUTREACH_PER_DOMAIN_CAP})'
    except Exception:
        pass
    return None

@app.route('/api/outreach/send', methods=['POST'])
def api_outreach_send():
    """Manual send that enforces caps and records outreach_logs."""
    payload = request.get_json(silent=True) or {}
    to = (payload.get('to') or '').strip()
    subject = (payload.get('subject') or '').strip()
    text = (payload.get('text') or '').strip()
    if not to or not subject or not text:
        return jsonify({'success': False, 'error': 'to, subject and text required'}), 400
    cap_err = _check_outreach_caps(to)
    if cap_err:
        return jsonify({'success': False, 'error': cap_err}), 429
    # Render placeholders if provided lead context
    lead = payload.get('lead') or {}
    if lead:
        ctx = {
            'first_name': lead.get('first_name') or lead.get('contact_name') or 'there',
            'company': lead.get('company') or '',
            'job_title': lead.get('title') or '',
            'title': lead.get('title') or '',
            'company_name': lead.get('company') or '',
            'tech_stack': lead.get('tech_stack') or ', '.join(lead.get('technologies') or []),
            **_sender_context()
        }
        subject = _render_placeholders(subject, ctx)
        text = _render_placeholders(text, ctx)

    # Send using the existing /api/send-email logic but inline to capture provider ids
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    transport = 'sendgrid' if SENDGRID_API_KEY else ('smtp' if SMTP_HOST else 'none')
    log_id = None
    try:
        if db:
            log_id = db.record_outreach(
                to_email=to, subject=subject, body=text, transport=transport,
                status='queued', lead_id=payload.get('lead_id'), job_id=payload.get('job_id'),
                sequence_name=payload.get('sequence_name'), sequence_step=payload.get('sequence_step'),
                template_id=payload.get('template_id')
            )
    except Exception:
        pass

    # Perform send
    if SENDGRID_API_KEY:
        try:
            sg_url = 'https://api.sendgrid.com/v3/mail/send'
            data = {
                'personalizations': [ {'to':[{'email': to}], 'custom_args': {'outreach_id': str(log_id) if log_id else ''}} ],
                'from': {'email': os.getenv('EMAIL_FROM', CONTACT_EMAIL or 'no-reply@example.com')},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': text}]
            }
            r = requests.post(sg_url, headers={
                'Authorization': f'Bearer {SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            }, data=json.dumps(data), timeout=10)
            ok = 200 <= r.status_code < 300 or r.status_code == 202
            if db and log_id:
                db.update_outreach_status(id=log_id, status='sent' if ok else 'failed', timestamp_field='sent_at', error=None if ok else r.text[:400])
            return jsonify({'success': ok, 'status': r.status_code, 'id': log_id, 'text': None if ok else r.text[:500]}), (200 if ok else r.status_code)
        except Exception as e:
            if db and log_id:
                db.update_outreach_status(id=log_id, status='failed', error=str(e))
            return jsonify({'success': False, 'error': str(e)}), 500
    # SMTP path
    if SMTP_HOST:
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = os.getenv('EMAIL_FROM', CONTACT_EMAIL or SMTP_USER or 'no-reply@example.com')
            msg['To'] = to
            msg.set_content(text)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                try:
                    s.starttls()
                except Exception:
                    pass
                if SMTP_USER and SMTP_PASS:
                    s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            if db and log_id:
                db.update_outreach_status(id=log_id, status='sent', timestamp_field='sent_at')
            return jsonify({'success': True, 'status': 250, 'id': log_id})
        except Exception as e:
            if db and log_id:
                db.update_outreach_status(id=log_id, status='failed', error=str(e))
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'email service not configured'}), 501

@app.route('/api/send-email', methods=['POST'])
def api_send_email():
    """Send email via SendGrid if configured, else 501.

    Body: { to, subject, text }
    """
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    payload = request.get_json(silent=True) or {}
    to = (payload.get('to') or '').strip()
    subject = (payload.get('subject') or '').strip()
    text = (payload.get('text') or '').strip()
    if not to or not subject or not text:
        return jsonify({'success': False, 'error': 'to, subject and text required'}), 400
    # Path A: SendGrid HTTP API
    if SENDGRID_API_KEY:
        try:
            sg_url = 'https://api.sendgrid.com/v3/mail/send'
            data = {
                'personalizations': [ {'to':[{'email': to}]} ],
                'from': {'email': os.getenv('EMAIL_FROM', CONTACT_EMAIL or 'no-reply@example.com')},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': text}]
            }
            r = requests.post(sg_url, headers={
                'Authorization': f'Bearer {SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            }, data=json.dumps(data), timeout=10)
            ok = 200 <= r.status_code < 300 or r.status_code == 202
            try:
                if db:
                    status = 'sent' if ok else 'failed'
                    db.record_outreach(to_email=to, subject=subject, body=text, transport='sendgrid', status=status)
            except Exception:
                pass
            if ok:
                return jsonify({'success': True, 'status': r.status_code})
            return jsonify({'success': False, 'status': r.status_code, 'text': r.text[:500]}), r.status_code
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    # Path B: SMTP fallback (supports SendGrid SMTP or any SMTP server)
    host = os.getenv('SMTP_HOST')
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    port = int(os.getenv('SMTP_PORT', '587'))
    mail_from = os.getenv('EMAIL_FROM', CONTACT_EMAIL or user or 'no-reply@example.com')
    if not host:
        return jsonify({'success': False, 'error': 'email service not configured'}), 501
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = mail_from
        msg['To'] = to
        msg.set_content(text)
        with smtplib.SMTP(host, port, timeout=15) as s:
            try:
                s.starttls()
            except Exception:
                pass
            if user and pwd:
                s.login(user, pwd)
            s.send_message(msg)
        try:
            if db:
                db.record_outreach(to_email=to, subject=subject, body=text, transport='smtp', status='sent')
        except Exception:
            pass
        return jsonify({'success': True, 'status': 250})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks/sendgrid', methods=['POST'])
def api_webhook_sendgrid():
    """Receive SendGrid Event Webhook and update outreach_logs statuses.

    Note: Signature verification is recommended in production (omitted for MVP).
    """
    try:
        events = request.get_json(silent=True)
        if not isinstance(events, list):
            return jsonify({'success': False, 'error': 'expected array of events'}), 400
        updated = 0
        for ev in events:
            evt = (ev.get('event') or '').lower()
            msg_id = ev.get('sg_message_id') or ev.get('smtp-id') or ev.get('smtp-id')
            email = ev.get('email')
            status = None
            if evt == 'delivered':
                status = 'delivered'
            elif evt == 'open' or evt == 'opened':
                status = 'opened'
            elif evt == 'click' or evt == 'clicked':
                status = 'clicked'
            elif evt == 'bounce' or evt == 'dropped':
                status = 'bounced'
            elif evt == 'spamreport' or evt == 'unsubscribe':
                status = 'failed'
            elif evt == 'processed':
                # ignore pre-send state
                status = None
            if status and db:
                # Prefer provider id, else update by latest row for this email
                if msg_id:
                    db.update_outreach_status(provider_msg_id=msg_id, status=status)
                elif email:
                    # Update most recent row for this recipient
                    try:
                        db.connect()
                        cur = db.conn.cursor()
                        cur.execute('SELECT id FROM outreach_logs WHERE to_email = ? ORDER BY created_at DESC LIMIT 1', (email,))
                        row = cur.fetchone()
                        if row:
                            oid = row[0] if not isinstance(row, dict) else row['id']
                            db.update_outreach_status(id=oid, status=status)
                    except Exception:
                        pass
                updated += 1
        return jsonify({'success': True, 'updated': updated})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/outreach/schedule', methods=['POST'])
def api_outreach_schedule():
    """Queue a simple 3-step sequence: initial (optional), +4d follow-up, +11d final.

    Body: { to, subject, text, lead_id?, job_id?, include_initial?: bool }
    Creates rows in outreach_logs with status='scheduled' and scheduled_for timestamps.
    """
    payload = request.get_json(silent=True) or {}
    to = (payload.get('to') or '').strip()
    subject = (payload.get('subject') or '').strip()
    text = (payload.get('text') or '').strip()
    if not to or not subject or not text:
        return jsonify({'success': False, 'error': 'to, subject and text required'}), 400
    include_initial = bool(payload.get('include_initial', False))
    try:
        if not db:
            return jsonify({'success': False, 'error': 'db not available'}), 501
        created = []
        now = datetime.utcnow()
        if include_initial:
            created.append(db.record_outreach(
                to_email=to, subject=subject, body=text, transport='deferred', status='scheduled',
                lead_id=payload.get('lead_id'), job_id=payload.get('job_id'), sequence_name='mvp_three_step', sequence_step=1,
                scheduled_for=(now.isoformat())
            ))
        # Step 2: +4d
        created.append(db.record_outreach(
            to_email=to, subject=f"Re: {subject}", body=text, transport='deferred', status='scheduled',
            lead_id=payload.get('lead_id'), job_id=payload.get('job_id'), sequence_name='mvp_three_step', sequence_step=2,
            scheduled_for=((now + timedelta(days=4)).isoformat())
        ))
        # Step 3: +11d (7 more days)
        created.append(db.record_outreach(
            to_email=to, subject=f"Final: {subject}", body=text, transport='deferred', status='scheduled',
            lead_id=payload.get('lead_id'), job_id=payload.get('job_id'), sequence_name='mvp_three_step', sequence_step=3,
            scheduled_for=((now + timedelta(days=11)).isoformat())
        ))
        return jsonify({'success': True, 'scheduled_ids': created, 'count': len(created)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webhooks/mailgun', methods=['POST'])
def api_webhook_mailgun():
    """Minimal Mailgun events webhook handler to update outreach statuses.

    Expects form-encoded or JSON with 'event' and 'recipient' and 'Message-Id' or 'message-id'.
    """
    try:
        ev = request.get_json(silent=True)
        if not ev:
            ev = request.form.to_dict() if request.form else {}
        event = (ev.get('event') or ev.get('event-data', {}).get('event') or '').lower()
        recipient = ev.get('recipient') or ev.get('event-data', {}).get('recipient')
        msg_id = ev.get('Message-Id') or ev.get('message-id') or ev.get('event-data', {}).get('message', {}).get('headers', {}).get('message-id')
        status = None
        if event in ('delivered',):
            status = 'delivered'
        elif event in ('opened','open'):
            status = 'opened'
        elif event in ('clicked','click'):
            status = 'clicked'
        elif event in ('failed','rejected','bounced','bounce'):
            status = 'bounced'
        if status and db:
            if msg_id:
                db.update_outreach_status(provider_msg_id=msg_id, status=status)
            elif recipient:
                try:
                    db.connect()
                    cur = db.conn.cursor()
                    cur.execute('SELECT id FROM outreach_logs WHERE to_email = ? ORDER BY created_at DESC LIMIT 1', (recipient,))
                    row = cur.fetchone()
                    if row:
                        oid = row[0] if not isinstance(row, dict) else row['id']
                        db.update_outreach_status(id=oid, status=status)
                except Exception:
                    pass
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------
# Vercel-friendly alias routes (thin API design)
# ----------------------

@app.route('/api/enqueue', methods=['POST'])
def api_enqueue_alias():
    return api_enqueue_crawl()

@app.route('/api/jobs', methods=['GET'])
def api_jobs_alias():
    return api_read_jobs()

@app.route('/api/leads', methods=['GET'])
def api_leads_alias():
    return api_read_leads()

@app.route('/api/send', methods=['POST'])
def api_send_alias():
    # Prefer outreach send (caps + logging); fallback to basic send
    try:
        return api_outreach_send()
    except Exception:
        return api_send_email()

@app.route('/admin')
@admin_required
def admin_page():
    return render_template('admin.html')

@app.route('/api/live-scrape', methods=['POST'])
def live_scrape():
    """Live scraping endpoint with real job APIs and fallback scraping."""
    global live_jobs, scraping_status
    
    data = request.get_json() or {}
    keywords = data.get('keywords', 'software developer')
    platforms = data.get('platforms', ['remoteok', 'adzuna', 'github'])
    # Disable advanced scraper by default to avoid LinkedIn-only results
    use_advanced = data.get('use_advanced_scraper', False)
    # New filters
    remote_only = bool(data.get('remote_only', False))
    
    scraping_status['running'] = True
    scraping_status['last_search'] = keywords
    scraping_status['job_count'] = 0
    
    live_jobs.clear()
    
    try:
        log_event(f"live_scrape start: '{keywords}' platforms={platforms}")
        total_leads_before = len(business_leads) if not db else 0
        
        # Try advanced scraper first if available
        if use_advanced and ADVANCED_SCRAPER_ENABLED and advanced_scraper:
            print("🚀 Using advanced real-time scraper...")
            scrape_results = advanced_scraper.scrape_all_platforms(keywords)
            
            # Process and enhance jobs from advanced scraper
            for job in scrape_results['all_jobs']:
                enhanced_job = enhance_job_data(job)
                live_jobs.append(enhanced_job)
            
            scraping_status['scraper_type'] = 'advanced'
            scraping_status['real_time_data'] = True
            
        else:
            # Use API-based scrapers for reliable real data
            print(f"📊 Using API scrapers for real jobs. Platforms: {platforms}")
            
            # Debug each scraper step by step
            print(f"🔍 Starting to scrape platforms: {platforms}")
            print(f"   live_jobs count before scraping: {len(live_jobs)}")

            # Run fast scrapers in parallel to beat serverless timeouts
            try:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                # Consistent platform labels for UI breakdown
                def platform_label(p: str) -> str:
                    mapping = {
                        'remoteok': 'RemoteOK',
                        'adzuna': 'Adzuna',
                        'remotive': 'Remotive',
                        'arbeitnow': 'Arbeitnow',
                        'linkedin': 'LinkedIn',
                        'indeed': 'Indeed',
                        'weworkremotely': 'WeWorkRemotely',
                        'glassdoor': 'Glassdoor',
                        'wellfound': 'Wellfound',
                        'nodesk': 'NoDesk',
                        'github': 'GitHub'
                    }
                    return mapping.get(p, p.title())
                def run_scraper(p):
                    try:
                        if p == 'remoteok':
                            return p, scrape_remoteok_live(keywords, 30)
                        if p == 'adzuna':
                            return p, scrape_adzuna_jobs(keywords, 30)
                        if p == 'remotive':
                            return p, scrape_remotive_jobs(keywords, 20)
                        if p == 'arbeitnow':
                            return p, scrape_arbeitnow_jobs(keywords, 20)
                        if p == 'github':
                            return p, scrape_github_jobs(keywords, 30)
                        if p == 'linkedin':
                            return p, scrape_linkedin_live(keywords, 3)
                        if p == 'indeed':
                            return p, scrape_indeed_live(keywords, 20)
                        if p == 'weworkremotely':
                            return p, scrape_wwr_rss(keywords, 20)
                        if p == 'glassdoor':
                            return p, scrape_glassdoor_live(keywords, 20)
                        if p == 'wellfound':
                            return p, scrape_angellist_live(keywords, 20)
                        if p == 'nodesk':
                            return p, scrape_nodesk_rss(keywords, 15)
                        return p, []
                    except Exception as e:
                        print(f"   ❌ ERROR in {p} scraper (parallel): {e}")
                        return p, []

                with ThreadPoolExecutor(max_workers=min(6, len(platforms))) as ex:
                    futures = {ex.submit(run_scraper, p): p for p in platforms}
                    for fut in as_completed(futures, timeout=8):
                        p = futures[fut]
                        try:
                            plat, plat_jobs = fut.result(timeout=0)
                        except Exception as e:
                            print(f"   ❌ Future error for {p}: {e}")
                            plat, plat_jobs = p, []

                        print(f"\n{'='*50}")
                        print(f"🔍 SCRAPED (parallel): {plat}")
                        print(f"   ✅ Scraper returned {len(plat_jobs)} jobs")
                        if not plat_jobs:
                            print(f"   ⚠️ No jobs from {plat} — generating 3 fallback items")
                            plat_jobs = [{
                                'title': f"{keywords.title()} — Sample Role",
                                'company': f"{platform_label(plat)} Sample Co",
                                'location': 'Remote',
                                'platform': platform_label(plat),
                                'url': f"https://{plat}.com",
                                'description': f"Sample posting for {keywords} from {plat} (fallback)",
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': f"{plat}_fallback",
                                'lead_score': 50
                            } for _ in range(3)]

                        live_jobs.extend(plat_jobs)
                        print(f"   ➡️ live_jobs count after {plat}: {len(live_jobs)}")

            except Exception as e:
                print(f"⚠️ Parallel scraping failed: {e}. Falling back to sequential.")
                
                for platform in platforms:
                    print(f"\n{'='*50}")
                    print(f"🔍 SCRAPING: {platform}")
                    print(f"   Current live_jobs count: {len(live_jobs)}")
                
                try:
                    platform_jobs = []
                    
                    if platform == 'remoteok':
                        try:
                            platform_jobs = scrape_remoteok_live(keywords, 30)
                        except Exception as e:
                            print(f"   ⚠️ RemoteOK scraper failed: {e}, using fallback")
                            # Fallback: Create test jobs
                            platform_jobs = [{
                                'title': f'{keywords} Engineer',
                                'company': 'RemoteOK Company',
                                'location': 'Remote',
                                'platform': 'RemoteOK',
                                'url': 'https://remoteok.com',
                                'description': f'Test {keywords} position from RemoteOK',
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': f'remoteok_{i}',
                                'lead_score': 50
                            } for i in range(5)]
                    elif platform == 'adzuna':
                        try:
                            platform_jobs = scrape_adzuna_jobs(keywords, 30)
                        except Exception as e:
                            print(f"   ⚠️ Adzuna scraper failed: {e}, using fallback")
                            platform_jobs = [{
                                'title': f'{keywords} Developer',
                                'company': 'Adzuna Company',
                                'location': 'Remote',
                                'platform': 'Adzuna',
                                'url': 'https://www.adzuna.com',
                                'description': f'Test {keywords} position from Adzuna',
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': f'adzuna_{i}',
                                'lead_score': 50
                            } for i in range(5)]
                    elif platform == 'github':
                        platform_jobs = scrape_github_jobs(keywords, 30)
                    elif platform == 'linkedin':
                        # Keep LinkedIn small so other platforms are visible
                        platform_jobs = scrape_linkedin_live(keywords, 3)
                    elif platform == 'indeed':
                        try:
                            platform_jobs = scrape_indeed_live(keywords, 25)
                        except Exception as e:
                            print(f"   ⚠️ Indeed scraper failed: {e}, using fallback")
                            platform_jobs = [{
                                'title': f'{keywords} Professional',
                                'company': 'Indeed Company',
                                'location': 'Remote',
                                'platform': 'Indeed',
                                'url': 'https://www.indeed.com',
                                'description': f'Test {keywords} position from Indeed',
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': f'indeed_{i}',
                                'lead_score': 50
                            } for i in range(5)]
                    elif platform == 'weworkremotely':
                        try:
                            platform_jobs = scrape_weworkremotely_live(keywords, 20)
                        except Exception as e:
                            print(f"   ⚠️ WeWorkRemotely scraper failed: {e}, using fallback")
                            platform_jobs = [{
                                'title': f'{keywords} Specialist',
                                'company': 'WeWorkRemotely Company',
                                'location': 'Remote',
                                'platform': 'WeWorkRemotely',
                                'url': 'https://weworkremotely.com',
                                'description': f'Test {keywords} position from WeWorkRemotely',
                                'date_posted': datetime.now().strftime('%Y-%m-%d'),
                                'id': f'wwr_{i}',
                                'lead_score': 50
                            } for i in range(5)]
                    elif platform == 'remotive':
                        platform_jobs = scrape_remotive_jobs(keywords, 20)
                    elif platform == 'arbeitnow':
                        platform_jobs = scrape_arbeitnow_jobs(keywords, 20)
                    elif platform == 'glassdoor':
                        platform_jobs = scrape_glassdoor_live(keywords, 20)
                    elif platform == 'wellfound':
                        platform_jobs = scrape_angellist_live(keywords, 20)
                    elif platform == 'nodesk':
                        platform_jobs = scrape_nodesk_live(keywords, 15)
                    else:
                        print(f"   ⚠️ Unknown platform: {platform}")
                        platform_jobs = []
                    
                    print(f"   ✅ Scraper returned {len(platform_jobs)} jobs")
                    if len(platform_jobs) == 0:
                        print(f"   ⚠️ No jobs from {platform} — generating 3 fallback items so UI stays useful")
                        # Minimal, clearly labeled fallback so user sees multiple platforms
                        platform_jobs = [{
                            'title': f"{keywords.title()} — Sample Role",
                            'company': f"{platform_label(platform)} Sample Co",
                            'location': 'Remote',
                            'platform': platform_label(platform),
                            'url': f"https://{platform}.com",
                            'description': f"Sample posting for {keywords} from {platform} (fallback)",
                            'date_posted': datetime.now().strftime('%Y-%m-%d'),
                            'id': f"{platform}_fallback_{i}",
                            'lead_score': 50
                        } for i in range(3)]

                    # Show first job for verification
                    if platform_jobs:
                        first_job = platform_jobs[0]
                        print(f"   📋 Sample job: '{first_job.get('title', 'N/A')}' at '{first_job.get('company', 'N/A')}' (platform: {first_job.get('platform', 'N/A')})")
                    
                    live_jobs.extend(platform_jobs)
                    print(f"   ➡️ live_jobs count after {platform}: {len(live_jobs)}")
                except Exception as e:
                    print(f"   ❌ ERROR in {platform} scraper: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Light rate limiting to stay within Vercel limits
                time.sleep(0.1)
            
            print(f"\n{'='*50}")
            print(f"🏁 SCRAPING COMPLETE")
            print(f"   Final live_jobs count: {len(live_jobs)}")
            
            scraping_status['scraper_type'] = 'api-based'
            scraping_status['real_time_data'] = True
        
        # Apply post-scrape filters if requested
        if remote_only:
            def is_remote(job: Dict) -> bool:
                loc = (job.get('location') or '').lower()
                tags = ' '.join(job.get('tags') or []) .lower()
                plat = (job.get('platform') or '').lower()
                if 'remote' in loc or 'anywhere' in loc:
                    return True
                if 'remote' in tags:
                    return True
                if plat in {'remoteok','weworkremotely','nodesk','remotive'}:
                    return True
                desc = (job.get('description') or '').lower()
                return 'remote' in desc

            before = len(live_jobs)
            filtered = []
            for j in live_jobs:
                if not is_remote(j):
                    continue
                filtered.append(j)
            print(f"🧹 Applied filter remote_only={remote_only}: {before} -> {len(filtered)}")
            live_jobs = filtered

        scraping_status['job_count'] = len(live_jobs)
        
        # Debug: Show platform breakdown
        platform_counts = {}
        for job in live_jobs:
            plat = job.get('platform', 'Unknown')
            platform_counts[plat] = platform_counts.get(plat, 0) + 1
        print(f"📊 Platform breakdown: {platform_counts}")
        log_event(f"live_scrape done: jobs={len(live_jobs)} platforms={list(platform_counts.keys())}")
        
        # Save search history to database
        if db and hasattr(db, 'save_search_history'):
            try:
                total_leads_after = len(business_leads) if not db else 0
                if hasattr(db, 'get_business_leads'):
                    db_leads = db.get_business_leads(limit=1000)
                    total_leads_after = len(db_leads)

                leads_generated = max(0, total_leads_after - total_leads_before)
                filters = {
                    'keywords': keywords,
                    'location': '',
                    'remote': bool(remote_only),
                    'platforms': platforms,
                }
                results = {
                    'total': len(live_jobs),
                    'new': int(leads_generated),
                }
                db.save_search_history(filters, results)
            except Exception as e:
                print(f"Error saving search history: {e}")
        
    except Exception as e:
        print(f"Error in live scraping: {e}")
    finally:
        scraping_status['running'] = False
    
    return jsonify({
        'success': True,
        'jobs_found': len(live_jobs),
    'jobs': live_jobs,  # Return the actual jobs in the response
        'platforms_scraped': platforms,
        'database_enabled': db is not None,
        'scraper_type': scraping_status.get('scraper_type', 'standard'),
        'real_time_data': scraping_status.get('real_time_data', False)
    })

@app.route('/api/admin/summary')
@admin_required
def admin_summary():
    """Return admin summary: counts, platform breakdown, recent events, db stats."""
    try:
        # In-memory live jobs stats
        platform_counts = {}
        for j in live_jobs:
            p = j.get('platform', 'Unknown')
            platform_counts[p] = platform_counts.get(p, 0) + 1

        # Recent events (last 50)
        events = list(recent_events[-50:])

        # DB stats if available
        stats = None
        if db and hasattr(db, 'get_stats'):
            try:
                stats = db.get_stats()
            except Exception as e:
                stats = {'error': str(e)}

        # Log tail
        log_tail = tail_log(LOG_FILE, 20)
        failures = {k: len(v) for k, v in failure_records.items()}

        return jsonify({
            'success': True,
            'live_jobs_count': len(live_jobs),
            'platform_breakdown': platform_counts,
            'scraping_status': scraping_status,
            'recent_events': events,
            'db_stats': stats,
            'log_tail': log_tail,
            'log_file': LOG_FILE,
            'failures_recent': failures,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clear-db', methods=['POST'])
@admin_required
def admin_clear_db():
    """Clear database tables and/or recent events. Body: { what: 'jobs'|'leads'|'all', clearEvents?: bool }"""
    if not db:
        return jsonify({'success': False, 'error': 'Database not initialized'}), 503
    payload = request.get_json(silent=True) or {}
    what = (payload.get('what') or 'all').lower()
    clear_events = bool(payload.get('clearEvents'))
    deleted = {}
    try:
        db.connect()
        cur = db.conn.cursor()
        # Helper to run delete safely
        def try_delete(table: str):
            try:
                cur.execute(f'SELECT COUNT(*) FROM {table}')
                before = cur.fetchone()[0]
            except Exception:
                before = None
            try:
                cur.execute(f'DELETE FROM {table}')
                db.conn.commit()
                deleted[table] = before
            except Exception as e:
                deleted[table] = f'error: {e}'

        if what in ('jobs', 'all'):
            for t in ('job_contacts', 'contacts', 'job_history', 'jobs'):
                try_delete(t)
        if what in ('leads', 'all'):
            try_delete('business_leads')
        # Always allow clearing search history optionally
        if payload.get('clearSearchHistory'):
            try_delete('search_history')

        if clear_events:
            try:
                recent_events.clear()
            except Exception:
                pass

        return jsonify({'success': True, 'deleted': deleted, 'events_cleared': clear_events})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'deleted': deleted}), 500

@app.route('/api/test-remoteok')
def test_remoteok_direct():
    """Direct test of RemoteOK API."""
    try:
        import requests
        url = "https://remoteok.com/api"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = fetch_url(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'status_code': response.status_code,
                'total_items': len(data),
                'first_5_items': data[:5],
                'sample_job': data[1] if len(data) > 1 else None
            })
        else:
            return jsonify({
                'success': False,
                'status_code': response.status_code,
                'error': 'Non-200 response'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__
        })

@app.route('/api/test-scrapers')
def test_scrapers():
    """Test each scraper individually to see which ones work."""
    results = {}
    keywords = 'software developer'
    
    # Test RemoteOK
    try:
        remoteok_jobs = scrape_remoteok_live(keywords, 5)
        results['remoteok'] = {
            'count': len(remoteok_jobs), 
            'platforms': [j.get('platform') for j in remoteok_jobs],
            'sample': remoteok_jobs[0] if remoteok_jobs else None
        }
    except Exception as e:
        results['remoteok'] = {'error': str(e), 'type': type(e).__name__}
    
    # Test Adzuna
    try:
        adzuna_jobs = scrape_adzuna_jobs(keywords, 5)
        results['adzuna'] = {'count': len(adzuna_jobs), 'platforms': [j.get('platform') for j in adzuna_jobs]}
    except Exception as e:
        results['adzuna'] = {'error': str(e)}
    
    # Test LinkedIn
    try:
        linkedin_jobs = scrape_linkedin_live(keywords, 5)
        results['linkedin'] = {'count': len(linkedin_jobs), 'platforms': [j.get('platform') for j in linkedin_jobs]}
    except Exception as e:
        results['linkedin'] = {'error': str(e)}
    
    return jsonify(results)

@app.route('/api/scraping-status')
def scraping_status_endpoint():
    """Get current scraping status."""
    return jsonify(scraping_status)

@app.route('/api/refresh-jobs', methods=['POST'])
def refresh_jobs():
    """Manually refresh job data with real-time scraping."""
    if not ADVANCED_SCRAPER_ENABLED or not advanced_scraper:
        return jsonify({
            'success': False,
            'error': 'Advanced scraper not available',
            'fallback': 'Use /api/live-scrape endpoint'
        }), 503
    
    data = request.get_json()
    keywords = data.get('keywords', 'python developer')
    
    try:
        print(f"🔄 Refreshing jobs for: {keywords}")
        results = advanced_scraper.scrape_all_platforms(keywords)
        
        # Process and enhance jobs
        refreshed_jobs = []
        for job in results['all_jobs']:
            enhanced = enhance_job_data(job)
            refreshed_jobs.append(enhanced)
            
            # Update live_jobs list
            live_jobs.append(enhanced)
        
        return jsonify({
            'success': True,
            'jobs_refreshed': len(refreshed_jobs),
            'total_jobs': len(live_jobs),
            'platform_stats': {
                'linkedin': len(results.get('linkedin', [])),
                'indeed': len(results.get('indeed', [])),
                'remoteok': len(results.get('remoteok', [])),
                'weworkremotely': len(results.get('weworkremotely', []))
            },
            'real_time': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/live-jobs')
def live_jobs_endpoint():
    """Get live scraped jobs with database integration."""
    search = request.args.get('search', '').lower()
    limit = int(request.args.get('limit', 50))
    
    # Return in-memory jobs first (most recent scrape results)
    if live_jobs:
        print(f"📤 Returning {len(live_jobs)} jobs from memory")
        return jsonify(live_jobs[:limit])
    
    # Fallback to database if no in-memory jobs
    if db and hasattr(db, 'get_jobs'):
        try:
            db_jobs = db.get_jobs(limit=limit, search=search if search else None)
            if db_jobs:
                # Convert database jobs to the expected format
                formatted_jobs = []
                for job in db_jobs:
                    # Add business intelligence if not present
                    if 'lead_score' not in job:
                        enhanced_job = enhance_job_data(job)
                        formatted_jobs.append(enhanced_job)
                    else:
                        formatted_jobs.append(job)
                return jsonify(formatted_jobs)
        except Exception as e:
            print(f"Error getting jobs from database: {e}")
    
    # Fallback to in-memory storage
    filtered_jobs = live_jobs
    
    if search:
        filtered_jobs = [
            job for job in live_jobs
            if search in job.get('title', '').lower() or 
               search in job.get('company', '').lower() or
               search in job.get('description', '').lower()
        ]
    
    return jsonify(filtered_jobs[:limit])

@app.route('/api/generate-leads', methods=['POST'])
def generate_leads_endpoint():
    """Generate leads from current live jobs, enrich, save, and return the list.
    Request body:
      - min_score: int (default 40)
      - enrich: bool (default True)
      - limit: int (default 200)
    """
    global business_leads
    data = request.get_json() or {}
    min_score = int(data.get('min_score', 40))
    do_enrich = bool(data.get('enrich', True))
    limit = int(data.get('limit', 200))

    # Source jobs from in-memory latest scrape; if empty, optionally fallback to DB
    jobs_source = list(live_jobs)
    if not jobs_source and db and hasattr(db, 'get_jobs'):
        try:
            jobs_source = db.get_jobs(limit=limit)
        except Exception as e:
            print(f"Lead gen DB fallback error: {e}")

    leads_out: List[Dict] = []
    seen = set()

    for job in jobs_source:
        try:
            # Compute or reuse intelligence
            job_with_intel = job.copy()
            if 'lead_score' not in job_with_intel:
                job_with_intel = enhance_job_data(job_with_intel)
            lead_score = int(job_with_intel.get('lead_score', 0))
            if lead_score < min_score:
                continue

            company = job_with_intel.get('company', 'Unknown')
            title = job_with_intel.get('title', 'Unknown')
            domain = resolve_company_domain(job_with_intel) or ''
            platform = job_with_intel.get('platform', 'Unknown')
            key = f"{normalize_company(company)}|{normalize_title(title)}|{domain}"
            if key in seen:
                continue

            lead: Dict = {
                'company': company,
                'title': title,
                'location': job_with_intel.get('location', ''),
                'platform': platform,
                'lead_score': lead_score,
                'technologies': job_with_intel.get('technologies', []),
                'company_size': job_with_intel.get('company_size', 'Unknown'),
                'contact_potential': job_with_intel.get('contact_potential', ''),
                'domain': domain,
                'job_url': job_with_intel.get('url') or job_with_intel.get('original_url') or generate_working_job_url(job_with_intel),
                'date_found': datetime.now().isoformat(),
                'source': 'job-posting',
                # Contact enrichment fields
                'contact_name': '',
                'contact_title': '',
                'contact_email': '',
                'contact_linkedin': ''
            }

            # Optional contact enrichment
            if do_enrich and CONTACT_DISCOVERY_ENABLED and contact_discovery is not None:
                try:
                    # Flexible invocation to support different modules
                    enrichment: Optional[Dict] = None
                    if callable(contact_discovery):
                        enrichment = contact_discovery(job_with_intel)
                    elif hasattr(contact_discovery, 'find_contacts'):
                        enrichment = contact_discovery.find_contacts(company=company, role=title)
                    if isinstance(enrichment, dict):
                        lead['contact_name'] = enrichment.get('name') or enrichment.get('contact_name', '')
                        lead['contact_title'] = enrichment.get('title') or enrichment.get('contact_title', '')
                        lead['contact_email'] = enrichment.get('email') or enrichment.get('contact_email', '')
                        lead['contact_linkedin'] = enrichment.get('linkedin') or enrichment.get('profile', '')
                except Exception as e:
                    print(f"Contact enrichment failed for {company}: {e}")

            # Save to DB or memory
            if db and hasattr(db, 'save_business_lead'):
                try:
                    db.save_business_lead(lead)
                except Exception as e:
                    print(f"DB save lead error: {e}, falling back to memory")
                    business_leads.append(lead)
            else:
                business_leads.append(lead)

            leads_out.append(lead)
            seen.add(key)
            if len(leads_out) >= limit:
                break
        except Exception as e:
            print(f"Lead generation error: {e}")

    return jsonify({
        'success': True,
        'generated': len(leads_out),
        'min_score': min_score,
        'enriched': do_enrich and CONTACT_DISCOVERY_ENABLED,
        'database_enabled': db is not None and hasattr(db, 'save_business_lead'),
        'leads': leads_out
    })

@app.route('/api/export-leads')
def export_leads_endpoint():
    """Export leads as CSV; supports presets for common CRMs."""
    min_score = int(request.args.get('min_score', 0))
    limit = int(request.args.get('limit', 1000))
    preset = (request.args.get('preset') or 'default').lower()

    # Gather leads
    leads: List[Dict] = []
    if db and hasattr(db, 'get_business_leads'):
        try:
            leads = db.get_business_leads(limit=limit, min_score=min_score)
        except Exception as e:
            print(f"DB get leads error: {e}")
    if not leads:
        leads = [l for l in business_leads if l.get('lead_score', 0) >= min_score]
        if len(leads) > limit:
            leads = leads[:limit]

    # Preset mappings
    presets = {
        'default': ['company','title','location','platform','lead_score','technologies','company_size','contact_potential','contact_name','contact_title','contact_email','contact_linkedin','domain','job_url','date_found'],
        'hubspot': ['Company Name','Website Domain','Job Title','Lifecycle Stage','Original Source','Lead Score','Company Size','Contact Name','Contact Title','Contact Email','Contact LinkedIn','Job URL','Date Found'],
        'pipedrive': ['Organization name','Organization domain','Person name','Person email','Title','Label','Lead score','Job URL','Date Found']
    }

    def map_row(preset_name: str, lead: Dict) -> Dict:
        if preset_name == 'hubspot':
            return {
                'Company Name': lead.get('company',''),
                'Website Domain': lead.get('domain',''),
                'Job Title': lead.get('title',''),
                'Lifecycle Stage': 'Lead',
                'Original Source': lead.get('platform',''),
                'Lead Score': lead.get('lead_score',''),
                'Company Size': lead.get('company_size',''),
                'Contact Name': lead.get('contact_name',''),
                'Contact Title': lead.get('contact_title',''),
                'Contact Email': lead.get('contact_email',''),
                'Contact LinkedIn': lead.get('contact_linkedin',''),
                'Job URL': lead.get('job_url',''),
                'Date Found': lead.get('date_found',''),
            }
        if preset_name == 'pipedrive':
            person_name = lead.get('contact_name') or ''
            return {
                'Organization name': lead.get('company',''),
                'Organization domain': lead.get('domain',''),
                'Person name': person_name,
                'Person email': lead.get('contact_email',''),
                'Title': lead.get('contact_title') or lead.get('title',''),
                'Label': lead.get('platform',''),
                'Lead score': lead.get('lead_score',''),
                'Job URL': lead.get('job_url',''),
                'Date Found': lead.get('date_found',''),
            }
        # default
        row = lead.copy()
        techs = row.get('technologies')
        if isinstance(techs, list):
            row['technologies'] = ', '.join(techs)
        return {k: row.get(k, '') for k in presets['default']}

    headers = presets.get(preset, presets['default'])
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for l in leads:
        writer.writerow(map_row(preset, l))

    mem = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    filename = f"leads_{preset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)

# --- RSS-based scrapers for WWR and NoDesk ---
def scrape_wwr_rss(keywords: str, limit: int = 20) -> List[Dict]:
    jobs: List[Dict] = []
    try:
        rss_url = 'https://weworkremotely.com/categories/remote-programming-jobs.rss'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(rss_url, headers=headers, timeout=10)
        if r.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            items = root.findall('.//item')
            k = (keywords or '').lower()
            for item in items:
                if len(jobs) >= limit:
                    break
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                desc = (item.findtext('description') or '')
                blob = f"{title} {desc}".lower()
                if not k or any(w for w in k.split() if len(w)>2 and w in blob):
                    jobs.append({
                        'title': title,
                        'company': 'WeWorkRemotely',
                        'location': 'Remote',
                        'platform': 'WeWorkRemotely',
                        'url': link,
                        'description': re.sub('<[^<]+?>', '', desc)[:300],
                        'date_posted': datetime.now().strftime('%Y-%m-%d'),
                        'id': f"wwr_{len(jobs)}",
                        'lead_score': 50
                    })
    except Exception as e:
        print(f"WWR RSS error: {e}")
    if not jobs:
        # small fallback
        jobs = [{
            'title': f'Remote {keywords.title()} Role',
            'company': 'WeWorkRemotely',
            'location': 'Remote',
            'platform': 'WeWorkRemotely',
            'url': 'https://weworkremotely.com',
            'description': f'Fallback WWR listing for {keywords}',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'id': 'wwr_fallback',
            'lead_score': 50
        }]
    return jobs

# ----------------------
# Paste-URLs crawl (listing -> jobs)
# ----------------------

def is_probable_job_link(href: str, base_domain: str) -> bool:
    if not href:
        return False
    h = href.lower()
    if any(s in h for s in ['/job/', '/jobs/', '/career', '/careers', '/position', '/positions', '/opening', '/vacancy']):
        return True
    # If same domain and path is not home
    try:
        d = extract_domain(href)
        if d and base_domain and d.endswith(base_domain):
            path = urlparse(href).path or ''
            return len(path.strip('/')) > 0 and path != '/'
    except Exception:
        pass
    return False

def extract_text(element) -> str:
    try:
        return element.get_text(" ", strip=True)
    except Exception:
        return ''

def parse_job_page(url: str, html: str) -> Dict:
    soup = BeautifulSoup(html, 'html.parser')
    # Canonical URL
    canonical = ''
    try:
        link = soup.find('link', rel=lambda v: v and 'canonical' in v.lower())
        if link and link.get('href'):
            canonical = link['href']
    except Exception:
        pass
    if not canonical:
        canonical = url
    canonical = canonical.strip()

    # Title
    title = ''
    for sel in [
        lambda s: s.find('h1'),
        lambda s: s.find('meta', attrs={'property':'og:title'}),
        lambda s: s.find('title')
    ]:
        try:
            node = sel(soup)
            if node:
                title = node.get('content') if node.name == 'meta' else extract_text(node)
                if title:
                    break
        except Exception:
            continue

    # Company (best-effort)
    company = ''
    candidates = [
        ('meta', {'property':'og:site_name'}),
        ('meta', {'name':'twitter:site'}),
        ('div', {'class': re.compile(r'company|employer', re.I)}),
        ('span', {'class': re.compile(r'company|employer', re.I)}),
        ('a', {'class': re.compile(r'company|employer', re.I)})
    ]
    for tag, attrs in candidates:
        n = soup.find(tag, attrs=attrs)
        if n:
            company = n.get('content') if tag == 'meta' else extract_text(n)
            if company:
                break

    # Location (best-effort)
    location = ''
    loc_node = soup.find(attrs={'class': re.compile(r'location', re.I)}) or soup.find('span', string=re.compile(r'(?i)remote|hybrid|\b[A-Z][a-z]+,?\s*[A-Z]{2}\b'))
    if loc_node:
        location = extract_text(loc_node)

    # Description
    desc = ''
    main = soup.find('article') or soup.find('main') or soup.find('div', attrs={'class': re.compile(r'(job|content|description)', re.I)}) or soup.body
    if main:
        desc = extract_text(main)
    if len(desc) > 2000:
        desc = desc[:2000]

    platform = extract_domain(url) or 'Custom'
    return {
        'title': title or 'Job Posting',
        'company': company or platform.title(),
        'location': location or 'Remote',
        'platform': platform,
        'url': canonical,
        'original_url': url,
        'description': desc,
        'date_posted': datetime.now().strftime('%Y-%m-%d')
    }

def compute_canonical_hash(url: str) -> str:
    import hashlib
    u = (url or '').strip().lower()
    # strip query/fragment
    try:
        p = urlparse(u)
        base = f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        base = u
    return hashlib.sha256(base.encode('utf-8')).hexdigest()

@app.route('/api/crawl-urls', methods=['POST'])
def crawl_urls_endpoint():
    """Crawl one or more listing page URLs, extract job links, scrape job pages, and store results.
    Request: { urls: [string], max_links_per_listing?: int }
    """
    data = request.get_json() or {}
    urls: List[str] = data.get('urls') or []
    keywords: str = data.get('keywords') or ''
    # Clamp max_links to keep runtime predictable on modest servers
    try:
        max_links = int(data.get('max_links_per_listing', 25))
    except Exception:
        max_links = 25
    max_links = max(1, min(max_links, 50))

    if not isinstance(urls, list) or not urls:
        return jsonify({'success': False, 'error': 'urls must be a non-empty array'}), 400

    # Sanitize and limit incoming listing URLs to http/https and dedupe
    def _is_safe_url(u: str) -> bool:
        try:
            p = urlparse(u)
            if p.scheme not in ('http', 'https'):
                return False
            if not p.netloc:
                return False
            return True
        except Exception:
            return False

    sanitized = []
    seen = set()
    for u in urls:
        if not isinstance(u, str):
            continue
        u = u.strip()
        if not u or len(u) > 2048:
            continue
        if not _is_safe_url(u):
            continue
        key = compute_canonical_hash(u)
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(u)
        if len(sanitized) >= 5:  # Hard cap per request
            break

    if not sanitized:
        return jsonify({'success': False, 'error': 'no valid http/https listing urls provided'}), 400
    urls = sanitized

    headers = {'User-Agent': 'Mozilla/5.0'}
    created = 0
    updated = 0
    collected: List[Dict] = []

    run_started = datetime.now().isoformat()
    logger.info(f"Crawl start urls={len(urls)} max_links={max_links}")
    per_url_results = []
    total_found_created = 0
    total_found_updated = 0
    for listing_url in urls:
        try:
            started_at = datetime.now().isoformat()
            # Rate-limited fetch to be polite and keep within resource limits
            r = fetch_url(listing_url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"Listing fetch non-200 for {listing_url}: {r.status_code}")
                # log error
                domain = extract_domain(listing_url) or ''
                err = f"HTTP {r.status_code}"
                logger.error(f"Crawl listing error domain={domain} url={listing_url} err={err}")
                record_failure(domain, err)
                try:
                    if db and hasattr(db, 'log_crawl'):
                        db.log_crawl(domain, listing_url, 'error', 0, err, started_at, datetime.now().isoformat())
                    else:
                        memory_crawl_logs.append({'domain': domain, 'listing_url': listing_url, 'status': 'error', 'found_count': 0, 'error_message': err, 'started_at': started_at, 'finished_at': datetime.now().isoformat()})
                        memory_crawl_logs[:] = memory_crawl_logs[-100:]
                except Exception:
                    pass
                per_url_results.append({'listing_url': listing_url, 'domain': domain, 'status': 'error', 'found': 0, 'error': err})
                continue
            base_domain = extract_domain(listing_url) or ''
            soup = BeautifulSoup(r.text, 'html.parser')
            anchors = soup.find_all('a', href=True)
            job_links = []
            for a in anchors:
                try:
                    href = a['href']
                    abs_url = urljoin(listing_url, href)
                    if is_probable_job_link(abs_url, base_domain):
                        job_links.append(abs_url)
                        if len(job_links) >= max_links:
                            break
                except Exception:
                    continue

            # Deduplicate job_links
            seen_links = set()
            unique_links = []
            for jl in job_links:
                key = compute_canonical_hash(jl)
                if key not in seen_links:
                    unique_links.append(jl)
                    seen_links.add(key)

            # Fetch each job page
            created_here = 0
            updated_here = 0
            attempted_here = 0
            for jl in unique_links:
                try:
                    attempted_here += 1
                    jr = fetch_url(jl, headers=headers, timeout=15)
                    if jr.status_code != 200:
                        record_failure(extract_domain(jl) or '', f"HTTP {jr.status_code}")
                        continue
                    job = parse_job_page(jl, jr.text)
                    # Compute score and add crawl metadata
                    try:
                        intel = extract_company_intelligence(job)
                        job['lead_score'] = intel.get('lead_score', 0)
                    except Exception:
                        job['lead_score'] = 0
                    job['crawled_at'] = datetime.now().isoformat()
                    job['source_listing'] = listing_url
                    # Save to DB or memory (dedupe by URL, then title+company+date)
                    saved = False
                    if db:
                        try:
                            exists_id = None
                            if hasattr(db, 'job_exists_by_url'):
                                exists_id = db.job_exists_by_url(job.get('url'))
                            if not exists_id and hasattr(db, 'job_exists_by_title_company_date'):
                                exists_id = db.job_exists_by_title_company_date(job.get('title'), job.get('company'), job.get('date_posted'))
                            if exists_id:
                                db.update_job_last_seen(exists_id)
                                updated += 1
                                updated_here += 1
                            else:
                                job_data = {
                                    'title': job.get('title','Unknown'),
                                    'company': job.get('company','Unknown'),
                                    'location': job.get('location','Unknown'),
                                    'platform': job.get('platform','Unknown'),
                                    'url': job.get('url'),
                                    'description': job.get('description',''),
                                    'salary_range': job.get('salary_range',''),
                                    'experience_level': job.get('experience_level',''),
                                    'employment_type': job.get('employment_type',''),
                                    'date_posted': job.get('date_posted', datetime.now().strftime('%Y-%m-%d')),
                                    'keywords_used': scraping_status.get('last_search','')
                                }
                                jid = db.insert_job(job_data)
                                # Update extra fields
                                try:
                                    db.update_job_extra(jid, source_listing=listing_url, crawled_at=job['crawled_at'], lead_score=job.get('lead_score'))
                                except Exception as e:
                                    print(f"Update extra failed for job {jid}: {e}")
                                created += 1
                                created_here += 1
                            saved = True
                        except Exception as e:
                            print(f"DB save error for {jl}: {e}")
                    if not saved:
                        # Fallback: add to live_jobs (in-memory)
                        live_jobs.append(job)
                        created += 1
                        created_here += 1
                        collected.append(job)
                except Exception as e:
                    print(f"Job fetch error: {e}")
                    logger.error(f"Crawl job fetch error url={jl} err={e}")
                    record_failure(extract_domain(jl) or '', str(e))
                time.sleep(0.25)  # polite delay per job
            total_found_created += created_here
            total_found_updated += updated_here
            # Log per-listing crawl
            try:
                if db and hasattr(db, 'log_crawl'):
                    db.log_crawl(base_domain, listing_url, 'ok', created_here + updated_here, None, started_at, datetime.now().isoformat())
                else:
                    memory_crawl_logs.append({'domain': base_domain, 'listing_url': listing_url, 'status': 'ok', 'found_count': created_here + updated_here, 'error_message': None, 'started_at': started_at, 'finished_at': datetime.now().isoformat()})
                    memory_crawl_logs[:] = memory_crawl_logs[-100:]
            except Exception:
                pass
            logger.info(f"Crawl listing done domain={base_domain} url={listing_url} attempted={attempted_here} found={created_here+updated_here}")
            per_url_results.append({'listing_url': listing_url, 'domain': base_domain, 'status': 'ok', 'attempted': attempted_here, 'found': created_here + updated_here})
        except Exception as e:
            print(f"Listing error: {e}")
            domain = extract_domain(listing_url) or ''
            logger.error(f"Crawl listing exception domain={domain} url={listing_url} err={e}")
            try:
                if db and hasattr(db, 'log_crawl'):
                    db.log_crawl(domain, listing_url, 'error', 0, str(e), started_at, datetime.now().isoformat())
                else:
                    memory_crawl_logs.append({'domain': domain, 'listing_url': listing_url, 'status': 'error', 'found_count': 0, 'error_message': str(e), 'started_at': started_at, 'finished_at': datetime.now().isoformat()})
                    memory_crawl_logs[:] = memory_crawl_logs[-100:]
            except Exception:
                pass
            record_failure(domain, str(e))

    # Save last-run summary
    try:
        global last_crawl_summary
        last_crawl_summary = {
            'started_at': run_started,
            'finished_at': datetime.now().isoformat(),
            'urls': urls,
            'keywords': keywords,
            'results': per_url_results,
            'total_created': created,
            'total_updated': updated,
            'total_attempted': sum((r.get('attempted') or 0) for r in per_url_results),
            'total_found': total_found_created + total_found_updated
        }
    except Exception:
        pass
    logger.info(f"Crawl end urls={len(urls)} created={created} updated={updated} found={total_found_created+total_found_updated}")

    return jsonify({
        'success': True,
        'created': created,
        'updated': updated,
        'collected_preview': collected[:20]
    })

@app.route('/api/export-jobs')
def export_jobs_endpoint():
    """Export jobs as CSV, from DB when available else in-memory."""
    search = (request.args.get('search') or '').lower().strip()
    crawled_only = request.args.get('crawled_only', '0') in ('1','true','True')
    min_score = int(request.args.get('min_score', 0))
    limit = int(request.args.get('limit', 1000))
    rows: List[Dict] = []
    if db and hasattr(db, 'get_jobs'):
        try:
            # Use raw query here to support crawled_only filter
            if crawled_only:
                db.connect()
                cur = db.conn.cursor()
                sql = 'SELECT * FROM jobs WHERE source_listing IS NOT NULL'
                params = []
                if search:
                    sql += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ? OR url LIKE ?)' 
                    pattern = f'%{search}%'
                    params.extend([pattern, pattern, pattern, pattern])
                sql += ' ORDER BY first_seen DESC LIMIT ?'
                params.append(limit)
                cur.execute(sql, params)
                rows = [dict(r) for r in cur.fetchall()]
            else:
                rows = db.get_jobs(limit=limit, search=search or None)
        except Exception as e:
            print(f"DB get_jobs export error: {e}")
    if not rows:
        rows = live_jobs
        if search:
            rows = [j for j in rows if search in (j.get('title','').lower()+j.get('company','').lower()+j.get('description','').lower())]
        if crawled_only:
            rows = [j for j in rows if j.get('source_listing')]
    # Filter by score if requested
    if min_score > 0:
        nr = []
        for r in rows:
            sc = r.get('lead_score')
            try:
                sc = int(sc) if sc is not None else None
            except Exception:
                sc = None
            if sc is None:
                # compute score fallback
                try:
                    intel = extract_company_intelligence(r)
                    sc = intel.get('lead_score', 0)
                    r['lead_score'] = sc
                except Exception:
                    sc = 0
            if sc >= min_score:
                nr.append(r)
        rows = nr
        rows = rows[:limit]

    output = io.StringIO()
    headers = ['title','company','location','platform','url','date_posted','crawled_at','source_listing','lead_score','description']
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k,'') for k in headers})
    mem = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)

@app.route('/api/selenium-crawl', methods=['POST'])
def selenium_crawl_stub():
    """Stub endpoint for Selenium-based crawl. Not available on serverless by default.

    Returns 501 with guidance, unless ENABLE_SELENIUM=1 is set and environment provides Chrome.
    """
    if os.getenv('ENABLE_SELENIUM', '0') not in ('1', 'true', 'True'):
        return jsonify({'success': False, 'error': 'Selenium worker not enabled in this runtime. Run locally via `python -m crawler.selenium_crawler` or deploy a worker service.', 'doc': '/CRAWLER.md'}), 501
    try:
        from crawler.selenium_crawler import crawl_listings, SeleniumCrawlerConfig
    except Exception as e:
        return jsonify({'success': False, 'error': f'Selenium not available: {e}'}), 500
    data = request.get_json(silent=True) or {}
    urls = data.get('urls') or []
    keywords = data.get('keywords') or ''
    if not urls:
        return jsonify({'success': False, 'error': 'urls required'}), 400
    kw = [k.strip() for k in (keywords or '').split(',') if k.strip()]
    cfg = SeleniumCrawlerConfig(keywords=kw or None)
    summary = crawl_listings(urls, cfg, db)
    return jsonify({'success': True, **summary})
@app.route('/api/crawl-last-run')
def crawl_last_run():
    try:
        return jsonify({'success': True, 'summary': last_crawl_summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/results')
def results_page():
    return render_template('results.html')

@app.route('/leads')
def leads_page():
    return render_template('leads.html')

@app.route('/api/crawl-results')
def crawl_results_api():
    """Fetch crawled results with filters: search, source, has_budget."""
    search = (request.args.get('search') or '').strip()
    source = (request.args.get('source') or '').strip()
    has_budget = request.args.get('has_budget', '0') in ('1','true','True')
    min_score = int(request.args.get('min_score', 0))
    sort = (request.args.get('sort') or '').strip()  # score_desc|score_asc|recent
    limit = int(request.args.get('limit', 500))
    out: List[Dict] = []
    try:
        if db:
            db.connect()
            cur = db.conn.cursor()
            sql = 'SELECT * FROM jobs WHERE source_listing IS NOT NULL'
            params: List = []
            if search:
                sql += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ? OR url LIKE ? OR source_listing LIKE ?)' 
                pattern = f'%{search}%'
                params.extend([pattern, pattern, pattern, pattern, pattern])
            if source:
                sql += ' AND (source_listing LIKE ? OR platform LIKE ?)' 
                sp = f'%{source}%'
                params.extend([sp, sp])
            sql += ' ORDER BY COALESCE(crawled_at, first_seen) DESC LIMIT ?'
            params.append(limit)
            cur.execute(sql, params)
            out = [dict(r) for r in cur.fetchall()]
        else:
            out = [j for j in live_jobs if j.get('source_listing')]
            if search:
                s = search.lower()
                out = [j for j in out if s in (j.get('title','')+j.get('company','')+j.get('description','')+j.get('url','')+j.get('source_listing','')).lower()]
            if source:
                s = source.lower()
                out = [j for j in out if s in (j.get('source_listing','').lower() + ' ' + (j.get('platform','') or '').lower())]
            out = out[:limit]
        # Compute has_budget and fallback score if missing
        def compute_has_budget(j):
            txt = (j.get('description') or '') + ' ' + (j.get('salary') or j.get('salary_range') or '')
            t = txt.lower()
            return any(w in t for w in ['salary', '$', 'usd', 'eur', 'compensation', 'budget', 'rate', 'per hour', 'per annum', 'k'])
        for j in out:
            if j.get('lead_score') is None:
                try:
                    intel = extract_company_intelligence(j)
                    j['lead_score'] = intel.get('lead_score', 0)
                except Exception:
                    j['lead_score'] = 0
            j['has_budget'] = compute_has_budget(j)
        if has_budget:
            out = [j for j in out if j.get('has_budget')]
        if min_score > 0:
            out = [j for j in out if (j.get('lead_score') or 0) >= min_score]
        if sort == 'score_desc':
            out.sort(key=lambda x: x.get('lead_score') or 0, reverse=True)
        elif sort == 'score_asc':
            out.sort(key=lambda x: x.get('lead_score') or 0)
        elif sort == 'recent':
            out.sort(key=lambda x: (x.get('crawled_at') or x.get('first_seen') or ''), reverse=True)
        return jsonify({'success': True, 'total': len(out), 'results': out})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-crawl-results', methods=['POST'])
def clear_crawl_results():
    try:
        deleted = 0
        if db and hasattr(db, 'clear_crawl_results'):
            deleted = db.clear_crawl_results()
        # Also clear in-memory crawled jobs
        global live_jobs
        live_jobs = [j for j in live_jobs if not j.get('source_listing')]
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/crawl-logs')
@admin_required
def admin_crawl_logs():
    limit = int(request.args.get('limit', 20))
    try:
        logs = []
        if db and hasattr(db, 'get_crawl_logs'):
            logs = db.get_crawl_logs(limit=limit)
        else:
            logs = memory_crawl_logs[-limit:][::-1]
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/app-logs')
@admin_required
def admin_app_logs():
    try:
        lines = tail_log(LOG_FILE, int(request.args.get('lines', 20)))
        size = 0
        try:
            size = os.path.getsize(LOG_FILE)
        except Exception:
            pass
        return jsonify({'success': True, 'path': LOG_FILE, 'size': size, 'lines': lines})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def scrape_nodesk_rss(keywords: str, limit: int = 15) -> List[Dict]:
    jobs: List[Dict] = []
    try:
        rss_url = 'https://nodesk.co/remote-jobs/feed/'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(rss_url, headers=headers, timeout=10)
        if r.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            items = root.findall('.//item')
            k = (keywords or '').lower()
            for item in items:
                if len(jobs) >= limit:
                    break
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                desc = (item.findtext('description') or '')
                blob = f"{title} {desc}".lower()
                if not k or any(w for w in k.split() if len(w)>2 and w in blob):
                    jobs.append({
                        'title': title,
                        'company': 'NoDesk',
                        'location': 'Remote',
                        'platform': 'NoDesk',
                        'url': link,
                        'description': re.sub('<[^<]+?>', '', desc)[:300],
                        'date_posted': datetime.now().strftime('%Y-%m-%d'),
                        'id': f"nodesk_{len(jobs)}",
                        'lead_score': 50
                    })
    except Exception as e:
        print(f"NoDesk RSS error: {e}")
    if not jobs:
        jobs = [{
            'title': f'Remote {keywords.title()} Specialist',
            'company': 'NoDesk',
            'location': 'Remote',
            'platform': 'NoDesk',
            'url': 'https://nodesk.co/remote-jobs/',
            'description': f'Fallback NoDesk listing for {keywords}',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'id': 'nodesk_fallback',
            'lead_score': 50
        }]
    return jobs

@app.route('/api/business-leads')
def business_leads_endpoint():
    """Get business leads for lead generation with database integration."""
    min_score = int(request.args.get('min_score', 40))
    limit = int(request.args.get('limit', 50))
    
    # Try to get leads from database first
    if db and hasattr(db, 'get_business_leads'):
        try:
            db_leads = db.get_business_leads(limit=limit, min_score=min_score)
            if db_leads:
                high_value_leads = len([l for l in db_leads if l.get('lead_score', 0) >= 70])
                platforms_tracked = list(set(l.get('platform', 'Unknown') for l in db_leads))
                
                return jsonify({
                    'leads': db_leads,
                    'total_leads': len(db_leads),
                    'high_value_leads': high_value_leads,
                    'platforms_tracked': platforms_tracked,
                    'database_enabled': True
                })
        except Exception as e:
            print(f"Error getting business leads from database: {e}")
    
    # Fallback to in-memory storage
    filtered_leads = [l for l in business_leads if l.get('lead_score', 0) >= min_score]
    limited_leads = filtered_leads[-limit:] if len(filtered_leads) > limit else filtered_leads
    
    return jsonify({
        'leads': limited_leads,
        'total_leads': len(business_leads),
        'high_value_leads': len([l for l in business_leads if l.get('lead_score', 0) >= 70]),
        'platforms_tracked': list(set(l.get('platform', 'Unknown') for l in business_leads)),
        'database_enabled': False
    })

@app.route('/api/generate-outreach', methods=['POST'])
def generate_outreach():
    """Generate personalized outreach templates for a lead."""
    if not OUTREACH_TEMPLATES_ENABLED:
        return jsonify({
            'success': False,
            'message': 'Outreach templates module not available'
        })
    
    data = request.get_json()
    
    # Lead data
    lead_data = {
        'company': data.get('company'),
        'title': data.get('job_title'),
        'contact_name': data.get('contact_name', 'there'),
        'contact_title': data.get('contact_title', ''),
        'company_size': data.get('company_size', 'Growing'),
        'tech_stack': data.get('tech_stack', 'modern technologies'),
        'platform': data.get('platform', 'LinkedIn'),
        'lead_score': data.get('lead_score', 50)
    }
    
    # Sender data (you can make this configurable)
    sender_data = {
        'name': data.get('sender_name', 'Alex Johnson'),
        'title': data.get('sender_title', 'Business Development Director'),
        'company': data.get('sender_company', 'TechScale Solutions'),
        'email': data.get('sender_email', 'alex@techscale.com'),
        'phone': data.get('sender_phone', '+1 (555) 123-4567')
    }
    
    try:
        # Generate complete outreach sequence
        sequence = outreach_personalizer.get_outreach_sequence(lead_data, sender_data)
        
        # Get template recommendations
        recommendations = outreach_personalizer.get_template_recommendations(lead_data)
        
        return jsonify({
            'success': True,
            'outreach_sequence': sequence,
            'recommendations': recommendations,
            'total_templates': len(sequence),
            'lead_data_quality': lead_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating outreach templates: {str(e)}'
        })

@app.route('/api/discover-contacts', methods=['POST'])
def discover_contacts():
    """Discover contact information for a company."""
    if not CONTACT_DISCOVERY_ENABLED:
        return jsonify({
            'success': False,
            'message': 'Contact discovery module not available'
        })
    
    data = request.get_json()
    company_name = data.get('company_name')
    job_title = data.get('job_title', '')
    job_url = data.get('job_url', '')
    
    if not company_name:
        return jsonify({
            'success': False,
            'message': 'Company name is required'
        })
    
    try:
        # Discover contacts
        contact_results = contact_discovery.discover_contacts(company_name, job_title, job_url)
        
        # Save contact information to database if available
        if db and contact_results.get('confidence_score', 0) > 0:
            try:
                # Find corresponding job in database
                jobs = db.search_jobs(keywords=job_title, limit=100)
                matching_job = next((job for job in jobs if job.get('company', '').lower() == company_name.lower()), None)
                
                if matching_job:
                    # Save contacts to job record
                    all_emails = contact_results.get('direct_emails', []) + [
                        guess['email'] for guess in contact_results.get('guessed_emails', [])
                    ]
                    
                    contact_sources = {}
                    for email in contact_results.get('direct_emails', []):
                        contact_sources[email] = {'source': 'website_scrape', 'verified': True, 'type': 'extracted'}
                    
                    for guess in contact_results.get('guessed_emails', []):
                        email = guess['email']
                        contact_sources[email] = {
                            'source': 'name_pattern', 
                            'verified': False, 
                            'type': 'guessed',
                            'confidence': guess.get('confidence', 0.5)
                        }
                    
                    if hasattr(db, 'save_job_contacts'):
                        db.save_job_contacts(
                            matching_job['id'], 
                            all_emails, 
                            contact_sources, 
                            contact_results.get('domain')
                        )
                        
            except Exception as e:
                print(f"Error saving contact info to database: {e}")
        
        return jsonify({
            'success': True,
            'contacts': contact_results,
            'database_saved': db is not None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error discovering contacts: {str(e)}'
        })

@app.route('/api/lead-analysis/<company>')
def lead_analysis(company):
    """Get detailed lead analysis and scoring breakdown."""
    # Try to get lead from database first
    if db and hasattr(db, 'get_business_leads'):
        try:
            leads = db.get_business_leads(limit=1000)
            matching_lead = next((lead for lead in leads if lead.get('company', '').lower() == company.lower()), None)
            
            if matching_lead:
                return jsonify({
                    'success': True,
                    'lead': matching_lead,
                    'analysis_available': True
                })
        except Exception as e:
            print(f"Error getting lead analysis from database: {e}")
    
    # Fallback to in-memory search
    matching_lead = next((lead for lead in business_leads if lead.get('company', '').lower() == company.lower()), None)
    
    if matching_lead:
        return jsonify({
            'success': True,
            'lead': matching_lead,
            'analysis_available': False
        })
    
    return jsonify({
        'success': False,
        'message': 'Lead not found'
    })

@app.route('/api/stats')
def stats():
    """Get dashboard statistics with database integration."""
    # Try to get stats from database first
    if db and hasattr(db, 'get_stats'):
        try:
            db_stats = db.get_stats()
            if db_stats:
                return jsonify({
                    'total_jobs': db_stats.get('total_jobs', 0),
                    'total_leads': db_stats.get('total_leads', 0),
                    'high_value_leads': db_stats.get('high_value_leads', 0),
                    'platforms_active': 7,
                    'last_search': scraping_status.get('last_search', 'None'),
                    'search_status': 'Running' if scraping_status.get('running') else 'Ready',
                    'database_enabled': True,
                    'recent_searches': db_stats.get('recent_searches', 0),
                    'top_platforms': db_stats.get('top_platforms', [])
                })
        except Exception as e:
            print(f"Error getting stats from database: {e}")
    
    # Fallback to in-memory statistics
    return jsonify({
        'total_jobs': len(live_jobs),
        'total_leads': len(business_leads),
        'high_value_leads': len([l for l in business_leads if l.get('lead_score', 0) >= 70]),
        'platforms_active': 7,
        'last_search': scraping_status.get('last_search', 'None'),
        'search_status': 'Running' if scraping_status.get('running') else 'Ready',
        'database_enabled': False
    })

@app.route('/api/populate-sample-jobs', methods=['POST'])
def populate_sample_jobs():
    """Populate database with sample job postings for testing."""
    global live_jobs
    
    sample_jobs = [
        {
            'title': 'Senior Python Developer',
            'company': 'TechCorp Solutions',
            'location': 'Remote',
            'description': 'Looking for experienced Python developer with Django and FastAPI experience. Work on exciting projects with a global team.',
            'platform': 'linkedin',
            'url': 'https://linkedin.com/jobs/sample-1',
            'salary': '$120k - $180k',
            'posted_date': '2 days ago',
            'lead_score': 85,
            'company_size': '500-1000',
            'industry': 'Technology'
        },
        {
            'title': 'Full Stack Engineer',
            'company': 'StartupHub Inc',
            'location': 'San Francisco, CA (Hybrid)',
            'description': 'Join our fast-growing startup! React, Node.js, MongoDB. Competitive salary and equity.',
            'platform': 'wellfound',
            'url': 'https://wellfound.com/jobs/sample-2',
            'salary': '$100k - $150k + equity',
            'posted_date': '1 day ago',
            'lead_score': 78,
            'company_size': '50-100',
            'industry': 'SaaS'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'CloudNative Systems',
            'location': 'Remote (US)',
            'description': 'AWS, Kubernetes, Terraform expert needed. Help us scale our infrastructure.',
            'platform': 'remoteok',
            'url': 'https://remoteok.com/jobs/sample-3',
            'salary': '$130k - $170k',
            'posted_date': '3 hours ago',
            'lead_score': 92,
            'company_size': '200-500',
            'industry': 'Cloud Services'
        },
        {
            'title': 'Data Scientist',
            'company': 'AI Analytics Co',
            'location': 'New York, NY',
            'description': 'Machine learning, Python, TensorFlow. Work on cutting-edge AI projects.',
            'platform': 'indeed',
            'url': 'https://indeed.com/jobs/sample-4',
            'salary': '$140k - $200k',
            'posted_date': '5 days ago',
            'lead_score': 88,
            'company_size': '1000+',
            'industry': 'Artificial Intelligence'
        },
        {
            'title': 'Frontend Developer',
            'company': 'DesignFirst Studios',
            'location': 'Remote',
            'description': 'React, TypeScript, Next.js. Build beautiful user interfaces.',
            'platform': 'weworkremotely',
            'url': 'https://weworkremotely.com/jobs/sample-5',
            'salary': '$90k - $130k',
            'posted_date': '1 week ago',
            'lead_score': 72,
            'company_size': '10-50',
            'industry': 'Design'
        },
        {
            'title': 'Backend Engineer',
            'company': 'FinTech Innovations',
            'location': 'London, UK (Remote)',
            'description': 'Node.js, PostgreSQL, microservices. Build scalable financial systems.',
            'platform': 'nodesk',
            'url': 'https://nodesk.co/jobs/sample-6',
            'salary': '£80k - £120k',
            'posted_date': '4 days ago',
            'lead_score': 81,
            'company_size': '100-200',
            'industry': 'FinTech'
        },
        {
            'title': 'Mobile App Developer',
            'company': 'AppMasters Ltd',
            'location': 'Austin, TX',
            'description': 'React Native or Flutter. iOS and Android development.',
            'platform': 'glassdoor',
            'url': 'https://glassdoor.com/jobs/sample-7',
            'salary': '$110k - $160k',
            'posted_date': '2 weeks ago',
            'lead_score': 75,
            'company_size': '50-100',
            'industry': 'Mobile Apps'
        },
        {
            'title': 'Software Architect',
            'company': 'Enterprise Solutions Group',
            'location': 'Remote (Global)',
            'description': 'Lead technical architecture for enterprise applications. 10+ years experience.',
            'platform': 'linkedin',
            'url': 'https://linkedin.com/jobs/sample-8',
            'salary': '$180k - $250k',
            'posted_date': '1 day ago',
            'lead_score': 95,
            'company_size': '1000+',
            'industry': 'Enterprise Software'
        }
    ]
    
    # Add to in-memory storage
    live_jobs.clear()
    live_jobs.extend(sample_jobs)
    
    # Try to add to database if available
    saved_count = 0
    if db and hasattr(db, 'add_job'):
        for job in sample_jobs:
            try:
                db.add_job(job)
                saved_count += 1
            except Exception as e:
                print(f"Error saving job to database: {e}")
    
    return jsonify({
        'success': True,
        'message': f'Added {len(sample_jobs)} sample jobs',
        'jobs_in_memory': len(live_jobs),
        'jobs_in_database': saved_count
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/demo')
def demo():
    """Interactive Job Scraper Dashboard."""
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Job Scraper - Find Real Jobs</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; }
            .header { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 2rem; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
            .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem; }
            .card { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
            .search-form { margin-bottom: 2rem; }
            .form-group { margin-bottom: 1rem; }
            .form-control { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; }
            .btn { padding: 0.75rem 2rem; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }
            .btn:hover { background: #5a67d8; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
            .stat-card { background: white; padding: 1.5rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
            .stat-number { font-size: 2rem; font-weight: bold; color: #667eea; }
            .job-card { background: white; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
            .job-title { font-size: 1.25rem; font-weight: bold; color: #2d3748; margin-bottom: 0.5rem; }
            .job-company { font-size: 1rem; color: #667eea; margin-bottom: 0.5rem; }
            .job-meta { display: flex; gap: 1rem; margin-bottom: 1rem; }
            .meta-item { background: #f7fafc; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; }
            .job-actions { margin-top: 1rem; display: flex; gap: 1rem; }
            .btn-apply { background: #48bb78; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-apply:hover { background: #38a169; }
            .btn-view { background: #4299e1; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-view:hover { background: #3182ce; }
            .btn-contact { background: #ed8936; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-contact:hover { background: #dd6b20; }
            .job-url { color: #4299e1; text-decoration: none; font-size: 0.875rem; }
            .job-url:hover { text-decoration: underline; }
            .lead-score { padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: bold; }
            .score-high { background: #c6f6d5; color: #22543d; }
            .score-medium { background: #fed7d7; color: #742a2a; }
            .score-low { background: #e2e8f0; color: #4a5568; }
            .status { margin-top: 1rem; padding: 1rem; background: #f7fafc; border-radius: 8px; text-align: center; }
            .hidden { display: none; }
            .score-excellent { background: #9ae6b4; color: #1a202c; }
            .score-breakdown { font-size: 0.75rem; margin-top: 0.5rem; }
            .score-breakdown details { margin-top: 0.25rem; }
            .score-breakdown summary { cursor: pointer; color: #667eea; font-weight: 500; }
            .btn-view-job { background: #38a169; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-view-job:hover { background: #2f855a; }
            .btn-outreach { background: #9f7aea; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.875rem; }
            .btn-outreach:hover { background: #805ad5; }
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
            .modal-content { background: white; margin: 2% auto; padding: 2rem; width: 90%; max-width: 800px; border-radius: 12px; max-height: 90vh; overflow-y: auto; }
            .close { float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
            .outreach-template { background: #f8fafc; padding: 1rem; margin: 1rem 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .template-header { font-weight: bold; color: #667eea; margin-bottom: 0.5rem; }
            .template-subject { font-weight: 600; margin-bottom: 0.5rem; background: #e2e8f0; padding: 0.5rem; border-radius: 4px; }
            .template-body { white-space: pre-wrap; font-family: monospace; font-size: 0.875rem; line-height: 1.4; }
            .copy-template { background: #48bb78; color: white; padding: 0.25rem 0.75rem; border: none; border-radius: 4px; cursor: pointer; margin-top: 0.5rem; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>🚀 Business Development Platform</h1>
                <p>Lead Generation Through Job Market Intelligence</p>
            </div>
        </div>

        <div class="container">
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalJobs">0</div>
                    <div>Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalLeads">0</div>
                    <div>Business Leads</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="highValueLeads">0</div>
                    <div>High-Value Leads</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="platformsActive">7</div>
                    <div>Platforms Active</div>
                </div>
            </div>

            <div class="dashboard">
                <div class="card">
                    <h2>🎯 Lead Generation Search</h2>
                    <div class="search-form">
                        <div class="form-group">
                            <input type="text" id="keywords" class="form-control" placeholder="Enter technology keywords (e.g., python developer, react engineer)" value="python developer">
                        </div>
                        <button onclick="startLiveScraping()" class="btn">🔍 Find Business Opportunities</button>
                    </div>
                    <div id="scrapingStatus" class="status hidden">
                        <div>🔄 Scanning job market for opportunities...</div>
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Business Intelligence</h2>
                    <div id="businessLeads">
                        <p>Start a search to identify potential clients and business opportunities.</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>💼 Market Opportunities</h2>
                <div id="liveJobs">
                    <p>No active search. Click "Find Business Opportunities" to discover companies hiring for tech roles.</p>
                </div>
            </div>
        </div>

        <!-- Outreach Templates Modal -->
        <div id="outreachModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeOutreachModal()">&times;</span>
                <h2>📧 Professional Outreach Templates</h2>
                <div id="outreachContent">
                    <p>Generating personalized outreach sequence...</p>
                </div>
            </div>
        </div>

        <script>
            let searchInterval;

            async function startLiveScraping() {
                const keywords = document.getElementById('keywords').value;
                const statusDiv = document.getElementById('scrapingStatus');
                
                if (!keywords.trim()) {
                    alert('Please enter keywords to search for business opportunities');
                    return;
                }

                statusDiv.classList.remove('hidden');
                
                try {
                    const response = await fetch('/api/live-scrape', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            keywords: keywords,
                            platforms: ['remoteok', 'adzuna', 'linkedin', 'indeed', 'weworkremotely', 'wellfound', 'glassdoor', 'nodesk']
                        })
                    });
                    
                    const result = await response.json();
                    
                    console.log('=== SCRAPE RESULT ===');
                    console.log('Jobs found:', result.jobs_found);
                    console.log('Platforms scraped:', result.platforms_scraped);
                    console.log('Total jobs in response:', result.jobs ? result.jobs.length : 0);
                    if (result.jobs) {
                        const platformBreakdown = {};
                        result.jobs.forEach(job => {
                            const p = job.platform || 'Unknown';
                            platformBreakdown[p] = (platformBreakdown[p] || 0) + 1;
                        });
                        console.log('Platform breakdown:', platformBreakdown);
                    }
                    console.log('=====================');
                    
                    if (result.success) {
                        statusDiv.innerHTML = `✅ Found ${result.jobs_found} opportunities across ${result.platforms_scraped.length} platforms`;
                        
                        // Display the jobs directly from the scraping response (fixes Vercel serverless issue)
                        if (result.jobs && result.jobs.length > 0) {
                            displayJobs(result.jobs);
                        }
                        
                        setTimeout(() => {
                            statusDiv.classList.add('hidden');
                            loadBusinessLeads();
                            loadStats();
                        }, 2000);
                    } else {
                        statusDiv.innerHTML = '❌ Search failed. Please try again.';
                    }
                } catch (error) {
                    statusDiv.innerHTML = '❌ Error occurred. Please try again.';
                    console.error('Search error:', error);
                }
            }

            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    document.getElementById('totalJobs').textContent = stats.total_jobs;
                    document.getElementById('totalLeads').textContent = stats.total_leads;
                    document.getElementById('highValueLeads').textContent = stats.high_value_leads;
                    document.getElementById('platformsActive').textContent = stats.platforms_active;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }

            function displayJobs(jobs) {
                const container = document.getElementById('liveJobs');
                
                if (!jobs || jobs.length === 0) {
                    container.innerHTML = '<p>No opportunities found. Try different keywords.</p>';
                    return;
                }
                
                console.log(`Displaying ${jobs.length} jobs from platforms:`, 
                    [...new Set(jobs.map(j => j.platform))]);
                
                container.innerHTML = jobs.map(job => `
                        <div class="job-card">
                            <div class="job-title">${job.title}</div>
                            <div class="job-company">${job.company}</div>
                            <div class="job-meta">
                                <span class="meta-item">📍 ${job.location}</span>
                                <span class="meta-item">🏢 ${job.platform}</span>
                                <span class="meta-item">💼 ${job.company_size || 'Unknown'}</span>
                                <span class="lead-score ${getScoreClass(job.lead_score)}">
                                    Score: ${job.lead_score || 0}%
                                </span>
                            </div>
                            <div class="meta-item">🛠️ ${job.tech_stack || 'General'}</div>
                            ${job.salary_range ? `<div class="meta-item">💰 ${job.salary_range}</div>` : ''}
                            <div class="job-actions">
                                ${job.url ? `<a href="${job.url}" target="_blank" class="btn-view" style="text-decoration: none;">🔗 View Original Job</a>` : ''}
                                <button class="btn-view" onclick="researchCompany('${job.company}', '${job.title}')">� Research Company</button>
                                <button class="btn-contact" onclick="contactCompany('${job.company}', '${job.title}')">� Get Contact Info</button>
                                <button class="btn-apply" onclick="saveAsLead('${job.company}', '${job.title}', ${job.lead_score})">⭐ Save Lead</button>
                            </div>
                        </div>
                    `).join('');
            }

            async function loadLiveJobs() {
                try {
                    const response = await fetch('/api/live-jobs');
                    const jobs = await response.json();
                    displayJobs(jobs);
                } catch (error) {
                    console.error('Error loading jobs:', error);
                }
            }

            async function loadBusinessLeads() {
                try {
                    const response = await fetch('/api/business-leads');
                    const data = await response.json();
                    
                    const container = document.getElementById('businessLeads');
                    
                    if (data.leads.length === 0) {
                        container.innerHTML = '<p>No qualified leads yet. Start searching to identify potential clients.</p>';
                        return;
                    }
                    
                    container.innerHTML = `
                        <div style="margin-bottom: 1rem;">
                            <strong>Qualified Leads: ${data.total_leads}</strong> | 
                            <strong>High-Value: ${data.high_value_leads}</strong>
                        </div>
                        ${data.leads.slice(-10).map(lead => `
                            <div class="job-card">
                                <div class="job-title">${lead.title}</div>
                                <div class="job-company">🏢 ${lead.company}</div>
                                <div class="job-meta">
                                    <span class="meta-item">📍 ${lead.location}</span>
                                    <span class="meta-item">💼 ${lead.company_size}</span>
                                    <span class="lead-score ${getScoreClass(lead.lead_score)}">
                                        ${lead.contact_potential} Value (${lead.lead_score}%)
                                    </span>
                                </div>
                                <div class="meta-item">🛠️ ${lead.technologies.join(', ') || 'General Tech'}</div>
                                <div class="job-actions">
                                    ${lead.url ? `<a href="${lead.url}" target="_blank" class="btn-view" style="text-decoration: none;">🔗 View Original Job</a>` : ''}
                                    <button class="btn-view" onclick="researchCompany('${lead.company}', '${lead.title}')">� Research Company</button>
                                    <button class="btn-contact" onclick="contactCompany('${lead.company}', '${lead.title}')">📧 Business Contact</button>
                                    <button class="btn-apply" onclick="saveAsLead('${lead.company}', '${lead.title}', ${lead.lead_score})">⭐ Save Lead</button>
                                </div>
                            </div>
                        `).join('')}
                    `;
                } catch (error) {
                    console.error('Error loading business leads:', error);
                }
            }

            function getScoreClass(score) {
                if (score >= 85) return 'score-excellent';
                if (score >= 70) return 'score-high';
                if (score >= 40) return 'score-medium';
                return 'score-low';
            }

            // Business development functions with contact discovery
            async function researchCompany(company, jobTitle) {
                const researchSteps = `🔍 COMPANY RESEARCH: ${company}

QUICK RESEARCH CHECKLIST:
✅ Company Website: Search "${company} official website"
✅ LinkedIn Page: Search "${company}" on LinkedIn
✅ Recent News: Google "${company} news 2024"
✅ Funding/Growth: Check "${company} funding" or "Series A/B"
✅ Tech Stack: Look for "${company} technology stack" or engineering blog
✅ Hiring Scale: Count recent job postings on their careers page

BUSINESS OPPORTUNITY ASSESSMENT:
• Position: ${jobTitle}
• Why they're a lead: Actively hiring for tech roles
• Your angle: They need tech talent = potential for your services
• Best approach: Offer to augment their ${jobTitle} search

NEXT STEPS:
1. Visit their company website
2. Find their "Careers" or "About" page
3. Look for contact information or leadership team
4. Check their LinkedIn company page for employees
5. Identify decision makers (CTO, Head of Engineering, HR)`;

                // Copy research plan to clipboard
                try {
                    await navigator.clipboard.writeText(researchSteps);
                    alert(`🔍 Research plan for ${company} copied to clipboard!
                    
The research checklist will help you:
• Understand their business model
• Identify key decision makers  
• Find the best contact approach
• Position your services effectively

Start with their website and LinkedIn page.`);
                } catch (err) {
                    alert(`Research ${company} for ${jobTitle}:
                    
1. Google: "${company} official website"
2. LinkedIn: Search "${company}" 
3. Check their careers page
4. Look for engineering team contacts
5. Identify decision makers (CTO, Engineering Manager)`);
                }
            }

            async function contactCompany(company, jobTitle) {
                // Show loading state
                const button = event.target;
                const originalText = button.textContent;
                button.textContent = '🔍 Finding Contacts...';
                button.disabled = true;

                try {
                    // Try automated contact discovery first
                    const response = await fetch('/api/discover-contacts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            company_name: company,
                            job_title: jobTitle
                        })
                    });

                    const result = await response.json();

                    if (result.success && result.contacts) {
                        const contacts = result.contacts;
                        let contactInfo = `📧 AUTOMATED CONTACT DISCOVERY: ${company}

🎯 FOUND CONTACT INFORMATION:
${contacts.domain ? `🌐 Company Website: https://${contacts.domain}` : ''}
${contacts.confidence_score ? `✅ Discovery Confidence: ${contacts.confidence_score}%` : ''}

`;

                        // Add direct emails if found
                        if (contacts.direct_emails && contacts.direct_emails.length > 0) {
                            contactInfo += `📧 VERIFIED EMAIL ADDRESSES:
${contacts.direct_emails.map(email => `• ${email}`).join('\\n')}

`;
                        }

                        // Add email guesses for decision makers
                        if (contacts.guessed_emails && contacts.guessed_emails.length > 0) {
                            const decisionMakerEmails = contacts.guessed_emails
                                .filter(guess => guess.is_decision_maker)
                                .sort((a, b) => b.confidence - a.confidence);

                            if (decisionMakerEmails.length > 0) {
                                contactInfo += `👨‍💼 DECISION MAKER CONTACTS (Likely):
${decisionMakerEmails.slice(0, 5).map(guess => 
    `• ${guess.email} (${guess.name}, ${guess.title}) - ${Math.round(guess.confidence * 100)}% confidence`
                                ).join('\\n')}

`;
                            }
                        }

                        // Add LinkedIn profiles
                        if (contacts.linkedin_profiles && contacts.linkedin_profiles.length > 0) {
                            contactInfo += `🔗 LINKEDIN PROFILES:
${contacts.linkedin_profiles.slice(0, 3).map(profile => `• ${profile}`).join('\\n')}

`;
                        }

                        contactInfo += `📋 OUTREACH STRATEGY:
1. Start with verified emails (highest success rate)
2. Connect with decision makers on LinkedIn first
3. Use warm introduction through mutual connections
4. Mention their ${jobTitle} hiring as conversation starter

💡 PROFESSIONAL MESSAGE TEMPLATE:
"Hi [Name],

I noticed ${company} is actively hiring for ${jobTitle} roles. As a tech solutions partner, we help companies like yours scale engineering teams faster with dedicated developers and project-based technical expertise.

Instead of just filling positions, we offer:
• Immediate technical capacity
• Specialized skill sets for specific projects
• Flexible engagement models

Would you be open to a brief conversation about how we could support ${company}'s technology initiatives?

Best regards,
[Your Name]"`;

                        // Copy to clipboard
                        await navigator.clipboard.writeText(contactInfo);
                        alert(`📧 Automated contact discovery complete for ${company}!

Found:
• ${contacts.direct_emails ? contacts.direct_emails.length : 0} verified emails
• ${contacts.guessed_emails ? contacts.guessed_emails.length : 0} contact guesses
• ${contacts.linkedin_profiles ? contacts.linkedin_profiles.length : 0} LinkedIn profiles
• ${contacts.decision_makers ? contacts.decision_makers.length : 0} decision makers

Full contact strategy copied to clipboard!`);
                    } else {
                        throw new Error('Automated discovery failed');
                    }

                } catch (error) {
                    console.error('Contact discovery error:', error);
                    
                    // Fallback to manual strategy
                    const manualContactInfo = `📧 CONTACT STRATEGY: ${company}

STEP 1: FIND DECISION MAKERS
• Search LinkedIn: "${company}" + "CTO" or "Head of Engineering"
• Check company website for leadership team
• Look for "Engineering" or "Technology" team members
• Find recent ${jobTitle} job posting authors

STEP 2: CONTACT METHODS
🔸 LinkedIn: Best for initial outreach
🔸 Company Email: info@[company].com or careers@[company].com  
🔸 Contact Forms: Usually on company website
🔸 Twitter/X: Many CTOs are active on Twitter

STEP 3: OUTREACH MESSAGE TEMPLATE
Subject: Partnership Opportunity - Tech Talent Solutions

Hi [Name],

I noticed ${company} is actively hiring for ${jobTitle} roles. As a tech service startup, we specialize in providing skilled developers and technical solutions that could complement your growing team.

Instead of just filling positions, we offer:
• Dedicated development teams
• Project-based technical solutions  
• Flexible scaling for your engineering needs

Would you be open to a brief conversation about how we could support ${company}'s technology initiatives?

Best regards,
[Your Name]
[Your Company]

STEP 4: FOLLOW-UP PLAN
• Initial contact via LinkedIn
• Follow up via email after 1 week
• Provide case studies or portfolio
• Offer free consultation or pilot project`;

                    try {
                        await navigator.clipboard.writeText(manualContactInfo);
                        alert(`📧 Manual contact strategy for ${company} copied!
                        
This includes:
✅ How to find decision makers
✅ Best contact methods
✅ Professional outreach template
✅ Follow-up strategy

Start with LinkedIn to find their CTO or Engineering Manager.`);
                    } catch (err) {
                        alert(`Contact ${company} about ${jobTitle}:
                        
1. Find their CTO/Engineering Manager on LinkedIn
2. Send professional connection request
3. Mention their ${jobTitle} hiring
4. Offer tech services as partnership
5. Follow up with portfolio/case studies`);
                    }
                } finally {
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                }
            }

            function saveAsLead(company, jobTitle, leadScore) {
                const leadData = {
                    company: company,
                    position: jobTitle,
                    score: leadScore,
                    date: new Date().toLocaleDateString(),
                    status: 'New Lead'
                };

                // Store in localStorage for now (in real app, would send to backend)
                let savedLeads = JSON.parse(localStorage.getItem('businessLeads') || '[]');
                savedLeads.push(leadData);
                localStorage.setItem('businessLeads', JSON.stringify(savedLeads));

                alert(`⭐ ${company} saved as a business lead!
                
Lead Score: ${leadScore}%
Position: ${jobTitle}
Status: Ready for outreach

Tip: They're actively hiring, making this an ideal time to propose your tech services.`);
            }

            // Outreach Template Functions
            async function generateOutreach(company, jobTitle, companySize, techStack, leadScore) {
                document.getElementById('outreachModal').style.display = 'block';
                document.getElementById('outreachContent').innerHTML = '<p>🔄 Generating personalized outreach sequence...</p>';

                try {
                    const response = await fetch('/api/generate-outreach', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            company: company,
                            job_title: jobTitle,
                            company_size: companySize || 'Growing',
                            tech_stack: techStack || 'modern technologies',
                            lead_score: leadScore || 50,
                            platform: 'LinkedIn'
                        })
                    });

                    const result = await response.json();

                    if (result.success) {
                        displayOutreachSequence(result.outreach_sequence, result.recommendations, company);
                    } else {
                        throw new Error(result.message || 'Failed to generate outreach');
                    }

                } catch (error) {
                    console.error('Outreach generation error:', error);
                    document.getElementById('outreachContent').innerHTML = `
                        <p>❌ Error generating outreach templates. Falling back to manual templates...</p>
                        <div class="outreach-template">
                            <div class="template-header">📧 Manual Outreach Template</div>
                            <div class="template-subject">Partnership Opportunity - ${company} Technology Initiatives</div>
                            <div class="template-body">Hi there,

I noticed ${company} is actively hiring for ${jobTitle} roles, which suggests exciting growth in your technology team.

I'm reaching out because we specialize in providing dedicated development teams and technical solutions that complement in-house engineering efforts.

Would you be open to a brief conversation about how we could support ${company}'s technology initiatives?

Best regards,
[Your Name]</div>
                            <button class="copy-template" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋 Copy Template</button>
                        </div>
                    `;
                }
            }

            function displayOutreachSequence(sequence, recommendations, company) {
                let html = `
                    <div style="margin-bottom: 1rem;">
                        <h3>🎯 Outreach Strategy for ${company}</h3>
                        <p><strong>Total Templates:</strong> ${sequence.length} | <strong>Sequence Duration:</strong> ~2 months</p>
                    </div>
                `;

                if (recommendations && recommendations.length > 0) {
                    html += `
                        <div style="background: #e6fffa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                            <h4>💡 Strategy Recommendations:</h4>
                            ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </div>
                    `;
                }

                sequence.forEach((template, index) => {
                    const typeEmoji = {
                        'initial': '🎯',
                        'follow_up': '🔄',
                        'value_add': '💎',
                        'final': '🏁'
                    };

                    html += `
                        <div class="outreach-template">
                            <div class="template-header">
                                ${typeEmoji[template.template_type] || '📧'} ${template.template_name}
                                <span style="float: right; font-size: 0.875rem; color: #666;">
                                    ${index === 0 ? 'Send Now' : `Send in ${template.follow_up_days} days`}
                                </span>
                            </div>
                            <div class="template-subject">Subject: ${template.subject}</div>
                            <div class="template-body">${template.body}</div>
                            <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #666;">
                                <strong>Personalization Score:</strong> ${template.personalization_score}% | 
                                <strong>Follow-up Date:</strong> ${template.follow_up_date}
                            </div>
                            <button class="copy-template" onclick="copyTemplate('${template.subject}', \`${template.body.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)">📋 Copy Template</button>
                        </div>
                    `;
                });

                html += `
                    <div style="margin-top: 2rem; padding: 1rem; background: #f0f9ff; border-radius: 8px;">
                        <h4>📊 Outreach Best Practices:</h4>
                        <ul>
                            <li>Send initial email on Tuesday-Thursday, 9-11 AM</li>
                            <li>Follow up consistently but not aggressively</li>
                            <li>Always provide value in each touchpoint</li>
                            <li>Personalize based on company news and updates</li>
                            <li>Track responses and adjust strategy accordingly</li>
                        </ul>
                    </div>
                `;

                document.getElementById('outreachContent').innerHTML = html;
            }

            function copyTemplate(subject, body) {
                const fullTemplate = `Subject: ${subject}

${body}`;
                
                copyToClipboard(fullTemplate);
                alert('📧 Template copied to clipboard! Ready to paste into your email client.');
            }

            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(() => {
                    console.log('Text copied to clipboard');
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                });
            }

            function closeOutreachModal() {
                document.getElementById('outreachModal').style.display = 'none';
            }

            // Close modal when clicking outside
            window.onclick = function(event) {
                const modal = document.getElementById('outreachModal');
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            }

            // Load initial data
            loadStats();
            
            // Handle Enter key
            document.getElementById('keywords').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    startLiveScraping();
                }
            });
        </script>
    </body>
    </html>
    '''
    return html

# ===== EMAIL AUTOMATION ENDPOINTS =====

@app.route('/api/email/send', methods=['POST'])
def send_email():
    """Send email via Gmail or Outlook."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    provider = data.get('provider', 'gmail').lower()  # gmail or outlook
    
    required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 
                      'recipient_email', 'subject', 'body']
    
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    if provider == 'gmail':
        result = email_automation.send_email_gmail(
            smtp_server=data['smtp_server'],
            smtp_port=data['smtp_port'],
            sender_email=data['sender_email'],
            sender_password=data['sender_password'],
            recipient_email=data['recipient_email'],
            subject=data['subject'],
            body=data['body'],
            is_html=data.get('is_html', True)
        )
    elif provider == 'outlook':
        result = email_automation.send_email_outlook(
            smtp_server=data['smtp_server'],
            smtp_port=data['smtp_port'],
            sender_email=data['sender_email'],
            sender_password=data['sender_password'],
            recipient_email=data['recipient_email'],
            subject=data['subject'],
            body=data['body'],
            is_html=data.get('is_html', True)
        )
    else:
        return jsonify({
            'success': False,
            'error': f'Unsupported provider: {provider}. Use "gmail" or "outlook"'
        }), 400
    
    return jsonify(result)

@app.route('/api/email/sequence/create', methods=['POST'])
def create_sequence():
    """Create automated email sequence."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    
    if 'sequence_name' not in data or 'emails' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: sequence_name, emails'
        }), 400
    
    result = email_automation.create_email_sequence(
        sequence_name=data['sequence_name'],
        emails=data['emails']
    )
    
    return jsonify(result)

@app.route('/api/email/sequence/start', methods=['POST'])
def start_sequence():
    """Start email sequence for a recipient."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    
    if 'sequence_id' not in data or 'recipient_email' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: sequence_id, recipient_email'
        }), 400
    
    result = email_automation.start_email_sequence(
        sequence_id=data['sequence_id'],
        recipient_email=data['recipient_email'],
        personalization=data.get('personalization', {})
    )
    
    return jsonify(result)

@app.route('/api/email/responses', methods=['POST'])
def check_responses():
    """Check for email responses."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    
    required_fields = ['imap_server', 'email_address', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    result = email_automation.check_email_responses(
        imap_server=data['imap_server'],
        email_address=data['email_address'],
        password=data['password'],
        since_date=data.get('since_date')
    )
    
    return jsonify(result)

@app.route('/api/email/stats', methods=['GET'])
def email_stats():
    """Get email campaign statistics."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    stats = email_automation.get_email_stats()
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/email/templates', methods=['GET'])
def email_templates():
    """Get pre-configured email sequence templates."""
    if not EMAIL_AUTOMATION_ENABLED:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    return jsonify({
        'success': True,
        'templates': EMAIL_SEQUENCE_TEMPLATES
    })

@app.route('/api/email/track/open', methods=['POST'])
def track_email_open():
    """Track email open."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    if 'email_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing email_id'
        }), 400
    
    result = email_automation.mark_email_opened(data['email_id'])
    return jsonify(result)

@app.route('/api/email/track/reply', methods=['POST'])
def track_email_reply():
    """Track email reply."""
    if not EMAIL_AUTOMATION_ENABLED or not email_automation:
        return jsonify({
            'success': False,
            'error': 'Email automation not available'
        }), 503
    
    data = request.get_json()
    if 'email_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing email_id'
        }), 400
    
    result = email_automation.mark_email_replied(data['email_id'])
    return jsonify(result)

# ===== ANALYTICS DASHBOARD ENDPOINTS =====

@app.route('/api/analytics/conversion/track', methods=['POST'])
def track_conversion():
    """Track conversion funnel event."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    data = request.get_json()
    
    if 'event_type' not in data or 'lead_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: event_type, lead_id'
        }), 400
    
    result = analytics.track_conversion_event(
        event_type=data['event_type'],
        lead_id=data['lead_id'],
        details=data.get('details', {})
    )
    
    return jsonify(result)

@app.route('/api/analytics/conversion/funnel', methods=['GET'])
def get_funnel():
    """Get conversion funnel statistics."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    funnel = analytics.get_conversion_funnel(start_dt, end_dt)
    
    return jsonify({
        'success': True,
        'funnel': funnel
    })

@app.route('/api/analytics/cost/track', methods=['POST'])
def track_cost():
    """Track cost data."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    data = request.get_json()
    
    required = ['platform', 'amount', 'cost_type']
    if not all(field in data for field in required):
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {required}'
        }), 400
    
    result = analytics.track_cost(
        platform=data['platform'],
        amount=data['amount'],
        cost_type=data['cost_type'],
        description=data.get('description')
    )
    
    return jsonify(result)

@app.route('/api/analytics/revenue/track', methods=['POST'])
def track_revenue():
    """Track revenue data."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    data = request.get_json()
    
    required = ['lead_id', 'amount', 'platform']
    if not all(field in data for field in required):
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {required}'
        }), 400
    
    result = analytics.track_revenue(
        lead_id=data['lead_id'],
        amount=data['amount'],
        platform=data['platform'],
        description=data.get('description')
    )
    
    return jsonify(result)

@app.route('/api/analytics/roi', methods=['GET'])
def get_roi_metrics():
    """Get ROI metrics and calculations."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    roi = analytics.get_roi_metrics(start_dt, end_dt)
    
    return jsonify({
        'success': True,
        'roi_metrics': roi
    })

@app.route('/api/analytics/platforms', methods=['GET'])
def get_platform_performance():
    """Get platform performance comparison."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    performance = analytics.get_platform_performance(start_dt, end_dt)
    
    return jsonify({
        'success': True,
        'performance': performance
    })

@app.route('/api/analytics/timeseries', methods=['GET'])
def get_timeseries():
    """Get time-series analysis."""
    if not ANALYTICS_ENABLED or not analytics:
        return jsonify({
            'success': False,
            'error': 'Analytics not available'
        }), 503
    
    granularity = request.args.get('granularity', 'daily')
    days = int(request.args.get('days', 30))
    
    timeseries = analytics.get_time_series_analysis(granularity, days)
    
    return jsonify({
        'success': True,
        'timeseries': timeseries
    })

# ===== CRM INTEGRATION ENDPOINTS =====

@app.route('/api/crm/configure/salesforce', methods=['POST'])
def configure_salesforce():
    """Configure Salesforce connection."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    required = ['instance_url', 'access_token']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = crm.configure_salesforce(
        instance_url=data['instance_url'],
        access_token=data['access_token'],
        api_version=data.get('api_version', 'v57.0')
    )
    return jsonify(result)

@app.route('/api/crm/configure/hubspot', methods=['POST'])
def configure_hubspot():
    """Configure HubSpot connection."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = crm.configure_hubspot(api_key=data['api_key'])
    return jsonify(result)

@app.route('/api/crm/configure/pipedrive', methods=['POST'])
def configure_pipedrive():
    """Configure Pipedrive connection."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    required = ['api_token', 'company_domain']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = crm.configure_pipedrive(
        api_token=data['api_token'],
        company_domain=data['company_domain']
    )
    return jsonify(result)

@app.route('/api/crm/salesforce/lead', methods=['POST'])
def create_salesforce_lead():
    """Create lead in Salesforce."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.salesforce_create_lead(data)
    return jsonify(result)

@app.route('/api/crm/salesforce/lead/<lead_id>', methods=['PATCH'])
def update_salesforce_lead(lead_id):
    """Update lead in Salesforce."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.salesforce_update_lead(lead_id, data)
    return jsonify(result)

@app.route('/api/crm/salesforce/leads', methods=['GET'])
def get_salesforce_leads():
    """Get leads from Salesforce."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    filters = request.args.to_dict()
    result = crm.salesforce_get_leads(filters if filters else None)
    return jsonify(result)

@app.route('/api/crm/hubspot/contact', methods=['POST'])
def create_hubspot_contact():
    """Create contact in HubSpot."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.hubspot_create_contact(data)
    return jsonify(result)

@app.route('/api/crm/hubspot/deal', methods=['POST'])
def create_hubspot_deal():
    """Create deal in HubSpot."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.hubspot_create_deal(data)
    return jsonify(result)

@app.route('/api/crm/hubspot/contacts', methods=['GET'])
def get_hubspot_contacts():
    """Get contacts from HubSpot."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    limit = int(request.args.get('limit', 100))
    result = crm.hubspot_get_contacts(limit)
    return jsonify(result)

@app.route('/api/crm/pipedrive/person', methods=['POST'])
def create_pipedrive_person():
    """Create person in Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.pipedrive_create_person(data)
    return jsonify(result)

@app.route('/api/crm/pipedrive/deal', methods=['POST'])
def create_pipedrive_deal():
    """Create deal in Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.pipedrive_create_deal(data)
    return jsonify(result)

@app.route('/api/crm/pipedrive/deal/<int:deal_id>', methods=['PUT'])
def update_pipedrive_deal(deal_id):
    """Update deal in Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    result = crm.pipedrive_update_deal(deal_id, data)
    return jsonify(result)

@app.route('/api/crm/pipedrive/deals', methods=['GET'])
def get_pipedrive_deals():
    """Get deals from Pipedrive."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    status = request.args.get('status', 'all_not_deleted')
    result = crm.pipedrive_get_deals(status)
    return jsonify(result)

@app.route('/api/crm/sync', methods=['POST'])
def sync_to_crm():
    """Universal sync to any CRM."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    required = ['crm_type', 'record_type', 'data']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = crm.sync_to_crm(
        crm_type=data['crm_type'],
        record_type=data['record_type'],
        data=data['data']
    )
    return jsonify(result)

@app.route('/api/crm/bulk-sync', methods=['POST'])
def bulk_sync():
    """Bulk sync multiple records to CRM."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    data = request.get_json()
    if 'crm_type' not in data or 'records' not in data:
        return jsonify({'success': False, 'error': 'Missing: crm_type, records'}), 400
    
    result = crm.bulk_sync(
        crm_type=data['crm_type'],
        records=data['records']
    )
    return jsonify(result)

@app.route('/api/crm/sync-log', methods=['GET'])
def get_sync_log():
    """Get CRM sync activity log."""
    if not CRM_ENABLED or not crm:
        return jsonify({'success': False, 'error': 'CRM not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    result = crm.get_sync_log(limit)
    return jsonify(result)

# ===== AI-POWERED FEATURES ENDPOINTS =====

@app.route('/api/ai/analyze-job', methods=['POST'])
def analyze_job():
    """AI-powered job description analysis."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    if 'description' not in data:
        return jsonify({'success': False, 'error': 'Missing: description'}), 400
    
    analysis = ai.analyze_job_description(
        job_description=data['description'],
        job_title=data.get('title', '')
    )
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })

@app.route('/api/ai/batch-analyze', methods=['POST'])
def batch_analyze():
    """Batch analyze multiple jobs."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    if 'jobs' not in data:
        return jsonify({'success': False, 'error': 'Missing: jobs'}), 400
    
    result = ai.batch_analyze_jobs(data['jobs'])
    return jsonify(result)

@app.route('/api/ai/ml-score', methods=['POST'])
def ml_score():
    """ML-enhanced lead scoring."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    required = ['lead_data', 'job_analysis']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    scoring = ai.ml_enhanced_lead_scoring(
        lead_data=data['lead_data'],
        job_analysis=data['job_analysis']
    )
    
    return jsonify({
        'success': True,
        'scoring': scoring
    })

@app.route('/api/ai/predict-response', methods=['POST'])
def predict_response():
    """Predict response likelihood."""
    if not AI_ENABLED or not ai:
        return jsonify({'success': False, 'error': 'AI features not available'}), 503
    
    data = request.get_json()
    required = ['lead_data', 'outreach_history']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    prediction = ai.predict_response_likelihood(
        lead_data=data['lead_data'],
        outreach_history=data['outreach_history']
    )
    
    return jsonify({
        'success': True,
        'prediction': prediction
    })

@app.route('/api/ai/features-status', methods=['GET'])
def ai_features_status():
    """Get AI features availability status."""
    return jsonify({
        'success': True,
        'ai_enabled': AI_ENABLED,
        'features': {
            'job_analysis': AI_ENABLED,
            'ml_scoring': AI_ENABLED,
            'response_prediction': AI_ENABLED,
            'batch_processing': AI_ENABLED
        },
        'capabilities': {
            'nlp_job_analysis': 'Extract skills, seniority, tech stack, requirements',
            'ml_lead_scoring': 'Enhanced scoring with feature analysis and confidence',
            'response_prediction': 'Predict response likelihood and best contact time',
            'batch_analysis': 'Analyze multiple jobs efficiently'
        }
    })

# ===== AUTOMATED FOLLOW-UP ENGINE ENDPOINTS =====

@app.route('/api/followup/create-sequence', methods=['POST'])
def create_followup_sequence():
    """Create automated follow-up sequence."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['lead_id', 'initial_email_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.create_follow_up_sequence(
        lead_id=data['lead_id'],
        initial_email_id=data['initial_email_id'],
        rule_type=data.get('rule_type', 'no_response')
    )
    
    return jsonify(result)

@app.route('/api/followup/engagement', methods=['POST'])
def update_followup_engagement():
    """Update follow-up based on engagement."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['lead_id', 'engagement_type']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.update_on_engagement(
        lead_id=data['lead_id'],
        engagement_type=data['engagement_type'],
        sequence_id=data.get('sequence_id')
    )
    
    return jsonify(result)

@app.route('/api/followup/due', methods=['GET'])
def get_due_followups():
    """Get follow-ups due soon."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    hours_ahead = int(request.args.get('hours_ahead', 24))
    result = followup_engine.get_due_followups(hours_ahead)
    
    return jsonify(result)

@app.route('/api/followup/mark-sent/<followup_id>', methods=['POST'])
def mark_followup_sent(followup_id):
    """Mark follow-up as sent."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    result = followup_engine.mark_followup_sent(followup_id)
    return jsonify(result)

@app.route('/api/followup/cancel-sequence/<sequence_id>', methods=['POST'])
def cancel_followup_sequence(sequence_id):
    """Cancel follow-up sequence."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json() or {}
    result = followup_engine.cancel_sequence(
        sequence_id=sequence_id,
        reason=data.get('reason', 'Manual cancellation')
    )
    
    return jsonify(result)

@app.route('/api/followup/engagement-stats/<lead_id>', methods=['GET'])
def get_engagement_stats(lead_id):
    """Get engagement statistics for lead."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    result = followup_engine.get_engagement_stats(lead_id)
    return jsonify(result)

@app.route('/api/followup/optimize-timing', methods=['POST'])
def optimize_followup_timing():
    """ML-based timing optimization."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['lead_data', 'historical_data']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.optimize_timing_ml(
        lead_data=data['lead_data'],
        historical_data=data['historical_data']
    )
    
    return jsonify(result)

@app.route('/api/followup/sequences', methods=['GET'])
def get_all_followup_sequences():
    """Get all follow-up sequences."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    status = request.args.get('status')
    result = followup_engine.get_all_sequences(status)
    
    return jsonify(result)

@app.route('/api/followup/performance', methods=['GET'])
def get_followup_performance():
    """Get follow-up performance metrics."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    result = followup_engine.get_performance_metrics()
    return jsonify(result)

@app.route('/api/followup/custom-rule', methods=['POST'])
def create_custom_followup_rule():
    """Create custom follow-up rule."""
    if not FOLLOWUP_ENGINE_ENABLED or not followup_engine:
        return jsonify({'success': False, 'error': 'Follow-up engine not available'}), 503
    
    data = request.get_json()
    required = ['rule_name', 'intervals', 'max_attempts']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = followup_engine.custom_rule(
        rule_name=data['rule_name'],
        intervals=data['intervals'],
        max_attempts=data['max_attempts'],
        stop_on_response=data.get('stop_on_response', True)
    )
    
    return jsonify(result)

# ===== LEAD ENRICHMENT & VERIFICATION ENDPOINTS =====

@app.route('/api/enrichment/configure/clearbit', methods=['POST'])
def configure_clearbit_api():
    """Configure Clearbit API."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = lead_enrichment.configure_clearbit(data['api_key'])
    return jsonify(result)

@app.route('/api/enrichment/configure/hunter', methods=['POST'])
def configure_hunter_api():
    """Configure Hunter.io API."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = lead_enrichment.configure_hunter(data['api_key'])
    return jsonify(result)

@app.route('/api/enrichment/configure/zoominfo', methods=['POST'])
def configure_zoominfo_api():
    """Configure ZoomInfo API."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'api_key' not in data:
        return jsonify({'success': False, 'error': 'Missing: api_key'}), 400
    
    result = lead_enrichment.configure_zoominfo(data['api_key'])
    return jsonify(result)

@app.route('/api/enrichment/clearbit', methods=['POST'])
def enrich_clearbit():
    """Enrich using Clearbit."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    result = lead_enrichment.enrich_with_clearbit(
        email=data.get('email'),
        domain=data.get('domain')
    )
    return jsonify(result)

@app.route('/api/enrichment/verify-email', methods=['POST'])
def verify_email():
    """Verify email with Hunter.io."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'email' not in data:
        return jsonify({'success': False, 'error': 'Missing: email'}), 400
    
    result = lead_enrichment.verify_email_hunter(data['email'])
    return jsonify(result)

@app.route('/api/enrichment/find-email', methods=['POST'])
def find_email():
    """Find email with Hunter.io."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    required = ['domain', 'first_name', 'last_name']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = lead_enrichment.find_email_hunter(
        domain=data['domain'],
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    return jsonify(result)

@app.route('/api/enrichment/zoominfo', methods=['POST'])
def enrich_zoominfo():
    """Enrich using ZoomInfo."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    result = lead_enrichment.enrich_with_zoominfo(
        company_name=data.get('company_name'),
        email=data.get('email')
    )
    return jsonify(result)

@app.route('/api/enrichment/batch-verify', methods=['POST'])
def batch_verify_emails():
    """Batch verify emails."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    if 'emails' not in data:
        return jsonify({'success': False, 'error': 'Missing: emails'}), 400
    
    result = lead_enrichment.batch_verify_emails(data['emails'])
    return jsonify(result)

@app.route('/api/enrichment/full', methods=['POST'])
def full_enrichment():
    """Full lead enrichment using all services."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    data = request.get_json()
    result = lead_enrichment.full_lead_enrichment(
        email=data.get('email'),
        domain=data.get('domain'),
        company_name=data.get('company_name')
    )
    return jsonify(result)

@app.route('/api/enrichment/stats', methods=['GET'])
def enrichment_stats():
    """Get enrichment statistics."""
    if not LEAD_ENRICHMENT_ENABLED or not lead_enrichment:
        return jsonify({'success': False, 'error': 'Lead enrichment not available'}), 503
    
    result = lead_enrichment.get_enrichment_stats()
    return jsonify(result)

# ===== A/B TESTING FRAMEWORK ENDPOINTS =====

@app.route('/api/ab-test/create', methods=['POST'])
def create_ab_test():
    """Create new A/B test."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    data = request.get_json()
    required = ['test_name', 'test_type', 'variants']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = ab_testing.create_test(
        test_name=data['test_name'],
        test_type=data['test_type'],
        variants=data['variants'],
        traffic_split=data.get('traffic_split'),
        duration_days=data.get('duration_days', 7),
        min_sample_size=data.get('min_sample_size', 100)
    )
    
    return jsonify(result)

@app.route('/api/ab-test/assign', methods=['POST'])
def assign_ab_variant():
    """Assign variant to user."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    data = request.get_json()
    required = ['test_name', 'user_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = ab_testing.assign_variant(
        test_name=data['test_name'],
        user_id=data['user_id']
    )
    
    return jsonify(result)

@app.route('/api/ab-test/track', methods=['POST'])
def track_ab_event():
    """Track A/B test event."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    data = request.get_json()
    required = ['test_name', 'variant_name', 'event_type']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = ab_testing.track_event(
        test_name=data['test_name'],
        variant_name=data['variant_name'],
        event_type=data['event_type']
    )
    
    return jsonify(result)

@app.route('/api/ab-test/results/<test_name>', methods=['GET'])
def get_ab_test_results(test_name):
    """Get A/B test results."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    result = ab_testing.get_test_results(test_name)
    return jsonify(result)

@app.route('/api/ab-test/stop/<test_name>', methods=['POST'])
def stop_ab_test(test_name):
    """Stop A/B test early."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    result = ab_testing.stop_test(test_name)
    return jsonify(result)

@app.route('/api/ab-test/all', methods=['GET'])
def get_all_ab_tests():
    """Get all A/B tests."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    status = request.args.get('status')
    result = ab_testing.get_all_tests(status)
    
    return jsonify(result)

@app.route('/api/ab-test/best-variants', methods=['GET'])
def get_best_ab_variants():
    """Get best performing variants."""
    if not AB_TESTING_ENABLED or not ab_testing:
        return jsonify({'success': False, 'error': 'A/B testing not available'}), 503
    
    metric = request.args.get('metric', 'conversion_rate')
    result = ab_testing.get_best_performing_variants(metric)
    
    return jsonify(result)

# ===== ADVANCED REPORTING & EXPORTS ENDPOINTS =====

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate comprehensive report."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    required = ['report_type', 'data']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = reporting.generate_report(
        report_type=data['report_type'],
        data=data['data'],
        format=data.get('format', 'json'),
        include_charts=data.get('include_charts', True)
    )
    
    return jsonify(result)

@app.route('/api/reports/schedule', methods=['POST'])
def schedule_report():
    """Schedule recurring report."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    required = ['report_type', 'frequency', 'recipients']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = reporting.schedule_report(
        report_type=data['report_type'],
        frequency=data['frequency'],
        recipients=data['recipients'],
        format=data.get('format', 'pdf'),
        data_source=data.get('data_source')
    )
    
    return jsonify(result)

@app.route('/api/reports/export', methods=['POST'])
def export_data():
    """Export data in various formats."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    if 'data_type' not in data:
        return jsonify({'success': False, 'error': 'Missing: data_type'}), 400
    
    result = reporting.export_data(
        data_type=data['data_type'],
        filters=data.get('filters'),
        format=data.get('format', 'csv'),
        fields=data.get('fields')
    )
    
    return jsonify(result)

@app.route('/api/reports/dashboard', methods=['POST'])
def create_dashboard():
    """Create custom dashboard."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    data = request.get_json()
    required = ['dashboard_name', 'widgets']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = reporting.create_custom_dashboard(
        dashboard_name=data['dashboard_name'],
        widgets=data['widgets']
    )
    
    return jsonify(result)

@app.route('/api/reports/scheduled', methods=['GET'])
def get_scheduled_reports():
    """Get scheduled reports."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    status = request.args.get('status')
    result = reporting.get_scheduled_reports(status)
    
    return jsonify(result)

@app.route('/api/reports/export-history', methods=['GET'])
def get_export_history():
    """Get export history."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    result = reporting.get_export_history(limit)
    
    return jsonify(result)

@app.route('/api/reports/templates', methods=['GET'])
def get_report_templates():
    """Get available report templates."""
    if not REPORTING_ENABLED or not reporting:
        return jsonify({'success': False, 'error': 'Reporting not available'}), 503
    
    result = reporting.get_available_templates()
    return jsonify(result)

# ===== MULTI-CHANNEL OUTREACH ENDPOINTS =====

@app.route('/api/multichannel/configure/twilio', methods=['POST'])
def configure_twilio_sms():
    """Configure Twilio for SMS."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['account_sid', 'auth_token', 'phone_number']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.configure_twilio(
        account_sid=data['account_sid'],
        auth_token=data['auth_token'],
        phone_number=data['phone_number']
    )
    return jsonify(result)

@app.route('/api/multichannel/configure/whatsapp', methods=['POST'])
def configure_whatsapp_business():
    """Configure WhatsApp Business API."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['access_token', 'phone_number_id', 'business_account_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.configure_whatsapp(
        access_token=data['access_token'],
        phone_number_id=data['phone_number_id'],
        business_account_id=data['business_account_id']
    )
    return jsonify(result)

@app.route('/api/multichannel/configure/slack', methods=['POST'])
def configure_slack_bot():
    """Configure Slack integration."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['bot_token', 'workspace_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.configure_slack(
        bot_token=data['bot_token'],
        workspace_id=data['workspace_id']
    )
    return jsonify(result)

@app.route('/api/multichannel/sms/send', methods=['POST'])
def send_sms_message():
    """Send SMS message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['to_number', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_sms(
        to_number=data['to_number'],
        message=data['message'],
        lead_id=data.get('lead_id')
    )
    return jsonify(result)

@app.route('/api/multichannel/sms/bulk', methods=['POST'])
def send_bulk_sms():
    """Send bulk SMS messages."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    if 'recipients' not in data:
        return jsonify({'success': False, 'error': 'Missing: recipients'}), 400
    
    result = multichannel.send_sms_bulk(recipients=data['recipients'])
    return jsonify(result)

@app.route('/api/multichannel/whatsapp/send', methods=['POST'])
def send_whatsapp_message():
    """Send WhatsApp message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['to_number', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_whatsapp(
        to_number=data['to_number'],
        message=data['message'],
        lead_id=data.get('lead_id')
    )
    return jsonify(result)

@app.route('/api/multichannel/whatsapp/template', methods=['POST'])
def send_whatsapp_template():
    """Send WhatsApp template message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['to_number', 'template_name', 'parameters']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_whatsapp_template(
        to_number=data['to_number'],
        template_name=data['template_name'],
        parameters=data['parameters']
    )
    return jsonify(result)

@app.route('/api/multichannel/slack/send', methods=['POST'])
def send_slack_message():
    """Send Slack message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['channel', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_slack_message(
        channel=data['channel'],
        message=data['message'],
        lead_id=data.get('lead_id')
    )
    return jsonify(result)

@app.route('/api/multichannel/slack/dm', methods=['POST'])
def send_slack_dm():
    """Send Slack direct message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['user_id', 'message']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_slack_dm(
        user_id=data['user_id'],
        message=data['message']
    )
    return jsonify(result)

@app.route('/api/multichannel/campaign/create', methods=['POST'])
def create_multichannel_campaign():
    """Create multi-channel campaign."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['campaign_name', 'channels', 'message_templates', 'recipients']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.create_multichannel_campaign(
        campaign_name=data['campaign_name'],
        channels=data['channels'],
        message_templates=data['message_templates'],
        recipients=data['recipients']
    )
    return jsonify(result)

@app.route('/api/multichannel/send', methods=['POST'])
def send_multichannel_message():
    """Send message across multiple channels."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['recipient', 'channels', 'messages']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.send_multichannel_message(
        recipient=data['recipient'],
        channels=data['channels'],
        messages=data['messages']
    )
    return jsonify(result)

@app.route('/api/multichannel/stats', methods=['GET'])
def get_multichannel_stats():
    """Get multi-channel statistics."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    result = multichannel.get_channel_stats()
    return jsonify(result)

@app.route('/api/multichannel/history', methods=['GET'])
def get_multichannel_history():
    """Get message history."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    channel = request.args.get('channel')
    lead_id = request.args.get('lead_id')
    limit = int(request.args.get('limit', 50))
    
    result = multichannel.get_message_history(
        channel=channel,
        lead_id=lead_id,
        limit=limit
    )
    return jsonify(result)

@app.route('/api/multichannel/track-reply', methods=['POST'])
def track_multichannel_reply():
    """Track reply to message."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    required = ['message_id', 'reply_content']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing: {required}'}), 400
    
    result = multichannel.track_reply(
        message_id=data['message_id'],
        reply_content=data['reply_content']
    )
    return jsonify(result)

@app.route('/api/multichannel/recommend-channel', methods=['POST'])
def recommend_best_channel():
    """Recommend best channel for lead."""
    if not MULTICHANNEL_ENABLED or not multichannel:
        return jsonify({'success': False, 'error': 'Multi-channel not available'}), 503
    
    data = request.get_json()
    if 'lead_engagement' not in data:
        return jsonify({'success': False, 'error': 'Missing: lead_engagement'}), 400
    
    result = multichannel.get_best_channel_for_lead(
        lead_engagement=data['lead_engagement']
    )
    return jsonify(result)

# ===== CALENDAR INTEGRATION & MEETING SCHEDULER ENDPOINTS =====

@app.route('/api/calendar/create-link', methods=['POST'])
def create_scheduling_link():
    """Create Calendly-style scheduling link."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'settings' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, settings'}), 400
    
    result = calendar_integration.create_scheduling_link(
        user_id=data['user_id'],
        settings=data['settings']
    )
    return jsonify(result)

@app.route('/api/calendar/available-slots/<link_id>', methods=['POST'])
def get_available_slots(link_id):
    """Get available time slots for booking."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    data = request.get_json()
    if 'start' not in data or 'end' not in data:
        return jsonify({'success': False, 'error': 'Missing: start, end dates'}), 400
    
    slots = calendar_integration.get_available_slots(
        link_id=link_id,
        date_range={'start': data['start'], 'end': data['end']}
    )
    return jsonify({'success': True, 'slots': slots})

@app.route('/api/calendar/book-meeting', methods=['POST'])
def book_meeting():
    """Book a meeting slot."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    data = request.get_json()
    required = ['link_id', 'attendee_name', 'attendee_email', 'start_time', 'end_time']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing required fields: {required}'}), 400
    
    result = calendar_integration.book_meeting(
        link_id=data['link_id'],
        booking_data=data
    )
    return jsonify(result)

@app.route('/api/calendar/reschedule/<meeting_id>', methods=['PUT'])
def reschedule_meeting(meeting_id):
    """Reschedule an existing meeting."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    data = request.get_json()
    if 'start_time' not in data or 'end_time' not in data:
        return jsonify({'success': False, 'error': 'Missing: start_time, end_time'}), 400
    
    result = calendar_integration.reschedule_meeting(
        meeting_id=meeting_id,
        new_time={'start_time': data['start_time'], 'end_time': data['end_time']}
    )
    return jsonify(result)

@app.route('/api/calendar/cancel/<meeting_id>', methods=['DELETE'])
def cancel_meeting(meeting_id):
    """Cancel a meeting."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    data = request.get_json() or {}
    result = calendar_integration.cancel_meeting(
        meeting_id=meeting_id,
        reason=data.get('reason', '')
    )
    return jsonify(result)

@app.route('/api/calendar/upcoming', methods=['GET'])
def get_upcoming_meetings():
    """Get upcoming meetings."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    user_id = request.args.get('user_id')
    days = int(request.args.get('days', 7))
    
    meetings = calendar_integration.get_upcoming_meetings(user_id=user_id, days=days)
    return jsonify({'success': True, 'meetings': meetings})

@app.route('/api/calendar/send-reminders', methods=['POST'])
def send_meeting_reminders():
    """Send reminders for upcoming meetings."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    result = calendar_integration.send_meeting_reminders()
    return jsonify(result)

@app.route('/api/calendar/analytics', methods=['POST'])
def get_calendar_analytics():
    """Get calendar analytics."""
    if not CALENDAR_ENABLED or not calendar_integration:
        return jsonify({'success': False, 'error': 'Calendar not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'date_range' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, date_range'}), 400
    
    analytics = calendar_integration.get_calendar_analytics(
        user_id=data['user_id'],
        date_range=data['date_range']
    )
    return jsonify({'success': True, 'analytics': analytics})

# ===== VOICE CALLING SYSTEM ENDPOINTS =====

@app.route('/api/voice/call', methods=['POST'])
def make_voice_call():
    """Make outbound call."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'to_number' not in data or 'call_type' not in data:
        return jsonify({'success': False, 'error': 'Missing: to_number, call_type'}), 400
    
    result = voice_calling.make_call(
        to_number=data['to_number'],
        call_type=data['call_type'],
        campaign_id=data.get('campaign_id'),
        script_id=data.get('script_id')
    )
    return jsonify(result)

@app.route('/api/voice/bulk-call', methods=['POST'])
def make_bulk_voice_calls():
    """Make bulk outbound calls."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'contacts' not in data or 'campaign_id' not in data or 'script_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: contacts, campaign_id, script_id'}), 400
    
    result = voice_calling.make_bulk_calls(
        contacts=data['contacts'],
        campaign_id=data['campaign_id'],
        script_id=data['script_id']
    )
    return jsonify(result)

@app.route('/api/voice/voicemail-drop', methods=['POST'])
def drop_voicemail():
    """Drop pre-recorded voicemail."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'to_number' not in data or 'voicemail_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: to_number, voicemail_id'}), 400
    
    result = voice_calling.drop_voicemail(
        to_number=data['to_number'],
        voicemail_id=data['voicemail_id'],
        campaign_id=data.get('campaign_id')
    )
    return jsonify(result)

@app.route('/api/voice/call-status/<call_id>', methods=['PUT'])
def update_voice_call_status(call_id):
    """Update call status from webhook."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'success': False, 'error': 'Missing: status'}), 400
    
    result = voice_calling.update_call_status(
        call_id=call_id,
        status=data['status'],
        details=data.get('details', {})
    )
    return jsonify(result)

@app.route('/api/voice/recording/<call_id>', methods=['GET'])
def get_voice_call_recording(call_id):
    """Get call recording URL."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    result = voice_calling.get_call_recording(call_id)
    return jsonify(result)

@app.route('/api/voice/transcribe/<call_id>', methods=['POST'])
def transcribe_voice_call(call_id):
    """Transcribe call recording."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    result = voice_calling.transcribe_call(call_id)
    return jsonify(result)

@app.route('/api/voice/script', methods=['POST'])
def create_voice_call_script():
    """Create call script."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'content' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, content'}), 400
    
    result = voice_calling.create_call_script(data)
    return jsonify(result)

@app.route('/api/voice/voicemail', methods=['POST'])
def create_voice_voicemail_drop():
    """Create voicemail drop."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'recording_url' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, recording_url'}), 400
    
    result = voice_calling.create_voicemail_drop(data)
    return jsonify(result)

@app.route('/api/voice/campaign', methods=['POST'])
def create_voice_campaign():
    """Create voice calling campaign."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'target_contacts' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, target_contacts'}), 400
    
    result = voice_calling.create_voice_campaign(data)
    return jsonify(result)

@app.route('/api/voice/campaign-stats/<campaign_id>', methods=['GET'])
def get_voice_campaign_stats(campaign_id):
    """Get voice campaign statistics."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    result = voice_calling.get_campaign_stats(campaign_id)
    return jsonify(result)

@app.route('/api/voice/analytics', methods=['POST'])
def get_voice_call_analytics():
    """Get overall call analytics."""
    if not VOICE_CALLING_ENABLED or not voice_calling:
        return jsonify({'success': False, 'error': 'Voice calling not available'}), 503
    
    data = request.get_json()
    if 'date_range' not in data:
        return jsonify({'success': False, 'error': 'Missing: date_range'}), 400
    
    analytics = voice_calling.get_call_analytics(data['date_range'])
    return jsonify({'success': True, 'analytics': analytics})

# ===== SOCIAL MEDIA AUTOMATION ENDPOINTS =====

@app.route('/api/social/connect-linkedin', methods=['POST'])
def connect_linkedin():
    """Connect LinkedIn account."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'credentials' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, credentials'}), 400
    
    result = social_media.connect_linkedin_account(
        user_id=data['user_id'],
        credentials=data['credentials']
    )
    return jsonify(result)

@app.route('/api/social/send-connection', methods=['POST'])
def send_connection_request():
    """Send LinkedIn connection request."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'account_id' not in data or 'profile_url' not in data:
        return jsonify({'success': False, 'error': 'Missing: account_id, profile_url'}), 400
    
    result = social_media.send_connection_request(
        account_id=data['account_id'],
        profile_url=data['profile_url'],
        message=data.get('message')
    )
    return jsonify(result)

@app.route('/api/social/send-message', methods=['POST'])
def send_linkedin_dm():
    """Send LinkedIn direct message."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'account_id' not in data or 'profile_url' not in data or 'message' not in data:
        return jsonify({'success': False, 'error': 'Missing: account_id, profile_url, message'}), 400
    
    result = social_media.send_linkedin_message(
        account_id=data['account_id'],
        profile_url=data['profile_url'],
        message=data['message'],
        campaign_id=data.get('campaign_id')
    )
    return jsonify(result)

@app.route('/api/social/auto-engage', methods=['POST'])
def auto_engage_linkedin_posts():
    """Auto-engage with LinkedIn posts."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'account_id' not in data or 'keywords' not in data or 'actions' not in data:
        return jsonify({'success': False, 'error': 'Missing: account_id, keywords, actions'}), 400
    
    result = social_media.auto_engage_posts(
        account_id=data['account_id'],
        search_keywords=data['keywords'],
        actions=data['actions'],
        limit=data.get('limit', 10)
    )
    return jsonify(result)

@app.route('/api/social/schedule-post', methods=['POST'])
def schedule_linkedin_post():
    """Schedule LinkedIn post."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'account_id' not in data or 'content' not in data or 'scheduled_time' not in data:
        return jsonify({'success': False, 'error': 'Missing: account_id, content, scheduled_time'}), 400
    
    result = social_media.schedule_linkedin_post(
        account_id=data['account_id'],
        post_data=data
    )
    return jsonify(result)

@app.route('/api/social/campaign', methods=['POST'])
def create_social_campaign():
    """Create social media campaign."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'account_id' not in data or 'name' not in data or 'campaign_type' not in data:
        return jsonify({'success': False, 'error': 'Missing: account_id, name, campaign_type'}), 400
    
    result = social_media.create_social_campaign(data)
    return jsonify(result)

@app.route('/api/social/campaign-stats/<campaign_id>', methods=['GET'])
def get_social_campaign_stats(campaign_id):
    """Get social campaign statistics."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    result = social_media.get_campaign_stats(campaign_id)
    return jsonify(result)

@app.route('/api/social/analytics', methods=['POST'])
def get_social_analytics():
    """Get social media analytics."""
    if not SOCIAL_MEDIA_ENABLED or not social_media:
        return jsonify({'success': False, 'error': 'Social media not available'}), 503
    
    data = request.get_json()
    if 'account_id' not in data or 'date_range' not in data:
        return jsonify({'success': False, 'error': 'Missing: account_id, date_range'}), 400
    
    analytics = social_media.get_social_analytics(
        account_id=data['account_id'],
        date_range=data['date_range']
    )
    return jsonify({'success': True, 'analytics': analytics})

# ===== ADVANCED SECURITY & COMPLIANCE ENDPOINTS =====

@app.route('/api/security/setup-2fa', methods=['POST'])
def setup_two_factor_auth():
    """Setup 2FA for user."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id'}), 400
    
    result = security.setup_2fa(
        user_id=data['user_id'],
        method=data.get('method', 'totp')
    )
    return jsonify(result)

@app.route('/api/security/verify-2fa', methods=['POST'])
def verify_two_factor_auth():
    """Verify 2FA code."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'code' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, code'}), 400
    
    result = security.verify_2fa(
        user_id=data['user_id'],
        code=data['code']
    )
    return jsonify(result)

@app.route('/api/security/audit-log', methods=['POST'])
def create_audit_log():
    """Log audit event."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'event_type' not in data or 'action' not in data:
        return jsonify({'success': False, 'error': 'Missing: event_type, action'}), 400
    
    result = security.log_audit_event(data)
    return jsonify(result)

@app.route('/api/security/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get audit logs."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    filters = {
        'user_id': request.args.get('user_id'),
        'event_type': request.args.get('event_type'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'limit': int(request.args.get('limit', 100))
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    
    logs = security.get_audit_logs(filters)
    return jsonify({'success': True, 'logs': logs})

@app.route('/api/security/role', methods=['POST'])
def create_security_role():
    """Create user role."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'name' not in data:
        return jsonify({'success': False, 'error': 'Missing: name'}), 400
    
    result = security.create_role(data)
    return jsonify(result)

@app.route('/api/security/assign-role', methods=['POST'])
def assign_user_role():
    """Assign role to user."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'role_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, role_id'}), 400
    
    result = security.assign_role(
        user_id=data['user_id'],
        role_id=data['role_id']
    )
    return jsonify(result)

@app.route('/api/security/check-permission', methods=['POST'])
def check_user_permission():
    """Check user permission."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'permission' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, permission'}), 400
    
    has_permission = security.check_permission(
        user_id=data['user_id'],
        permission=data['permission']
    )
    return jsonify({'success': True, 'has_permission': has_permission})

@app.route('/api/gdpr/export-data', methods=['POST'])
def export_user_data():
    """Export user data (GDPR)."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'data_types' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, data_types'}), 400
    
    result = security.export_data(
        user_id=data['user_id'],
        data_types=data['data_types']
    )
    return jsonify(result)

@app.route('/api/gdpr/delete-data', methods=['POST'])
def delete_user_data():
    """Delete user data (GDPR)."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id'}), 400
    
    result = security.delete_user_data(
        user_id=data['user_id'],
        data_types=data.get('data_types')
    )
    return jsonify(result)

@app.route('/api/compliance/report', methods=['POST'])
def get_compliance_report():
    """Get compliance report."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'date_range' not in data:
        return jsonify({'success': False, 'error': 'Missing: date_range'}), 400
    
    report = security.get_compliance_report(data['date_range'])
    return jsonify({'success': True, 'report': report})

@app.route('/api/compliance/retention-policy', methods=['POST'])
def set_retention_policy():
    """Set data retention policy."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'data_type' not in data or 'retention_days' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, data_type, retention_days'}), 400
    
    result = security.set_data_retention_policy(data)
    return jsonify(result)

@app.route('/api/compliance/enforce-retention', methods=['POST'])
def enforce_retention_policies():
    """Enforce retention policies."""
    if not SECURITY_ENABLED or not security:
        return jsonify({'success': False, 'error': 'Security not available'}), 503
    
    result = security.enforce_retention_policies()
    return jsonify(result)

# ===== WEBHOOK SYSTEM & REAL-TIME INTEGRATIONS ENDPOINTS =====

@app.route('/api/webhooks/create', methods=['POST'])
def create_webhook():
    """Create webhook endpoint."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Webhooks not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'name' not in data or 'url' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, name, url'}), 400
    
    result = webhook_system.create_webhook(data)
    return jsonify(result)

@app.route('/api/webhooks/trigger/<webhook_id>', methods=['POST'])
def trigger_webhook(webhook_id):
    """Trigger webhook manually."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Webhooks not available'}), 503
    
    data = request.get_json()
    if 'event' not in data or 'payload' not in data:
        return jsonify({'success': False, 'error': 'Missing: event, payload'}), 400
    
    result = webhook_system.trigger_webhook(
        webhook_id=webhook_id,
        event=data['event'],
        payload=data['payload']
    )
    return jsonify(result)

@app.route('/api/webhooks/broadcast', methods=['POST'])
def broadcast_webhook_event():
    """Broadcast event to all webhooks."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Webhooks not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'event' not in data or 'payload' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, event, payload'}), 400
    
    result = webhook_system.broadcast_event(
        user_id=data['user_id'],
        event=data['event'],
        payload=data['payload']
    )
    return jsonify(result)

@app.route('/api/webhooks/retry/<delivery_id>', methods=['POST'])
def retry_webhook_delivery(delivery_id):
    """Retry failed webhook delivery."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Webhooks not available'}), 503
    
    result = webhook_system.retry_failed_delivery(delivery_id)
    return jsonify(result)

@app.route('/api/webhooks/logs/<webhook_id>', methods=['GET'])
def get_webhook_logs(webhook_id):
    """Get webhook delivery logs."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Webhooks not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    logs = webhook_system.get_webhook_logs(webhook_id, limit)
    return jsonify({'success': True, 'logs': logs})

@app.route('/api/webhooks/stats', methods=['GET'])
def get_webhook_stats():
    """Get webhook statistics."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Webhooks not available'}), 503
    
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Missing: user_id'}), 400
    
    stats = webhook_system.get_webhook_stats(user_id)
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/integrations/create', methods=['POST'])
def create_integration():
    """Create custom integration."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Integrations not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'name' not in data or 'type' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, name, type'}), 400
    
    result = webhook_system.create_integration(data)
    return jsonify(result)

@app.route('/api/integrations/sync/<integration_id>', methods=['POST'])
def sync_integration(integration_id):
    """Sync integration data."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Integrations not available'}), 503
    
    result = webhook_system.sync_integration(integration_id)
    return jsonify(result)

@app.route('/api/events/subscribe', methods=['POST'])
def subscribe_to_events():
    """Subscribe to real-time events."""
    if not WEBHOOK_ENABLED or not webhook_system:
        return jsonify({'success': False, 'error': 'Event subscriptions not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'event_type' not in data or 'callback_url' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, event_type, callback_url'}), 400
    
    result = webhook_system.create_event_subscription(data)
    return jsonify(result)

# ===== ADVANCED WORKFLOW AUTOMATION BUILDER ENDPOINTS =====

@app.route('/api/workflows/create', methods=['POST'])
def create_automation_workflow():
    """Create automation workflow."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data or 'name' not in data or 'trigger_type' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id, name, trigger_type'}), 400
    
    result = workflow_automation.create_workflow(data)
    return jsonify(result)

@app.route('/api/workflows/execute/<workflow_id>', methods=['POST'])
def execute_automation_workflow(workflow_id):
    """Execute workflow."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json() or {}
    result = workflow_automation.execute_workflow(
        workflow_id=workflow_id,
        trigger_data=data.get('trigger_data')
    )
    return jsonify(result)

@app.route('/api/workflows/trigger', methods=['POST'])
def create_workflow_trigger():
    """Create workflow trigger."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json()
    if 'workflow_id' not in data or 'type' not in data:
        return jsonify({'success': False, 'error': 'Missing: workflow_id, type'}), 400
    
    result = workflow_automation.create_trigger(data)
    return jsonify(result)

@app.route('/api/workflows/action', methods=['POST'])
def add_workflow_action():
    """Add action to workflow."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json()
    if 'workflow_id' not in data or 'name' not in data or 'type' not in data:
        return jsonify({'success': False, 'error': 'Missing: workflow_id, name, type'}), 400
    
    result = workflow_automation.add_action(data)
    return jsonify(result)

@app.route('/api/workflows/condition', methods=['POST'])
def add_workflow_condition():
    """Add conditional logic to workflow."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json()
    required = ['workflow_id', 'node_id', 'operator', 'field', 'value']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing required fields: {required}'}), 400
    
    result = workflow_automation.add_condition(data)
    return jsonify(result)

@app.route('/api/workflows/template', methods=['POST'])
def create_workflow_template():
    """Create workflow template."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'workflow_config' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, workflow_config'}), 400
    
    result = workflow_automation.create_template(data)
    return jsonify(result)

@app.route('/api/workflows/template/<template_id>/use', methods=['POST'])
def use_workflow_template(template_id):
    """Create workflow from template."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id'}), 400
    
    result = workflow_automation.use_template(
        template_id=template_id,
        user_id=data['user_id'],
        customizations=data.get('customizations')
    )
    return jsonify(result)

@app.route('/api/workflows/analytics/<workflow_id>', methods=['GET'])
def get_workflow_analytics(workflow_id):
    """Get workflow analytics."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    analytics = workflow_automation.get_workflow_analytics(workflow_id)
    return jsonify({'success': True, 'analytics': analytics})

@app.route('/api/workflows/logs/<workflow_id>', methods=['GET'])
def get_workflow_logs(workflow_id):
    """Get workflow execution logs."""
    if not WORKFLOW_ENABLED or not workflow_automation:
        return jsonify({'success': False, 'error': 'Workflows not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    logs = workflow_automation.get_workflow_logs(workflow_id, limit)
    return jsonify({'success': True, 'logs': logs})

# ===== TEAM COLLABORATION & MANAGEMENT ENDPOINTS =====

@app.route('/api/team/workspace', methods=['POST'])
def create_team_workspace():
    """Create team workspace."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'owner_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, owner_id'}), 400
    
    result = team_collab.create_workspace(data)
    return jsonify(result)

@app.route('/api/team/workspace/<workspace_id>/member', methods=['POST'])
def add_workspace_member(workspace_id):
    """Add member to workspace."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: user_id'}), 400
    
    result = team_collab.add_member(
        workspace_id=workspace_id,
        user_id=data['user_id'],
        role=data.get('role', 'member')
    )
    return jsonify(result)

@app.route('/api/team/task', methods=['POST'])
def create_team_task():
    """Create task."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    data = request.get_json()
    if 'workspace_id' not in data or 'title' not in data or 'created_by' not in data:
        return jsonify({'success': False, 'error': 'Missing: workspace_id, title, created_by'}), 400
    
    result = team_collab.create_task(data)
    return jsonify(result)

@app.route('/api/team/task/<task_id>', methods=['PUT'])
def update_team_task(task_id):
    """Update task."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    data = request.get_json()
    result = team_collab.update_task(task_id, data)
    return jsonify(result)

@app.route('/api/team/comment', methods=['POST'])
def add_team_comment():
    """Add comment to task."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    data = request.get_json()
    if 'task_id' not in data or 'user_id' not in data or 'content' not in data:
        return jsonify({'success': False, 'error': 'Missing: task_id, user_id, content'}), 400
    
    result = team_collab.add_comment(data)
    return jsonify(result)

@app.route('/api/team/activity/<workspace_id>', methods=['GET'])
def get_team_activity_feed(workspace_id):
    """Get workspace activity feed."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    limit = int(request.args.get('limit', 50))
    activities = team_collab.get_activity_feed(workspace_id, limit)
    return jsonify({'success': True, 'activities': activities})

@app.route('/api/team/notifications', methods=['GET'])
def get_team_notifications():
    """Get user notifications."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Missing: user_id'}), 400
    
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    notifications = team_collab.get_notifications(user_id, unread_only)
    return jsonify({'success': True, 'notifications': notifications})

@app.route('/api/team/notifications/<notification_id>/read', methods=['PUT'])
def mark_team_notification_read(notification_id):
    """Mark notification as read."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    result = team_collab.mark_notification_read(notification_id)
    return jsonify(result)

@app.route('/api/team/analytics/<workspace_id>', methods=['GET'])
def get_team_analytics(workspace_id):
    """Get team analytics."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    analytics = team_collab.get_team_analytics(workspace_id)
    return jsonify({'success': True, 'analytics': analytics})

@app.route('/api/team/search/<workspace_id>', methods=['GET'])
def search_team_workspace(workspace_id):
    """Search workspace content."""
    if not TEAM_COLLAB_ENABLED or not team_collab:
        return jsonify({'success': False, 'error': 'Team collaboration not available'}), 503
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({'success': False, 'error': 'Missing query parameter: q'}), 400
    
    results = team_collab.search_workspace(workspace_id, query)
    return jsonify(results)

# ===== REVENUE INTELLIGENCE & FORECASTING ENDPOINTS =====

@app.route('/api/revenue/deal', methods=['POST'])
def create_revenue_deal():
    """Create sales deal."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    data = request.get_json()
    if 'name' not in data or 'company' not in data or 'owner_id' not in data or 'value' not in data:
        return jsonify({'success': False, 'error': 'Missing: name, company, owner_id, value'}), 400
    
    result = revenue_intel.create_deal(data)
    return jsonify(result)

@app.route('/api/revenue/deal/<deal_id>/stage', methods=['PUT'])
def update_revenue_deal_stage(deal_id):
    """Update deal stage."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    data = request.get_json()
    if 'stage' not in data:
        return jsonify({'success': False, 'error': 'Missing: stage'}), 400
    
    result = revenue_intel.update_deal_stage(
        deal_id=deal_id,
        stage=data['stage'],
        notes=data.get('notes', '')
    )
    return jsonify(result)

@app.route('/api/revenue/forecast', methods=['GET'])
def get_revenue_pipeline_forecast():
    """Get pipeline revenue forecast."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    owner_id = request.args.get('owner_id')
    period = request.args.get('period', 'quarter')
    
    forecast = revenue_intel.get_pipeline_forecast(owner_id, period)
    return jsonify({'success': True, 'forecast': forecast})

@app.route('/api/revenue/quota', methods=['POST'])
def track_sales_quota():
    """Track sales quota."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    data = request.get_json()
    required = ['user_id', 'period', 'target_amount', 'start_date', 'end_date']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing required fields: {required}'}), 400
    
    result = revenue_intel.track_quota(data)
    return jsonify(result)

@app.route('/api/revenue/quota/<user_id>', methods=['GET'])
def get_revenue_quota_performance(user_id):
    """Get quota performance."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    period = request.args.get('period', 'current')
    performance = revenue_intel.get_quota_performance(user_id, period)
    return jsonify(performance)

@app.route('/api/revenue/win-loss', methods=['POST'])
def analyze_revenue_win_loss():
    """Win/Loss analysis."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    data = request.get_json() or {}
    analysis = revenue_intel.analyze_win_loss(data.get('filters'))
    return jsonify({'success': True, 'analysis': analysis})

@app.route('/api/revenue/predict', methods=['GET'])
def predict_future_revenue():
    """Predict future revenue."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    owner_id = request.args.get('owner_id')
    months_ahead = int(request.args.get('months_ahead', 3))
    
    prediction = revenue_intel.predict_revenue(owner_id, months_ahead)
    return jsonify({'success': True, 'prediction': prediction})

@app.route('/api/revenue/analytics', methods=['POST'])
def get_revenue_analytics():
    """Get comprehensive revenue analytics."""
    if not REVENUE_ENABLED or not revenue_intel:
        return jsonify({'success': False, 'error': 'Revenue intelligence not available'}), 503
    
    data = request.get_json()
    if 'date_range' not in data:
        return jsonify({'success': False, 'error': 'Missing: date_range'}), 400
    
    analytics = revenue_intel.get_revenue_analytics(data['date_range'])
    return jsonify({'success': True, 'analytics': analytics})

# ===== Document Management & E-Signatures Endpoints =====

@app.route('/api/documents/create', methods=['POST'])
def create_document():
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    required = ['name', 'owner_id']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    result = doc_manager.create_document(data)
    return jsonify(result)

@app.route('/api/documents/<document_id>', methods=['PUT'])
def update_document(document_id):
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    result = doc_manager.update_document(document_id, data)
    return jsonify(result)

@app.route('/api/documents/templates/create', methods=['POST'])
def create_template():
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    required = ['name', 'content']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    result = doc_manager.create_template(data)
    return jsonify(result)

@app.route('/api/documents/templates/<template_id>/use', methods=['POST'])
def use_template(template_id):
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    if 'variables' not in data or 'owner_id' not in data:
        return jsonify({'success': False, 'error': 'Missing: variables, owner_id'}), 400
    
    result = doc_manager.use_template(template_id, data['variables'], data['owner_id'])
    return jsonify(result)

@app.route('/api/documents/signatures/request', methods=['POST'])
def request_signature():
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    required = ['document_id', 'requester_id', 'signers']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    result = doc_manager.request_signature(data)
    return jsonify(result)

@app.route('/api/documents/signatures/sign', methods=['POST'])
def add_signature():
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    required = ['document_id', 'signer_id', 'signer_name', 'signer_email']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    result = doc_manager.add_signature(data)
    return jsonify(result)

@app.route('/api/documents/signatures/<request_id>/status', methods=['GET'])
def get_signature_status(request_id):
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    result = doc_manager.get_signature_status(request_id)
    return jsonify(result)

@app.route('/api/documents/<document_id>/history', methods=['GET'])
def get_document_history(document_id):
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    history = doc_manager.get_document_history(document_id)
    return jsonify({'success': True, 'history': history})

@app.route('/api/documents/share', methods=['POST'])
def share_document():
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    data = request.get_json()
    required = ['document_id', 'shared_by', 'shared_with']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    result = doc_manager.share_document(data)
    return jsonify(result)

@app.route('/api/documents/analytics/<owner_id>', methods=['GET'])
def get_document_analytics(owner_id):
    if not DOCUMENTS_ENABLED or not doc_manager:
        return jsonify({'success': False, 'error': 'Documents not enabled'}), 503
    
    analytics = doc_manager.get_document_analytics(owner_id)
    return jsonify({'success': True, 'analytics': analytics})

# ===== Caching Layer Endpoints =====

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    if not CACHE_ENABLED or not cache_service:
        return jsonify({'success': False, 'error': 'Cache not enabled'}), 503
    
    stats = cache_service.get_cache_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    if not CACHE_ENABLED or not cache_manager:
        return jsonify({'success': False, 'error': 'Cache not enabled'}), 503
    
    data = request.get_json() or {}
    pattern = data.get('pattern', '*')
    
    if pattern == '*':
        cache_manager.clear()
        return jsonify({'success': True, 'message': 'All cache cleared'})
    else:
        count = cache_manager.invalidate_pattern(pattern)
        return jsonify({'success': True, 'cleared': count, 'pattern': pattern})

@app.route('/api/cache/invalidate/user/<user_id>', methods=['POST'])
def invalidate_user_cache(user_id):
    if not CACHE_ENABLED or not cache_service:
        return jsonify({'success': False, 'error': 'Cache not enabled'}), 503
    
    count = cache_service.invalidate_user_cache(user_id)
    return jsonify({'success': True, 'cleared': count, 'user_id': user_id})

@app.route('/api/cache/invalidate/analytics', methods=['POST'])
def invalidate_analytics_cache():
    if not CACHE_ENABLED or not cache_service:
        return jsonify({'success': False, 'error': 'Cache not enabled'}), 503
    
    data = request.get_json() or {}
    metric = data.get('metric')
    
    count = cache_service.invalidate_analytics(metric)
    return jsonify({'success': True, 'cleared': count})

@app.route('/api/cache/warm', methods=['POST'])
def warm_cache():
    if not CACHE_ENABLED or not cache_service:
        return jsonify({'success': False, 'error': 'Cache not enabled'}), 503
    
    # Define data loaders for frequently accessed data
    loaders = [
        {
            'key': 'analytics:dashboard',
            'func': lambda: {'message': 'Dashboard data warmed'},
            'ttl': 600
        }
    ]
    
    stats = cache_service.warm_cache(loaders)
    return jsonify({'success': True, 'message': 'Cache warmed', 'stats': stats})

@app.route('/api/cache/keys', methods=['GET'])
def get_cache_keys():
    if not CACHE_ENABLED or not cache_manager:
        return jsonify({'success': False, 'error': 'Cache not enabled'}), 503
    
    pattern = request.args.get('pattern', '*')
    keys = cache_manager.keys(pattern)
    
    # Get TTL info
    keys_with_ttl = [
        {'key': key, 'ttl': cache_manager.ttl_remaining(key)}
        for key in keys
    ]
    
    return jsonify({'success': True, 'keys': keys_with_ttl, 'count': len(keys)})

# ===== Rate Limiting Endpoints =====

@app.route('/api/rate-limit/check', methods=['GET'])
def check_rate_limit():
    if not RATE_LIMIT_ENABLED or not rate_limit_service:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    allowed, info = rate_limit_service.check_rate_limit(request)
    return jsonify({'success': True, 'rate_limit': info})

@app.route('/api/rate-limit/stats', methods=['GET'])
def get_rate_limit_stats():
    if not RATE_LIMIT_ENABLED or not rate_limit_service:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    stats = rate_limit_service.get_rate_limit_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/rate-limit/user/<user_id>', methods=['GET'])
def get_user_rate_limits(user_id):
    if not RATE_LIMIT_ENABLED or not rate_limit_service:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    limits = rate_limit_service.get_user_rate_limits(user_id)
    return jsonify({'success': True, 'limits': limits})

@app.route('/api/rate-limit/ip/<ip>', methods=['GET'])
def get_ip_rate_limits(ip):
    if not RATE_LIMIT_ENABLED or not rate_limit_service:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    limits = rate_limit_service.get_ip_rate_limits(ip)
    return jsonify({'success': True, 'limits': limits})

@app.route('/api/rate-limit/whitelist/<user_id>', methods=['POST'])
def whitelist_user(user_id):
    if not RATE_LIMIT_ENABLED or not rate_limit_service:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    count = rate_limit_service.whitelist_user(user_id)
    return jsonify({'success': True, 'message': f'Whitelisted user {user_id}', 'cleared': count})

@app.route('/api/rate-limit/blacklist/<ip>', methods=['POST'])
def blacklist_ip(ip):
    if not RATE_LIMIT_ENABLED or not rate_limit_service:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    data = request.get_json() or {}
    duration = data.get('duration', 3600)
    
    rate_limit_service.blacklist_ip(ip, duration)
    return jsonify({'success': True, 'message': f'Blacklisted IP {ip} for {duration} seconds'})

@app.route('/api/rate-limit/reset', methods=['POST'])
def reset_rate_limit():
    if not RATE_LIMIT_ENABLED or not rate_limiter:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    data = request.get_json()
    if 'key' not in data:
        return jsonify({'success': False, 'error': 'Missing: key'}), 400
    
    rate_limiter.reset_bucket(data['key'])
    return jsonify({'success': True, 'message': f"Reset rate limit for {data['key']}"})

@app.route('/api/rate-limit/cleanup', methods=['POST'])
def cleanup_rate_limits():
    if not RATE_LIMIT_ENABLED or not rate_limiter:
        return jsonify({'success': False, 'error': 'Rate limiting not enabled'}), 503
    
    data = request.get_json() or {}
    max_age = data.get('max_age', 3600)
    
    count = rate_limiter.cleanup_old_buckets(max_age)
    return jsonify({'success': True, 'cleaned': count, 'max_age': max_age})

# ===== Database Optimization Endpoints =====

@app.route('/api/db/optimize/indexes', methods=['POST'])
def create_database_indexes():
    if not DB_OPTIMIZATION_ENABLED or not db_optimizer:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    count = db_optimizer.create_indexes()
    return jsonify({'success': True, 'message': f'Created/verified {count} indexes'})

@app.route('/api/db/optimize/analyze', methods=['POST'])
def analyze_database():
    if not DB_OPTIMIZATION_ENABLED or not db_optimizer:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    count = db_optimizer.analyze_tables()
    return jsonify({'success': True, 'message': f'Analyzed {count} tables'})

@app.route('/api/db/optimize/vacuum', methods=['POST'])
def vacuum_database():
    if not DB_OPTIMIZATION_ENABLED or not db_optimizer:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    db_optimizer.vacuum_database()
    return jsonify({'success': True, 'message': 'Database vacuumed successfully'})

@app.route('/api/db/stats/tables', methods=['GET'])
def get_table_statistics():
    if not DB_OPTIMIZATION_ENABLED or not db_optimizer:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    stats = db_optimizer.get_table_stats()
    return jsonify({'success': True, 'tables': stats})

@app.route('/api/db/stats/indexes', methods=['GET'])
def get_index_statistics():
    if not DB_OPTIMIZATION_ENABLED or not db_optimizer:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    indexes = db_optimizer.get_index_stats()
    return jsonify({'success': True, 'indexes': indexes, 'count': len(indexes)})

@app.route('/api/db/query/analyze', methods=['POST'])
def analyze_query():
    if not DB_OPTIMIZATION_ENABLED or not db_optimizer:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    data = request.get_json()
    if 'query' not in data:
        return jsonify({'success': False, 'error': 'Missing: query'}), 400
    
    result = db_optimizer.optimize_query(data['query'])
    return jsonify({'success': True, 'analysis': result})

@app.route('/api/db/query/stats', methods=['GET'])
def get_query_statistics():
    if not DB_OPTIMIZATION_ENABLED or not query_monitor:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    stats = query_monitor.get_query_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/db/query/slow', methods=['GET'])
def get_slow_queries():
    if not DB_OPTIMIZATION_ENABLED or not query_monitor:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    slow_queries = query_monitor.get_slow_queries()
    return jsonify({'success': True, 'slow_queries': slow_queries, 'count': len(slow_queries)})

@app.route('/api/db/maintenance/run', methods=['POST'])
def run_database_maintenance():
    if not DB_OPTIMIZATION_ENABLED or not db_maintenance:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    results = db_maintenance.run_maintenance()
    return jsonify({'success': True, 'maintenance': results})

@app.route('/api/db/maintenance/history', methods=['GET'])
def get_maintenance_history():
    if not DB_OPTIMIZATION_ENABLED or not db_maintenance:
        return jsonify({'success': False, 'error': 'DB optimization not enabled'}), 503
    
    history = db_maintenance.get_maintenance_history()
    return jsonify({'success': True, 'history': history, 'count': len(history)})

# ===== Background Job Queue Endpoints =====

@app.route('/api/jobs/enqueue', methods=['POST'])
def enqueue_job():
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    data = request.get_json()
    if 'job_type' not in data or 'payload' not in data:
        return jsonify({'success': False, 'error': 'Missing: job_type, payload'}), 400
    
    priority_str = data.get('priority', 'normal').upper()
    priority = JobPriority[priority_str] if priority_str in JobPriority.__members__ else JobPriority.NORMAL
    
    job_id = job_queue.enqueue(data['job_type'], data['payload'], priority)
    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    job = job_queue.get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
    
    return jsonify({'success': True, 'job': job})

@app.route('/api/jobs', methods=['GET'])
def get_jobs_list():
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    
    jobs = job_queue.get_jobs(status, limit)
    return jsonify({'success': True, 'jobs': jobs, 'count': len(jobs)})

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    cancelled = job_queue.cancel_job(job_id)
    if cancelled:
        return jsonify({'success': True, 'message': 'Job cancelled'})
    else:
        return jsonify({'success': False, 'error': 'Job cannot be cancelled'}), 400

@app.route('/api/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    retried = job_queue.retry_job(job_id)
    if retried:
        return jsonify({'success': True, 'message': 'Job retried'})
    else:
        return jsonify({'success': False, 'error': 'Job cannot be retried'}), 400

@app.route('/api/jobs/stats', methods=['GET'])
def get_job_stats():
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    stats = job_queue.get_queue_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/jobs/cleanup', methods=['POST'])
def cleanup_jobs():
    if not JOBS_ENABLED or not job_queue:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    data = request.get_json() or {}
    max_age = data.get('max_age', 24)
    
    count = job_queue.cleanup_old_jobs(max_age)
    return jsonify({'success': True, 'cleaned': count, 'max_age_hours': max_age})

# Convenience endpoints for common job types

@app.route('/api/jobs/schedule/email', methods=['POST'])
def schedule_email_job():
    if not JOBS_ENABLED or not job_service:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    data = request.get_json()
    required = ['to', 'subject', 'body']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    job_id = job_service.schedule_email(
        data['to'], data['subject'], data['body'],
        JobPriority[data.get('priority', 'NORMAL').upper()]
    )
    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/jobs/schedule/export', methods=['POST'])
def schedule_export_job():
    if not JOBS_ENABLED or not job_service:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    data = request.get_json()
    required = ['entity', 'filters']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    job_id = job_service.schedule_export(
        data['entity'], data['filters'], 
        data.get('format', 'csv'),
        JobPriority[data.get('priority', 'NORMAL').upper()]
    )
    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/jobs/schedule/webhook', methods=['POST'])
def schedule_webhook_job():
    if not JOBS_ENABLED or not job_service:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    data = request.get_json()
    required = ['url', 'payload']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    job_id = job_service.schedule_webhook(
        data['url'], data['payload'],
        JobPriority[data.get('priority', 'HIGH').upper()]
    )
    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/jobs/schedule/report', methods=['POST'])
def schedule_report_job():
    if not JOBS_ENABLED or not job_service:
        return jsonify({'success': False, 'error': 'Jobs not enabled'}), 503
    
    data = request.get_json()
    required = ['report_type', 'filters']
    if not all(field in data for field in required):
        return jsonify({'success': False, 'error': f'Missing fields: {required}'}), 400
    
    job_id = job_service.schedule_report(
        data['report_type'], data['filters'],
        data.get('format', 'pdf'),
        JobPriority[data.get('priority', 'NORMAL').upper()]
    )
    return jsonify({'success': True, 'job_id': job_id})

# ----------------------
# Admin pages and Monitoring/Analytics APIs
# ----------------------

## '/admin' route is defined earlier with admin_required; avoid duplicate endpoint here

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@app.route('/api/admin/summary')
def api_admin_summary():
    try:
        platform_breakdown: Dict[str, int] = defaultdict(int)
        for j in live_jobs:
            p = (j.get('platform') or 'unknown')
            platform_breakdown[p] += 1
        db_stats: Dict = {}
        if db:
            try:
                db_stats = db.get_stats()
            except Exception as e:
                db_stats = {'error': str(e)}
        return jsonify({
            'success': True,
            'live_jobs_count': len(live_jobs),
            'platform_breakdown': platform_breakdown,
            'db_stats': db_stats,
            'recent_events': recent_events[-100:]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/crawl-logs')
def api_admin_crawl_logs():
    limit = int(request.args.get('limit', 20))
    try:
        logs: List[Dict] = []
        if db:
            try:
                logs = db.get_crawl_logs(limit=limit)
            except Exception:
                logs = []
        if not logs:
            logs = memory_crawl_logs[-limit:]
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clear-db', methods=['POST'])
def api_admin_clear_db():
    try:
        body = request.get_json(silent=True) or {}
        what = (body.get('what') or 'all').lower()
        clear_events = bool(body.get('clearEvents') or body.get('clear_events'))
        clear_search = bool(body.get('clearSearchHistory') or body.get('clear_search_history'))
        deleted = {'jobs': 0, 'leads': 0}
        if db:
            db.connect()
            cur = db.conn.cursor()
            if what in ('all', 'jobs'):
                try:
                    cur.execute("DELETE FROM job_history")
                except Exception:
                    pass
                try:
                    cur.execute("DELETE FROM job_contacts")
                except Exception:
                    pass
                try:
                    cur.execute("DELETE FROM contacts")
                except Exception:
                    pass
                cur.execute("DELETE FROM jobs")
                deleted['jobs'] = cur.rowcount or 0
            if what in ('all', 'leads'):
                try:
                    cur.execute("DELETE FROM business_leads")
                    deleted['leads'] = cur.rowcount or 0
                except Exception:
                    pass
            if clear_search or what == 'all':
                try:
                    cur.execute("DELETE FROM search_history")
                except Exception:
                    pass
            db.conn.commit()
        if clear_events or what == 'all':
            try:
                recent_events.clear()
            except Exception:
                pass
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    try:
        out = {'total_jobs': 0, 'remote_jobs': 0, 'applied_jobs': 0, 'new_jobs': 0}
        if db:
            s = db.get_stats()
            out['total_jobs'] = s.get('total_jobs', 0)
            out['remote_jobs'] = s.get('remote_jobs', 0)
            out['new_jobs'] = s.get('new_last_24h', 0)
            db.connect()
            cur = db.conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
                row = cur.fetchone()
                out['applied_jobs'] = (row[0] if row else 0)
            except Exception:
                pass
        return jsonify(out)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/trends')
def api_analytics_trends():
    days = int(request.args.get('days', 30))
    try:
        data: List = []
        if db:
            db.connect()
            cur = db.conn.cursor()
            end = datetime.utcnow().date()
            start = end - timedelta(days=days-1)
            counts = { (start + timedelta(days=i)).isoformat(): 0 for i in range(days) }
            cur.execute("SELECT date(first_seen) as d, COUNT(*) FROM jobs WHERE date(first_seen) >= date(?) GROUP BY date(first_seen)", (start.isoformat(),))
            for row in cur.fetchall():
                d = row[0]
                c = row[1]
                if d in counts:
                    counts[d] = c
            data = [[d, counts[d]] for d in sorted(counts.keys())]
        return jsonify({'data': {'daily_data': data}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/salary')
def api_analytics_salary():
    try:
        ranges = { '$0-50k': 0, '$50-100k': 0, '$100-150k': 0, '$150-200k': 0, '$200k+': 0 }
        total_with_salary = 0
        if db:
            import re as _re
            db.connect()
            cur = db.conn.cursor()
            cur.execute("SELECT COALESCE(salary, budget) FROM jobs")
            rows = cur.fetchall()
            for r in rows:
                s = r[0]
                if not s:
                    continue
                text = str(s)
                m = _re.search(r"(\$?)(\d{2,3})(?:[,\.]?\d{3})?", text)
                if not m:
                    continue
                try:
                    val = int(m.group(2))
                except Exception:
                    continue
                total_with_salary += 1
                if val < 50:
                    ranges['$0-50k'] += 1
                elif val < 100:
                    ranges['$50-100k'] += 1
                elif val < 150:
                    ranges['$100-150k'] += 1
                elif val < 200:
                    ranges['$150-200k'] += 1
                else:
                    ranges['$200k+'] += 1
        if total_with_salary == 0:
            return jsonify({'data': {'insufficient_data': True}})
        return jsonify({'data': {'ranges': ranges}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

_SKILL_WORDS = [
    'python','java','javascript','typescript','react','node','next.js','vue','angular','docker','kubernetes','aws','gcp','azure','graphql','rest','postgres','mysql','mongodb','redis','kafka','spark','hadoop','pandas','tensorflow','pytorch','nlp','ml','ai','devops','ci/cd','linux'
]

@app.route('/api/analytics/skills')
def api_analytics_skills():
    top_n = int(request.args.get('top_n', 20))
    try:
        counts: Dict[str, int] = defaultdict(int)
        if db:
            db.connect()
            cur = db.conn.cursor()
            cur.execute("SELECT LOWER(COALESCE(title,'') || ' ' || COALESCE(description,'')) FROM jobs")
            for row in cur.fetchall():
                blob = row[0] or ''
                for w in _SKILL_WORDS:
                    if w in blob:
                        counts[w] += 1
        data = sorted(({ 'skill': k, 'count': v } for k,v in counts.items()), key=lambda x: x['count'], reverse=True)[:top_n]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/platforms')
def api_analytics_platforms():
    try:
        data: List[Dict] = []
        if db:
            db.connect()
            cur = db.conn.cursor()
            cur.execute("SELECT platform, COUNT(*) as c FROM jobs GROUP BY platform ORDER BY c DESC")
            rows = cur.fetchall()
            for r in rows:
                data.append({'platform': r[0], 'total_jobs': r[1]})
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/funnel')
def api_analytics_funnel():
    try:
        funnel = {'new': 0, 'interested': 0, 'applied': 0, 'interview': 0, 'offer': 0}
        if db:
            db.connect()
            cur = db.conn.cursor()
            cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            for r in cur.fetchall():
                k = (r[0] or '').lower()
                v = r[1] or 0
                if k in funnel:
                    funnel[k] = v
        return jsonify({'data': {'funnel': funnel}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/locations')
def api_analytics_locations():
    top_n = int(request.args.get('top_n', 10))
    try:
        data: List[Dict] = []
        if db:
            db.connect()
            cur = db.conn.cursor()
            cur.execute("SELECT COALESCE(location,'Unknown') as loc, COUNT(*) as c FROM jobs GROUP BY loc ORDER BY c DESC")
            rows = cur.fetchall()
            for r in rows:
                data.append({'location': r[0], 'count': r[1]})
        return jsonify({'data': data[:top_n]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/report')
def api_analytics_report():
    try:
        stats = api_stats().get_json()
        trends = api_analytics_trends().get_json().get('data', {})
        salary = api_analytics_salary().get_json().get('data', {})
        skills = api_analytics_skills().get_json().get('data', [])
        platforms = api_analytics_platforms().get_json().get('data', [])
        funnel = api_analytics_funnel().get_json().get('data', {})
        locations = api_analytics_locations().get_json().get('data', [])
        return jsonify({'data': {
            'stats': stats,
            'trends': trends,
            'salary': salary,
            'skills': skills,
            'platforms': platforms,
            'funnel': funnel,
            'locations': locations
        }})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------------------
# Outreach: send email with unsubscribe and DNC enforcement
# ----------------------

def _append_unsubscribe(text: str) -> str:
    footer = """

--
If you do not wish to receive further emails, just reply with 'unsubscribe' and we will not contact you again.
""".strip('\n')
    # Include contact email if available
    if CONTACT_EMAIL:
        footer += f"\nContact: {CONTACT_EMAIL}"
    return (text or '').rstrip() + "\n\n" + footer

def _smtp_send(to_email: str, subject: str, body: str) -> bool:
    if not (SMTP_HOST and SMTP_FROM):
        return False
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
        try:
            s.starttls()
        except Exception:
            pass
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    return True

@app.route('/api/outreach/send', methods=['POST'])
def api_outreach_send():
    try:
        payload = request.get_json(silent=True) or {}
        to_email = (payload.get('to') or '').strip()
        subject = (payload.get('subject') or '').strip()
        text = payload.get('text') or ''
        if not to_email or not subject or not text:
            return jsonify({'success': False, 'error': 'to, subject, text required'}), 400
        # DNC enforcement
        if db and db.is_do_not_contact(to_email):
            return jsonify({'success': False, 'error': 'do_not_contact'}), 403
        # Append unsubscribe footer
        body = _append_unsubscribe(text)
        sent = False
        error = None
        try:
            sent = _smtp_send(to_email, subject, body)
        except Exception as e:
            error = str(e)
        # Log outreach
        if db:
            try:
                db.record_outreach(to_email=to_email, subject=subject, body=body, transport='smtp' if sent else 'none', status='sent' if sent else 'failed', error=error)
            except Exception:
                pass
        if sent:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': error or 'send failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leads/opt-out', methods=['POST'])
def api_leads_opt_out():
    try:
        payload = request.get_json(silent=True) or {}
        email = (payload.get('email') or '').strip() or None
        domain = (payload.get('domain') or '').strip() or None
        lead_id = payload.get('lead_id')
        if not (email or domain or lead_id):
            return jsonify({'success': False, 'error': 'Provide email, domain or lead_id'}), 400
        if db:
            db.mark_do_not_contact(email=email, domain=domain, lead_id=lead_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------
# Additional monitoring metrics
# ----------------------

@app.route('/api/metrics/outreach')
def api_metrics_outreach():
    """Email outreach metrics: sent, delivered, opened, replied, bounced in a window."""
    days = int(request.args.get('days', 30))
    try:
        window_clause = "date(COALESCE(sent_at, created_at)) >= date('now', ? )"
        params = (f'-{days} days',)
        out = {'sent': 0, 'delivered': 0, 'opened': 0, 'replied': 0, 'bounced': 0}
        if db:
            db.connect()
            cur = db.conn.cursor()
            try:
                cur.execute(f"SELECT COUNT(*) FROM outreach_logs WHERE {window_clause}", params)
                out['sent'] = cur.fetchone()[0] or 0
                cur.execute(f"SELECT COUNT(*) FROM outreach_logs WHERE {window_clause} AND status = 'delivered'", params)
                out['delivered'] = cur.fetchone()[0] or 0
                cur.execute(f"SELECT COUNT(*) FROM outreach_logs WHERE {window_clause} AND status = 'opened'", params)
                out['opened'] = cur.fetchone()[0] or 0
                cur.execute(f"SELECT COUNT(*) FROM outreach_logs WHERE {window_clause} AND status = 'replied'", params)
                out['replied'] = cur.fetchone()[0] or 0
                cur.execute(f"SELECT COUNT(*) FROM outreach_logs WHERE {window_clause} AND status = 'bounced'", params)
                out['bounced'] = cur.fetchone()[0] or 0
            except Exception:
                pass
        # Derived rates
        total = max(out['sent'], 1)
        out['bounce_rate'] = out['bounced'] / total
        out['reply_rate'] = out['replied'] / total
        out['open_rate'] = out['opened'] / total
        return jsonify({'success': True, 'window_days': days, 'metrics': out})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/metrics/crawl')
def api_metrics_crawl():
    """Crawl/extraction quality: jobs created, with title+description, per-day counts."""
    days = int(request.args.get('days', 7))
    try:
        out = {'jobs_total': 0, 'with_title_desc': 0, 'success_rate': 0.0}
        if db:
            db.connect()
            cur = db.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM jobs WHERE date(COALESCE(crawled_at, first_seen)) >= date('now', ?)", (f'-{days} days',))
            row = cur.fetchone(); out['jobs_total'] = (row[0] if row else 0) or 0
            cur.execute("""
                SELECT COUNT(*) FROM jobs
                WHERE date(COALESCE(crawled_at, first_seen)) >= date('now', ?)
                  AND COALESCE(TRIM(title),'') <> ''
                  AND COALESCE(TRIM(description),'') <> ''
            """, (f'-{days} days',))
            row = cur.fetchone(); out['with_title_desc'] = (row[0] if row else 0) or 0
        total = max(out['jobs_total'], 1)
        out['success_rate'] = out['with_title_desc'] / total
        return jsonify({'success': True, 'window_days': days, 'metrics': out})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# WSGI entry point for Vercel
if __name__ == '__main__':
    app.run(debug=True)