import logging
import re
from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.core.management import call_command
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)
SCRAPE_INTERVAL_HOURS = 8
TEN_MINUTE_INTERVAL = 10


def run_scrape_if_due():
    from apps.jobs.models import ScrapeLog

    now = timezone.now()
    cutoff = now - timedelta(hours=SCRAPE_INTERVAL_HOURS)

    last_successful = ScrapeLog.objects.filter(
        status='completed'
    ).order_by('-started_at').first()

    if last_successful and last_successful.started_at > cutoff:
        next_run = last_successful.started_at + timedelta(hours=SCRAPE_INTERVAL_HOURS)
        logger.info(f"Scrape not due yet. Next scrape after {next_run.isoformat()}")
        return

    try:
        with transaction.atomic():
            log = ScrapeLog.objects.create(
                run_type='full',
                started_at=now,
                status='running',
            )
    except IntegrityError:
        logger.warning("Scrape already in progress (duplicate ScrapeLog)")
        return

    out = StringIO()
    jobs_created = 0
    hackathons_created = 0
    jobs_expired = 0
    hackathons_expired = 0

    try:
        call_command('run_scraper', stdout=out, stderr=out)
        output = out.getvalue()
        m = re.search(r'created (\d+) new jobs', output)
        if m:
            jobs_created = int(m.group(1))

        out.truncate(0)
        out.seek(0)
        call_command('scrape_hackathons', stdout=out, stderr=out)
        output = out.getvalue()
        m = re.search(r'created (\d+) new hackathons', output)
        if m:
            hackathons_created = int(m.group(1))

        out.truncate(0)
        out.seek(0)
        call_command('daily_refresh', stdout=out, stderr=out)
        output = out.getvalue()
        m = re.search(r'Expired (\d+) jobs', output)
        if m:
            jobs_expired = int(m.group(1))
        m = re.search(r'Expired (\d+) hackathons', output)
        if m:
            hackathons_expired = int(m.group(1))

        log.status = 'completed'
        log.jobs_created = jobs_created
        log.hackathons_created = hackathons_created
        log.jobs_expired = jobs_expired
        log.hackathons_expired = hackathons_expired
        log.completed_at = timezone.now()
        log.save()
        logger.info(f"Scrape complete: {jobs_created} jobs, {hackathons_created} hackathons created, "
                     f"{jobs_expired} jobs, {hackathons_expired} hackathons expired")

    except Exception as e:
        log.status = 'failed'
        log.error = str(e)
        log.completed_at = timezone.now()
        log.save()
        logger.error(f"Scrape failed: {e}")


def start_scheduler():
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED=False")
        return

    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    trigger = IntervalTrigger(minutes=TEN_MINUTE_INTERVAL)
    scheduler.add_job(
        run_scrape_if_due,
        trigger=trigger,
        id='scrape_check',
        name='Check if scrape is due every 10 minutes',
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — checking for due scrape every {TEN_MINUTE_INTERVAL} minutes")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
