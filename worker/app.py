import os
import json
import hmac
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime

from flask import Flask, request, jsonify
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import JobDatabase
from email.message import EmailMessage
import smtplib

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv('WORKER_WEBHOOK_SECRET') or os.getenv('WEBHOOK_SECRET') or ''
BACKEND_CRAWL_URL = os.getenv('BACKEND_CRAWL_URL')  # e.g. https://your-backend.example.com/api/crawl-urls
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'jobs.db'))
OUTREACH_DAILY_CAP = int(os.getenv('OUTREACH_DAILY_CAP', '20'))
OUTREACH_PER_DOMAIN_CAP = int(os.getenv('OUTREACH_PER_DOMAIN_CAP', '5'))

db = None
try:
    db = JobDatabase(DB_PATH)
except Exception:
    db = None


def verify_signature(secret: str, body: bytes, provided: str) -> bool:
    if not secret:
        return False
    try:
        expected = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, provided or '')
    except Exception:
        return False


@app.route('/worker/crawl', methods=['POST'])
def worker_crawl():
    # Verify signature
    sig = request.headers.get('X-Webhook-Signature')
    raw = request.get_data()  # raw bytes
    if not verify_signature(WEBHOOK_SECRET, raw, sig):
        return jsonify({'success': False, 'error': 'invalid signature'}), 401

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    urls = payload.get('urls') or []
    if not isinstance(urls, list) or not urls:
        return jsonify({'success': False, 'error': 'urls must be non-empty array'}), 400

    # Option A (recommended for MVP): forward to backend crawl endpoint that does the heavy lifting synchronously
    if BACKEND_CRAWL_URL:
        try:
            # Map fields to backend expects
            body = {
                'listing_urls': urls,
                'max_links_per_listing': int(payload.get('maxLinksPerListing') or 25),
                'keywords': payload.get('keywords') or [],
                'min_score': int(payload.get('minScore') or 0),
                'write_to_db': True
            }
            r = requests.post(BACKEND_CRAWL_URL, json=body, timeout=60)
            data = None
            try:
                data = r.json()
            except Exception:
                data = {'status_code': r.status_code, 'text': r.text[:500]}
            return jsonify({'success': 200 <= r.status_code < 300, 'backend': data}), 202
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 502

    # Option B: implement native crawling logic here (Playwright/Selenium/requests). Left as a future expansion.
    return jsonify({'success': True, 'message': 'Accepted. No BACKEND_CRAWL_URL configured; no-op.'}), 202


def _check_caps(to_email: str) -> Optional[str]:
    try:
        if not db:
            return None
        if OUTREACH_DAILY_CAP > 0 and db.count_sent_today() >= OUTREACH_DAILY_CAP:
            return f'daily cap {OUTREACH_DAILY_CAP} reached'
        dom = (to_email.split('@')[-1]).lower() if '@' in to_email else ''
        if OUTREACH_PER_DOMAIN_CAP > 0 and dom and db.count_sent_today_by_domain(dom) >= OUTREACH_PER_DOMAIN_CAP:
            return f'per-domain cap for {dom} reached ({OUTREACH_PER_DOMAIN_CAP})'
    except Exception:
        return None
    return None


def _send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    sendgrid_key = os.getenv('SENDGRID_API_KEY')
    if sendgrid_key:
        try:
            sg_url = 'https://api.sendgrid.com/v3/mail/send'
            data = {
                'personalizations': [ {'to':[{'email': to}]} ],
                'from': {'email': os.getenv('EMAIL_FROM', os.getenv('CONTACT_EMAIL') or 'no-reply@example.com')},
                'subject': subject,
                'content': [{'type': 'text/plain', 'value': body}]
            }
            r = requests.post(sg_url, headers={
                'Authorization': f'Bearer {sendgrid_key}',
                'Content-Type': 'application/json'
            }, data=json.dumps(data), timeout=10)
            ok = 200 <= r.status_code < 300 or r.status_code == 202
            return {'ok': ok, 'status': r.status_code, 'text': r.text[:500], 'transport': 'sendgrid'}
        except Exception as e:
            return {'ok': False, 'error': str(e), 'transport': 'sendgrid'}
    # SMTP
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    if not host:
        return {'ok': False, 'error': 'no email transport configured', 'transport': 'none'}
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = os.getenv('EMAIL_FROM', os.getenv('CONTACT_EMAIL') or user or 'no-reply@example.com')
        msg['To'] = to
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=15) as s:
            try:
                s.starttls()
            except Exception:
                pass
            if user and pwd:
                s.login(user, pwd)
            s.send_message(msg)
        return {'ok': True, 'status': 250, 'transport': 'smtp'}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'transport': 'smtp'}


@app.route('/worker/outreach-tick', methods=['POST', 'GET'])
def worker_outreach_tick():
    """Process due scheduled outreach respecting caps."""
    if not db:
        return jsonify({'success': False, 'error': 'db not available'}), 500
    due = db.get_scheduled_outreach_due(limit=20)
    processed = 0
    skipped = []
    for row in due:
        to_email = row.get('to_email')
        if not to_email:
            continue
        cap_err = _check_caps(to_email)
        if cap_err:
            skipped.append({'id': row.get('id'), 'reason': cap_err})
            continue
        res = _send_email(to_email, row.get('subject') or '', row.get('body') or '')
        if res.get('ok'):
            db.update_outreach_status(id=row.get('id'), status='sent', timestamp_field='sent_at')
            processed += 1
        else:
            db.update_outreach_status(id=row.get('id'), status='failed', error=res.get('error') or res.get('text'))
    return jsonify({'success': True, 'processed': processed, 'skipped': skipped, 'remaining': len(due) - processed - len(skipped)})


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)

@app.route('/worker/health', methods=['GET'])
def worker_health():
    return jsonify({'ok': True, 'time': datetime.utcnow().isoformat() + 'Z'}), 200
