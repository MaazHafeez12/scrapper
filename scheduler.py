"""Background scheduler for automated scraping.

Uses APScheduler's BackgroundScheduler to run the multi-platform scraper periodically
based on configuration in config.py.
"""
from typing import Dict, List
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
import atexit

import config
from main import JobScraperApp
from database import JobDatabase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _build_filters() -> Dict:
    return {
        'keywords': config.DEFAULT_KEYWORDS,
        'location': config.DEFAULT_LOCATION,
        'remote': config.DEFAULT_REMOTE,
        'job_type': None,
        'max_pages': config.DEFAULT_MAX_PAGES,
    }


def _run_scrape_job(platforms: List[str]):
    try:
        app = JobScraperApp()
        filters = _build_filters()
        logger.info(f"[scheduler] Running scrape @ {datetime.now().isoformat()} | platforms={platforms} | filters={filters}")
        jobs = app.scrape_all_platforms(filters, platforms)

        # Save to DB
        db = JobDatabase()
        result = db.save_jobs(jobs)
        db.save_search_history({
            'keywords': filters['keywords'],
            'location': filters['location'],
            'remote': filters['remote'],
            'platforms': platforms,
        }, result)
        logger.info(f"[scheduler] Saved new={result['new']} updated={result['updated']} (total scraped={len(jobs)})")
    except Exception as e:
        logger.exception(f"[scheduler] scrape job failed: {e}")


def start_scheduler() -> BackgroundScheduler:
    if not config.AUTO_SCRAPE_ENABLED:
        logger.info("[scheduler] Auto-scrape disabled by config")
        return None

    executors = {
        'default': ThreadPoolExecutor(4),
    }
    scheduler = BackgroundScheduler(executors=executors, timezone="UTC")

    interval_minutes = max(5, config.AUTO_SCRAPE_INTERVAL_MINUTES)
    trigger = IntervalTrigger(minutes=interval_minutes)

    scheduler.add_job(
        _run_scrape_job,
        trigger=trigger,
        args=[config.DEFAULT_PLATFORMS],
        id='auto_scrape_job',
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
    )

    scheduler.start()
    logger.info(f"[scheduler] Started. Interval={interval_minutes} minutes, platforms={config.DEFAULT_PLATFORMS}")

    # Ensure clean shutdown
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler
