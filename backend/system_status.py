"""
System status and health monitoring utilities.
"""
import os
import psutil
from datetime import datetime
from typing import Dict


def get_system_stats() -> Dict:
    """Get system resource statistics."""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available_mb': psutil.virtual_memory().available / (1024 * 1024),
            'disk_percent': psutil.disk_usage('/').percent,
            'disk_available_gb': psutil.disk_usage('/').free / (1024 * 1024 * 1024),
        }
    except Exception:
        # psutil might not be available, return None
        return None


def get_database_stats() -> Dict:
    """Get database statistics."""
    from database import get_connection, config

    try:
        # Get database file size
        db_size = os.path.getsize(config.DB_PATH) if os.path.exists(config.DB_PATH) else 0
        db_size_mb = db_size / (1024 * 1024)

        # Get record counts
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM travel_times')
        travel_times_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM segments')
        segments_count = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM travel_times')
        date_range = cursor.fetchone()

        conn.close()

        return {
            'size_mb': round(db_size_mb, 2),
            'travel_times_count': travel_times_count,
            'segments_count': segments_count,
            'date_range': {
                'start': date_range[0] if date_range[0] else None,
                'end': date_range[1] if date_range[1] else None
            }
        }
    except Exception as e:
        return {'error': str(e)}


def get_comprehensive_status() -> Dict:
    """Get comprehensive system status."""
    from config import config
    from database import get_collection_status

    collection_status = get_collection_status()
    db_stats = get_database_stats()
    system_stats = get_system_stats()

    return {
        'timestamp': datetime.now().isoformat(),
        'application': {
            'version': '2.0.0',
            'debug_mode': config.DEBUG,
            'google_maps_configured': config.is_google_maps_configured(),
            'datex_configured': config.is_datex_configured(),
        },
        'collection': {
            'is_collecting': collection_status['is_collecting'],
            'last_poll': collection_status['last_poll'],
            'days_collected': collection_status['days_collected'],
            'poll_interval': config.DATEX_POLL_INTERVAL_SECONDS,
        },
        'database': db_stats,
        'system': system_stats,
    }
