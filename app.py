"""Web dashboard for job scraper using Flask."""
from flask import Flask, render_template, request, jsonify, send_file
from database import JobDatabase
from notifications import NotificationManager
from export import DataExporter
from ai_matcher import JobMatcher
import os
import threading
import time
import logging
from datetime import datetime
import json
from typing import Optional

import config
from scheduler import start_scheduler
from database import JobDatabase
from leads import find_contacts_for_job, check_mx, score_contact

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Don't create database connection at module level - SQLite isn't thread-safe
# We'll create it per request
notifier = NotificationManager()
exporter = DataExporter()
matcher = JobMatcher()
scheduler_instance = None
scrape_lock = threading.Lock()
last_scrape_info = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'filters': None,
    'platforms': None,
    'result': None,
    'error': None,
}

# Batch contacts discovery state
contacts_lock = threading.Lock()
contacts_batch = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'total': 0,
    'processed': 0,
    'found_contacts': 0,
    'verify_mx': False,
    'filters': None,
    'error': None,
}

def get_db():
    """Get database connection for current request."""
    return JobDatabase('output/jobs.db')


def _get_scheduler_status():
    """Build a scheduler status payload with interval and next run time."""
    status = {
        'configured_enabled': bool(config.AUTO_SCRAPE_ENABLED),
        'runtime_enabled': scheduler_instance is not None,
        'interval_minutes': int(config.AUTO_SCRAPE_INTERVAL_MINUTES),
        'platforms': list(getattr(config, 'DEFAULT_PLATFORMS', [])),
        'next_run_iso': None,
    }

    try:
        if scheduler_instance:
            job = scheduler_instance.get_job('auto_scrape_job')
            if job and job.next_run_time:
                status['next_run_iso'] = job.next_run_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            # Try to get interval from trigger if possible
            try:
                from apscheduler.triggers.interval import IntervalTrigger
                if isinstance(job.trigger, IntervalTrigger):
                    minutes = max(1, int(job.trigger.interval.total_seconds() // 60))
                    status['interval_minutes'] = minutes
            except Exception:
                pass
    except Exception:
        pass
    return status


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Simple health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/config/runtime')
def get_runtime_config():
    """Expose key runtime config flags for the UI (non-sensitive)."""
    try:
        info = {
            'use_selenium': bool(getattr(config, 'USE_SELENIUM', False)),
            'use_playwright': bool(getattr(config, 'USE_PLAYWRIGHT', False)),
            'use_stealth': bool(getattr(config, 'USE_STEALTH', False)),
            'stealth_backend': getattr(config, 'STEALTH_BACKEND', ''),
            'headless': bool(getattr(config, 'HEADLESS_MODE', True)),
            'proxy_set': bool(getattr(config, 'PROXY_URL', '').strip()),
            'default_platforms': list(getattr(config, 'DEFAULT_PLATFORMS', [])),
        }
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scheduler/status')
def scheduler_status():
    """Return current scheduler status including next run time."""
    try:
        return jsonify({'success': True, 'data': _get_scheduler_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _write_env_setting(key: str, value: str) -> bool:
    """Best-effort update or insert a key=value in .env for persistence."""
    try:
        env_path = os.path.join(os.getcwd(), '.env')
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f'{key}='):
                new_lines.append(f'{key}={value}')
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f'{key}={value}')
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines) + ('\n' if new_lines and not new_lines[-1].endswith('\n') else ''))
        return True
    except Exception:
        return False


@app.route('/api/scheduler/toggle', methods=['POST'])
def scheduler_toggle():
    """Enable or disable the background scheduler at runtime.

    JSON body:
        enable: bool
        persist: bool (optional) write AUTO_SCRAPE_ENABLED to .env
    """
    global scheduler_instance
    try:
        data = request.get_json(silent=True) or {}
        enable = bool(data.get('enable', True))
        persist = bool(data.get('persist', False))

        if enable:
            if scheduler_instance is None:
                scheduler_instance = start_scheduler()
        else:
            if scheduler_instance is not None:
                try:
                    scheduler_instance.shutdown(wait=False)
                except Exception:
                    pass
                scheduler_instance = None

        if persist:
            _write_env_setting('AUTO_SCRAPE_ENABLED', 'True' if enable else 'False')
            # Reflect immediately in config module for future status reads
            config.AUTO_SCRAPE_ENABLED = enable

        return jsonify({'success': True, 'data': _get_scheduler_status()})
    except Exception as e:
        logging.exception('/api/scheduler/toggle failed')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scheduler/interval', methods=['POST'])
