"""
Advanced scheduler for DATEX data collection using APScheduler.
Provides more robust scheduling with job management and error recovery.
"""
import logging
from datetime import datetime
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

from config import config
from datex_client import fetch_travel_time_data
from database import store_travel_time, update_collection_status

logger = logging.getLogger(__name__)


class DatexScheduler:
    """
    Advanced scheduler for DATEX data collection.
    Falls back to threading if APScheduler is not available.
    """

    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self.job_id = 'datex_collection_job'
        self.is_running = False
        self.last_success = None
        self.last_error = None
        self.success_count = 0
        self.error_count = 0

    def _collect_data(self):
        """Perform data collection - called by scheduler."""
        try:
            logger.info("Starting DATEX data collection cycle...")
            travel_times = fetch_travel_time_data()

            if travel_times:
                logger.info(f"Received {len(travel_times)} travel time measurements")

                for data in travel_times:
                    store_travel_time(
                        segment_id=data['segment_id'],
                        travel_time_seconds=data['travel_time_seconds'],
                        timestamp=data['timestamp']
                    )

                update_collection_status(last_poll=datetime.now())
                self.last_success = datetime.now()
                self.success_count += 1
                logger.info(f"Data stored successfully (success count: {self.success_count})")
            else:
                logger.warning("No travel time data received")
                self.error_count += 1

        except Exception as e:
            logger.error(f"Error during collection: {e}", exc_info=True)
            self.last_error = str(e)
            self.error_count += 1

    def _job_listener(self, event):
        """Listen to job execution events."""
        if event.exception:
            logger.error(f"Job failed: {event.exception}")
        else:
            logger.debug("Job executed successfully")

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return False

        if not HAS_APSCHEDULER:
            logger.warning("APScheduler not available, falling back to simple threading")
            # Fall back to the original threading-based collector
            from datex_collector import get_collector
            collector = get_collector()
            collector.start()
            self.is_running = True
            return True

        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

            # Add the collection job
            self.scheduler.add_job(
                func=self._collect_data,
                trigger=IntervalTrigger(seconds=config.DATEX_POLL_INTERVAL_SECONDS),
                id=self.job_id,
                name='DATEX Data Collection',
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )

            self.scheduler.start()
            self.is_running = True
            update_collection_status(is_collecting=True)

            logger.info(f"Scheduler started - polling every {config.DATEX_POLL_INTERVAL_SECONDS}s")

            # Run first collection immediately
            self._collect_data()

            return True

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            self.is_running = False
            return False

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return False

        if not HAS_APSCHEDULER:
            # Fall back to threading-based collector
            from datex_collector import get_collector
            collector = get_collector()
            collector.stop()
            self.is_running = False
            return True

        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=False)
                self.scheduler = None

            self.is_running = False
            update_collection_status(is_collecting=False)
            logger.info("Scheduler stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            return False

    def get_status(self) -> dict:
        """Get detailed scheduler status."""
        status = {
            'is_running': self.is_running,
            'has_apscheduler': HAS_APSCHEDULER,
            'poll_interval_seconds': config.DATEX_POLL_INTERVAL_SECONDS,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_error': self.last_error,
        }

        if HAS_APSCHEDULER and self.scheduler and self.is_running:
            job = self.scheduler.get_job(self.job_id)
            if job:
                status['next_run'] = job.next_run_time.isoformat() if job.next_run_time else None

        return status

    def run_now(self):
        """Trigger an immediate collection cycle."""
        if not self.is_running:
            logger.warning("Scheduler is not running, cannot run collection now")
            return False

        logger.info("Running immediate collection cycle...")
        self._collect_data()
        return True


# Global scheduler instance
_scheduler: Optional[DatexScheduler] = None


def get_scheduler() -> DatexScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DatexScheduler()
    return _scheduler


def start_scheduler():
    """Start the data collection scheduler."""
    scheduler = get_scheduler()
    return scheduler.start()


def stop_scheduler():
    """Stop the data collection scheduler."""
    scheduler = get_scheduler()
    return scheduler.stop()


def get_scheduler_status() -> dict:
    """Get scheduler status."""
    scheduler = get_scheduler()
    return scheduler.get_status()


def run_collection_now():
    """Trigger immediate collection."""
    scheduler = get_scheduler()
    return scheduler.run_now()
