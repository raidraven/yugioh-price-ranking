"""
APScheduler integration: schedules the daily 7:00 JST price update.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)


@util.close_old_connections
def update_prices_job():
    """The scheduled job that refreshes all card prices from the API."""
    from .services import update_all_prices
    logger.info('Starting scheduled price update...')
    count = update_all_prices()
    logger.info('Scheduled price update done: %d cards updated.', count)


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """Clean up APScheduler execution logs older than 7 days."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start():
    """Start the APScheduler. Called from apps.py ready()."""
    scheduler = BackgroundScheduler(timezone='Asia/Tokyo')
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    # Run every day at 07:00 JST
    scheduler.add_job(
        update_prices_job,
        trigger=CronTrigger(hour=7, minute=0, timezone='Asia/Tokyo'),
        id='update_prices',
        max_instances=1,
        replace_existing=True,
    )
    logger.info('APScheduler: scheduled price update at 07:00 JST daily.')

    # Clean up old job executions every Sunday at 00:00
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week='sun', hour=0, minute=0, timezone='Asia/Tokyo'),
        id='delete_old_job_executions',
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    logger.info('APScheduler started successfully.')
