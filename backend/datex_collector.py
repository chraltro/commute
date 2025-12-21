"""
Background collector for DATEX travel time data.
Polls every 5 minutes and stores data in the database.
"""
import time
from datetime import datetime
from typing import Optional
import threading
import logging

from datex_client import fetch_travel_time_data, fetch_segment_locations
from database import (
    init_database, store_travel_time, store_segment,
    update_collection_status, get_collection_status
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatexCollector:
    """Background collector for DATEX data."""

    def __init__(self, poll_interval_seconds: int = 300):
        """
        Initialize the collector.

        Args:
            poll_interval_seconds: How often to poll (default 300 = 5 minutes)
        """
        self.poll_interval = poll_interval_seconds
        self.is_running = False
        self.thread: Optional[threading.Thread] = None

    def _collect_once(self):
        """Perform a single collection cycle."""
        try:
            logger.info("Fetching travel time data from DATEX API...")
            travel_times = fetch_travel_time_data()

            if travel_times:
                logger.info(f"Received {len(travel_times)} travel time measurements")

                # Store each measurement
                for data in travel_times:
                    store_travel_time(
                        segment_id=data['segment_id'],
                        travel_time_seconds=data['travel_time_seconds'],
                        timestamp=data['timestamp']
                    )

                # Update last poll time
                update_collection_status(last_poll=datetime.now())
                logger.info("Data stored successfully")
            else:
                logger.warning("No travel time data received")

        except Exception as e:
            logger.error(f"Error during collection: {e}")

    def _collection_loop(self):
        """Main collection loop that runs in a background thread."""
        logger.info(f"Starting DATEX collection loop (polling every {self.poll_interval}s)")

        while self.is_running:
            self._collect_once()

            # Sleep in small intervals to allow responsive shutdown
            sleep_time = 0
            while sleep_time < self.poll_interval and self.is_running:
                time.sleep(1)
                sleep_time += 1

        logger.info("Collection loop stopped")

    def start(self):
        """Start the background collection process."""
        if self.is_running:
            logger.warning("Collector is already running")
            return

        self.is_running = True
        update_collection_status(is_collecting=True)

        self.thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.thread.start()

        logger.info("DATEX collector started")

    def stop(self):
        """Stop the background collection process."""
        if not self.is_running:
            logger.warning("Collector is not running")
            return

        self.is_running = False
        update_collection_status(is_collecting=False)

        if self.thread:
            self.thread.join(timeout=5)

        logger.info("DATEX collector stopped")

    def status(self) -> dict:
        """Get current collector status."""
        db_status = get_collection_status()
        return {
            'is_running': self.is_running,
            'is_collecting': db_status['is_collecting'],
            'last_poll': db_status['last_poll'],
            'days_collected': db_status['days_collected'],
            'poll_interval_seconds': self.poll_interval
        }


def initialize_segments():
    """
    Fetch and store segment definitions from DATEX API.
    Should be run once during setup.
    """
    try:
        logger.info("Fetching segment locations from DATEX API...")
        segments = fetch_segment_locations()

        if segments:
            logger.info(f"Received {len(segments)} segment definitions")

            for segment in segments:
                store_segment(
                    segment_id=segment['segment_id'],
                    name=segment['name'],
                    from_location=segment.get('from_location'),
                    to_location=segment.get('to_location'),
                    description=segment.get('description')
                )

            logger.info("Segment definitions stored successfully")
            return True
        else:
            logger.warning("No segment data received")
            return False

    except Exception as e:
        logger.error(f"Error fetching segments: {e}")
        return False


# Global collector instance
_collector: Optional[DatexCollector] = None


def get_collector() -> DatexCollector:
    """Get or create the global collector instance."""
    global _collector
    if _collector is None:
        _collector = DatexCollector()
    return _collector


def start_collection():
    """Start the data collection process."""
    collector = get_collector()
    collector.start()


def stop_collection():
    """Stop the data collection process."""
    collector = get_collector()
    collector.stop()


def get_status() -> dict:
    """Get collection status."""
    collector = get_collector()
    return collector.status()


if __name__ == '__main__':
    # For testing/standalone running
    init_database()

    # Optionally initialize segments
    import sys
    if '--init-segments' in sys.argv:
        initialize_segments()

    # Start collector
    collector = DatexCollector()
    collector.start()

    try:
        # Keep running until interrupted
        while True:
            time.sleep(60)
            status = collector.status()
            logger.info(f"Status: {status}")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        collector.stop()