def scheduler_interval():
    """Update scheduler interval (minutes). If scheduler is running, reschedule the job.

    JSON body:
        minutes: int
        persist: bool (optional) write AUTO_SCRAPE_INTERVAL_MINUTES to .env
    """
    global scheduler_instance
    try:
        data = request.get_json(silent=True) or {}
        minutes = int(data.get('minutes', 60))
        minutes = max(5, minutes)
        persist = bool(data.get('persist', False))

        # Update running job if present
        if scheduler_instance is not None:
            from apscheduler.triggers.interval import IntervalTrigger
            try:
                scheduler_instance.reschedule_job('auto_scrape_job', trigger=IntervalTrigger(minutes=minutes))
            except Exception:
                # Fallback: remove and re-add
                try:
                    scheduler_instance.remove_job('auto_scrape_job')
                except Exception:
                    pass
                # Recreate using current default platforms
                scheduler_instance.add_job(
                    func=lambda: None,  # temp placeholder to ensure job id uniqueness
                    trigger=IntervalTrigger(minutes=minutes),
                    id='auto_scrape_job',
                    replace_existing=True,
                )
                # Replace with proper function by restarting scheduler job via helper
                try:
                    scheduler_instance.shutdown(wait=False)
                except Exception:
                    pass
                scheduler_instance = start_scheduler()

        # Reflect in config
        config.AUTO_SCRAPE_INTERVAL_MINUTES = minutes
        if persist:
            _write_env_setting('AUTO_SCRAPE_INTERVAL_MINUTES', str(minutes))

        return jsonify({'success': True, 'data': _get_scheduler_status()})
    except Exception as e:
        logging.exception('/api/scheduler/interval failed')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Trigger an on-demand scrape run.
    JSON body (all optional):
        keywords: str
        location: str
        remote: bool
        max_pages: int
        platforms: list[str]
    """
    try:
        from main import JobScraperApp

        data = request.get_json(silent=True) or {}
        filters = {
            'keywords': data.get('keywords', ''),
            'location': data.get('location', ''),
            'remote': bool(data.get('remote', True)),
            'job_type': None,
            'max_pages': int(data.get('max_pages', 2)),
        }
        platforms = data.get('platforms')

        # Prevent overlapping runs
        if not scrape_lock.acquire(blocking=False):
            return jsonify({'success': False, 'error': 'Scrape already in progress'}), 429

        try:
            last_scrape_info.update({
                'running': True,
                'started_at': time.time(),
                'finished_at': None,
                'filters': filters,
                'platforms': platforms,
                'result': None,
                'error': None,
            })

            app_scraper = JobScraperApp()
            jobs = app_scraper.scrape_all_platforms(filters, platforms)

            db_results = get_db().save_jobs(jobs)
            last_scrape_info.update({
                'running': False,
                'finished_at': time.time(),
                'result': {
                    'scraped': len(jobs),
                    'saved': db_results,
                },
                'error': None,
            })

            return jsonify({
                'success': True,
                'scraped': len(jobs),
                'saved': db_results
            })
        except Exception as e:
            last_scrape_info.update({
                'running': False,
                'finished_at': time.time(),
                'error': str(e),
            })
            raise
        finally:
            try:
                scrape_lock.release()
            except Exception:
                pass
    except Exception as e:
        logging.exception("/api/scrape failed")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape/status')
def scrape_status():
    """Get scrape running status and last result info."""
    try:
        info = dict(last_scrape_info)
        # Add human-readable timestamps
        if info.get('started_at'):
            info['started_at_iso'] = datetime.utcfromtimestamp(info['started_at']).isoformat() + 'Z'
        if info.get('finished_at'):
            info['finished_at_iso'] = datetime.utcfromtimestamp(info['finished_at']).isoformat() + 'Z'
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/kanban')
def kanban():
    """Kanban board view."""
    return render_template('kanban.html')


@app.route('/api/jobs')
def get_jobs():
    """Get all jobs with filtering.
    
    Query parameters:
        remote_only: bool
        platform: str
        status: str
        keywords: str
        limit: int
        offset: int
    """
    try:
        remote_only = request.args.get('remote_only', 'false').lower() == 'true'
        platform = request.args.get('platform')
        status = request.args.get('status')
        keywords = request.args.get('keywords')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Search jobs
        jobs = get_db().search_jobs(
            keywords=keywords,
            remote_only=remote_only,
            platform=platform,
            limit=limit * 2  # Get more to filter by status
        )
        
        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job.get('status') == status]
        
        # Apply offset and limit
        jobs = jobs[offset:offset + limit] if offset > 0 else jobs[:limit]
        
        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<int:job_id>')
def get_job(job_id):
    """Get single job details."""
    try:
        with get_db():
            cursor = get_db().conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({
                    'success': False,
                    'error': 'Job not found'
                }), 404
            
            return jsonify({
                'success': True,
                'job': dict(job)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<int:job_id>/status', methods=['POST'])
def update_job_status(job_id):
    """Update job status.
    
    JSON body:
        status: str (new/applied/interested/rejected/archived)
        notes: str (optional)
    """
    try:
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        # Get job URL
        with get_db():
            cursor = get_db().conn.cursor()
            cursor.execute("SELECT url FROM jobs WHERE id = ?", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                return jsonify({
                    'success': False,
                    'error': 'Job not found'
                }), 404
            
            # Update status
            get_db().update_job_status(job['url'], new_status, notes)
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    try:
        stats = get_db().get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR in /api/stats: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/new-jobs')
def get_new_jobs():
    """Get new jobs from last N hours.
    
    Query parameters:
        hours: int (default: 24)
    """
    try:
        hours = int(request.args.get('hours', 24))
        jobs = get_db().get_new_jobs(since_hours=hours)
        
        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/platforms')
def get_platforms():
    """Get list of available platforms."""
    try:
        with get_db():
            cursor = get_db().conn.cursor()
            cursor.execute("SELECT DISTINCT platform FROM jobs ORDER BY platform")
            platforms = [row['platform'] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'platforms': platforms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export')
def export_jobs():
    """Export jobs to file.
    
    Query parameters:
        format: str (csv/json/excel)
        remote_only: bool
        platform: str
        status: str
    """
    try:
        format_type = request.args.get('format', 'csv')
        remote_only = request.args.get('remote_only', 'false').lower() == 'true'
        platform = request.args.get('platform')
        status = request.args.get('status')
        
        filters = {}
        if remote_only:
            filters['remote'] = True
        if platform:
            filters['platform'] = platform
        if status:
            filters['status'] = status
        
        # Export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'jobs_export_{timestamp}'
        
        filepath = exporter.export_database_to_file(
            format=format_type,
            filename=filename,
            filters=filters if filters else None
        )
        
        if filepath:
            return send_file(
                filepath,
                as_attachment=True,
                download_name=os.path.basename(filepath)
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Export failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<int:job_id>/history')
def get_job_history(job_id):
    """Get job change history."""
    try:
        with get_db():
            cursor = get_db().conn.cursor()
            cursor.execute("""
                SELECT change_date, field_name, old_value, new_value
                FROM job_history
                WHERE job_id = ?
                ORDER BY change_date DESC
            """, (job_id,))
            
            history = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<int:job_id>/contacts', methods=['GET', 'POST'])
def job_contacts(job_id):
    """Get or refresh contacts for a job.

    - GET: returns stored contacts
    - POST: refreshes contacts (extract + guess) and stores them
    """
    try:
        db = get_db()
        if request.method == 'GET':
            job = db.get_job_by_id(job_id)
            if not job:
                return jsonify({'success': False, 'error': 'Job not found'}), 404
            contacts = []
            try:
                emails = json.loads(job.get('contact_emails') or '[]')
            except Exception:
                emails = []
            try:
                sources = json.loads(job.get('contact_sources') or '{}')
            except Exception:
                sources = {}
            for e in emails:
                meta = sources.get(e, {})
                contacts.append({
                    'email': e,
                    'source': meta.get('source', 'unknown'),
                    'verified': bool(meta.get('verified', False)),
                    'type': meta.get('type', 'extracted'),
                })
            return jsonify({'success': True, 'contacts': contacts, 'company_domain': job.get('company_domain'), 'checked_at': job.get('contact_checked_at')})

        elif request.method == 'POST':
            job = db.get_job_by_id(job_id)
            if not job:
                return jsonify({'success': False, 'error': 'Job not found'}), 404
            body = request.get_json(silent=True) or {}
            verify_mx = bool(body.get('verify_mx', False))
            result = find_contacts_for_job(job, verify_mx=verify_mx)
            db.save_job_contacts(job_id, result['emails'], result['sources'], result.get('company_domain'))
            # Also store normalized contacts for cross-job dedup/export
            db.save_contacts_normalized(job_id, result['emails'], result['sources'], result.get('company_domain'), result.get('mx_ok'), result.get('confidence'))
            contacts = []
            for e in result['emails']:
                meta = result['sources'].get(e, {}).copy()
                meta['email'] = e
                meta['confidence'] = result.get('confidence', {}).get(e, 0.0)
                contacts.append(meta)
            return jsonify({'success': True, 'found': len(result['emails']), 'company_domain': result.get('company_domain'), 'mx_ok': result.get('mx_ok'), 'contacts': contacts})
    except Exception as e:
        logging.exception('/api/jobs/<id>/contacts failed')
        return jsonify({'success': False, 'error': str(e)}), 500


def _run_contacts_batch(filters: dict, verify_mx: bool):
    """Background worker to scan contacts across filtered jobs."""
    try:
        contacts_batch.update({'running': True, 'started_at': time.time(), 'finished_at': None, 'processed': 0, 'found_contacts': 0, 'error': None})
        # Fetch jobs according to filters
        keywords = filters.get('keywords')
        platform = filters.get('platform')
        status = filters.get('status')
        remote_only = bool(filters.get('remote_only', False))
        jobs = get_db().search_jobs(keywords=keywords, remote_only=remote_only, platform=platform, limit=10000)
        if status:
            jobs = [j for j in jobs if j.get('status') == status]
        contacts_batch['total'] = len(jobs)
        found_total = 0
        fetch_cache = {}
        for j in jobs:
            if not contacts_batch['running']:
                break
            jid = j.get('id') or get_db().job_exists(get_db().generate_job_hash(j))
            if not jid:
                contacts_batch['processed'] += 1
                continue
            res = find_contacts_for_job(j, verify_mx=verify_mx, fetch_cache=fetch_cache)
            get_db().save_job_contacts(jid, res['emails'], res['sources'], res.get('company_domain'))
            get_db().save_contacts_normalized(jid, res['emails'], res['sources'], res.get('company_domain'), res.get('mx_ok'), res.get('confidence'))
            found_total += len(res['emails'])
            contacts_batch['processed'] += 1
            contacts_batch['found_contacts'] = found_total
        contacts_batch.update({'running': False, 'finished_at': time.time()})
    except Exception as e:
        logging.exception('contacts batch failed')
        contacts_batch.update({'running': False, 'error': str(e), 'finished_at': time.time()})
    finally:
        try:
            contacts_lock.release()
        except Exception:
            pass


@app.route('/api/contacts/find', methods=['POST'])
def start_contacts_batch():
    """Start a background contacts discovery across current filters.

    JSON body (any optional): keywords, platform, status, remote_only, verify_mx
    """
    try:
        data = request.get_json(silent=True) or {}
        verify_mx = bool(data.get('verify_mx', False))
        filters = {
            'keywords': data.get('keywords') or None,
            'platform': data.get('platform') or None,
            'status': data.get('status') or None,
            'remote_only': bool(data.get('remote_only', False)),
        }
        # Prevent overlap
        if not contacts_lock.acquire(blocking=False):
            return jsonify({'success': False, 'error': 'Contacts batch already running'}), 429
        contacts_batch.update({'verify_mx': verify_mx, 'filters': filters})
        t = threading.Thread(target=_run_contacts_batch, args=(filters, verify_mx), daemon=True)
        t.start()
        return jsonify({'success': True})
    except Exception as e:
        try:
            contacts_lock.release()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts/find/cancel', methods=['POST'])
def cancel_contacts_batch():
    """Request cancellation of the running contacts batch."""
    try:
        if not contacts_batch.get('running'):
            return jsonify({'success': True, 'message': 'No batch running'})
        # Signal the worker to stop; it will release the lock in finally
        contacts_batch['running'] = False
        return jsonify({'success': True, 'message': 'Cancel requested'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts/find/status')
def contacts_batch_status():
    try:
        info = dict(contacts_batch)
        if info.get('started_at'):
            info['started_at_iso'] = datetime.utcfromtimestamp(info['started_at']).isoformat() + 'Z'
        if info.get('finished_at'):
            info['finished_at_iso'] = datetime.utcfromtimestamp(info['finished_at']).isoformat() + 'Z'
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/contacts')
def export_contacts():
    """Export contacts joined with job context.

    Query params:
      - format: csv|json (default csv)
      - min_confidence: float in [0,1] or percentage like 70
      - platform: optional filter
    """
    try:
        fmt = request.args.get('format', 'csv').lower()
        minc_raw = request.args.get('min_confidence', '0')
        platform = request.args.get('platform')
        try:
            minc = float(minc_raw)
            if minc > 1:
                minc = minc / 100.0
        except Exception:
            minc = 0.0
        # Add more filters to match UI
        keywords = request.args.get('keywords')
        status = request.args.get('status')
        remote_only = (request.args.get('remote_only', 'false').lower() == 'true')
        rows = get_db().query_contacts(min_confidence=minc, platform=platform, keywords=keywords, status=status, remote_only=remote_only)
        if not rows:
            return jsonify({'success': False, 'error': 'No contacts match filters'}), 404

        os.makedirs('output', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contacts_{timestamp}.{"json" if fmt=="json" else "csv"}'
        path = os.path.join('output', filename)

        if fmt == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
        else:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    except Exception as e:
        logging.exception('/api/export/contacts failed')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/contacts/selected', methods=['POST'])
def export_contacts_selected():
    """Export contacts for selected job IDs.

    JSON body:
      - job_ids: list[int]
      - format: csv|json (default csv)
      - min_confidence: float or percent
    """
    try:
        data = request.get_json(silent=True) or {}
        job_ids = data.get('job_ids') or []
        fmt = (data.get('format') or 'csv').lower()
        minc_raw = str(data.get('min_confidence') or '0')
        try:
            minc = float(minc_raw)
            if minc > 1:
                minc = minc / 100.0
        except Exception:
            minc = 0.0

        rows = get_db().query_contacts_for_jobs(job_ids, min_confidence=minc)
        if not rows:
            return jsonify({'success': False, 'error': 'No contacts for selected jobs'}), 404

        os.makedirs('output', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contacts_selected_{timestamp}.{"json" if fmt=="json" else "csv"}'
        path = os.path.join('output', filename)

        if fmt == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
        else:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    except Exception as e:
        logging.exception('/api/export/contacts/selected failed')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search-history')
def get_search_history():
    """Get recent search history."""
    try:
        with get_db():
            cursor = get_db().conn.cursor()
            cursor.execute("""
                SELECT search_date, keywords, location, remote_only,
                       platforms_searched, results_count, new_jobs_count
                FROM search_history
                ORDER BY search_date DESC
                LIMIT 20
            """)
            
            history = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/notify', methods=['POST'])
def send_notification():
    """Send notification for selected jobs.
    
    JSON body:
        job_ids: list of int
        channel: str (email/slack/discord)
        recipient: str (for email)
    """
    try:
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        channel = data.get('channel', 'email')
        recipient = data.get('recipient')
        
        if not job_ids:
            return jsonify({
                'success': False,
                'error': 'No jobs selected'
            }), 400
        
        # Get jobs
        with get_db():
            cursor = get_db().conn.cursor()
            placeholders = ','.join('?' * len(job_ids))
            cursor.execute(f"""
                SELECT * FROM jobs WHERE id IN ({placeholders})
            """, job_ids)
            
            jobs = [dict(row) for row in cursor.fetchall()]
        
        # Send notification
        if channel == 'email':
            if not recipient:
                recipient = os.getenv('RECIPIENT_EMAIL')
            if not recipient:
                return jsonify({
                    'success': False,
                    'error': 'Recipient email not specified'
                }), 400
            
            success = notifier.email.send_new_jobs_alert(recipient, jobs)
            
        elif channel in ['slack', 'discord']:
            success = notifier.webhook.send_new_jobs_notification(jobs)
            
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid channel'
            }), 400
        
        return jsonify({
            'success': success,
            'message': 'Notification sent' if success else 'Notification failed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_jobs():
    """Clean up old jobs.
    
    JSON body:
        days: int (default: 90)
    """
    try:
        data = request.get_json()
        days = data.get('days', 90)
        
        deleted = get_db().cleanup_old_jobs(days)
        
        return jsonify({
            'success': True,
            'deleted': deleted
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/recommendations')
def get_recommendations():
    """Get AI-powered job recommendations.
    
    Query parameters:
        limit: int (default 10)
        min_score: float (default 60)
    """
    try:
        limit = int(request.args.get('limit', 10))
        min_score = float(request.args.get('min_score', 60))
        
        recommendations = matcher.get_recommendations(limit=limit, min_score=min_score)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/preferences', methods=['GET', 'POST'])
def manage_preferences():
    """Get or update AI preferences."""
    try:
        if request.method == 'GET':
            # Get current preferences
            return jsonify({
                'success': True,
                'preferences': matcher.preferences
            })
        
        elif request.method == 'POST':
            # Update preferences
            data = request.get_json()
            matcher.save_preferences(data)
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/analyze-skills')
def analyze_skills():
    """Analyze skills demand in job market."""
    try:
        analysis = matcher.analyze_skills_demand()
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/suggest-skills')
def suggest_skills():
    """Get skill learning suggestions."""
    try:
        limit = int(request.args.get('limit', 10))
        suggestions = matcher.suggest_skills_to_learn(top_n=limit)
        
        # Convert tuples to dicts for JSON
        suggestions_list = [
            {'skill': skill, 'count': count}
            for skill, count in suggestions
        ]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/score-job/<int:job_id>')
def score_job(job_id):
    """Get AI match score for a specific job."""
    try:
        jobs = get_db().search_jobs(limit=1000)
        job = next((j for j in jobs if j['id'] == job_id), None)
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        score, breakdown = matcher.calculate_match_score(job)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'score': score,
            'breakdown': breakdown
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/analytics')
def analytics_page():
    """Analytics dashboard page."""
    return render_template('analytics.html')


@app.route('/api/analytics/trends')
def get_trends():
    """Get job posting trends."""
    try:
        from analytics import JobAnalytics
        
        days = int(request.args.get('days', 30))
        analytics = JobAnalytics(get_db())
        trends = analytics.get_job_trends(days)
        
        return jsonify({
            'success': True,
            'data': trends
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/salary')
def get_salary_insights():
    """Get salary insights."""
    try:
        from analytics import JobAnalytics
        
        analytics = JobAnalytics(get_db())
        salary = analytics.get_salary_insights()
        
        return jsonify({
            'success': True,
            'data': salary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/skills')
def get_skills_frequency():
    """Get skills frequency analysis."""
    try:
        from analytics import JobAnalytics
        
        top_n = int(request.args.get('top_n', 20))
        analytics = JobAnalytics(get_db())
        skills = analytics.get_skills_frequency(top_n)
        
        return jsonify({
            'success': True,
            'data': [{'skill': skill, 'count': count} for skill, count in skills]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/platforms')
def get_platform_stats():
    """Get platform statistics."""
    try:
        from analytics import JobAnalytics
        
        analytics = JobAnalytics(get_db())
        platforms = analytics.get_platform_stats()
        
        return jsonify({
            'success': True,
            'data': platforms
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/funnel')
def get_application_funnel():
    """Get application funnel metrics."""
    try:
        from analytics import JobAnalytics
        
        analytics = JobAnalytics(get_db())
        funnel = analytics.get_application_funnel()
        
        return jsonify({
            'success': True,
            'data': funnel
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/locations')
def get_locations():
    """Get geographic distribution."""
    try:
        from analytics import JobAnalytics
        
        top_n = int(request.args.get('top_n', 10))
        analytics = JobAnalytics(get_db())
        locations = analytics.get_geographic_distribution(top_n)
        
        return jsonify({
            'success': True,
            'data': [{'location': loc, 'count': count} for loc, count in locations]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/companies')
def get_companies():
    """Get company insights."""
    try:
        from analytics import JobAnalytics
        
        top_n = int(request.args.get('top_n', 10))
        analytics = JobAnalytics(get_db())
        companies = analytics.get_company_insights(top_n)
        
        return jsonify({
            'success': True,
            'data': companies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/report')
def get_comprehensive_report():
    """Get comprehensive analytics report."""
    try:
        from analytics import JobAnalytics
        
        analytics = JobAnalytics(get_db())
        report = analytics.get_comprehensive_report()
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    # Start scheduler if enabled
    try:
        import config
        from scheduler import start_scheduler
        if config.AUTO_SCRAPE_ENABLED:
            scheduler_instance = start_scheduler()
    except Exception as e:
        print(f"[scheduler] Failed to start: {e}")
    
    # Run development server
    app.run(debug=True, host='0.0.0.0', port=5000)
