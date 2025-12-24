"""
Database module for storing and querying DATEX travel time data.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from config import config


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table for DATEX travel time measurements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travel_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            segment_id TEXT NOT NULL,
            travel_time_seconds INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            hour INTEGER NOT NULL,
            minute INTEGER NOT NULL
        )
    ''')

    # Index for efficient queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_segment_day_time
        ON travel_times(segment_id, day_of_week, hour, minute)
    ''')

    # Table for DATEX segment definitions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS segments (
            segment_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            from_location TEXT,
            to_location TEXT,
            description TEXT
        )
    ''')

    # Table for user configuration
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Table for collection status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collection_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_poll DATETIME,
            is_collecting BOOLEAN DEFAULT 0
        )
    ''')

    # Initialize collection status if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO collection_status (id, is_collecting)
        VALUES (1, 0)
    ''')

    conn.commit()
    conn.close()


def store_travel_time(segment_id: str, travel_time_seconds: int, timestamp: datetime):
    """Store a travel time measurement."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO travel_times
        (timestamp, segment_id, travel_time_seconds, day_of_week, hour, minute)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        segment_id,
        travel_time_seconds,
        timestamp.weekday(),  # 0 = Monday, 6 = Sunday
        timestamp.hour,
        timestamp.minute
    ))

    conn.commit()
    conn.close()


def store_segment(segment_id: str, name: str, from_location: str = None,
                  to_location: str = None, description: str = None):
    """Store or update a segment definition."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO segments
        (segment_id, name, from_location, to_location, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (segment_id, name, from_location, to_location, description))

    conn.commit()
    conn.close()


def get_all_segments() -> List[Dict]:
    """Get all available segments."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM segments ORDER BY name')
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_selected_segments() -> List[str]:
    """Get the list of selected segment IDs for analysis."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT value FROM config WHERE key = ?', ('selected_segments',))
    row = cursor.fetchone()
    conn.close()

    if row:
        # Stored as comma-separated values
        return row['value'].split(',')
    return []


def set_selected_segments(segment_ids: List[str]):
    """Set which segments to use for analysis."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO config (key, value)
        VALUES (?, ?)
    ''', ('selected_segments', ','.join(segment_ids)))

    conn.commit()
    conn.close()


def get_aggregated_travel_times(day_of_week: int, start_hour: int = 6,
                                end_hour: int = 10) -> List[Dict]:
    """
    Get aggregated travel times for a specific day of week.
    Returns average travel time for each 15-minute interval.

    Args:
        day_of_week: 0 = Monday, 6 = Sunday
        start_hour: Start hour (default 6 for 06:00)
        end_hour: End hour (default 10 for 10:00)
    """
    selected_segments = get_selected_segments()
    if not selected_segments:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # Build placeholders for segment IDs
    placeholders = ','.join('?' * len(selected_segments))

    query = f'''
        SELECT
            hour,
            CAST(minute / 15 AS INTEGER) * 15 as minute_bucket,
            AVG(travel_time_seconds) as avg_travel_time,
            COUNT(*) as sample_count
        FROM travel_times
        WHERE segment_id IN ({placeholders})
            AND day_of_week = ?
            AND hour >= ?
            AND hour < ?
        GROUP BY hour, minute_bucket
        ORDER BY hour, minute_bucket
    '''

    params = selected_segments + [day_of_week, start_hour, end_hour]
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_collection_status() -> Dict:
    """Get the current collection status."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM collection_status WHERE id = 1')
    row = cursor.fetchone()

    # Count days of data collected
    cursor.execute('''
        SELECT COUNT(DISTINCT DATE(timestamp)) as days_collected
        FROM travel_times
    ''')
    days_row = cursor.fetchone()

    conn.close()

    return {
        'is_collecting': bool(row['is_collecting']) if row else False,
        'last_poll': row['last_poll'] if row and row['last_poll'] else None,
        'days_collected': days_row['days_collected'] if days_row else 0
    }


def update_collection_status(is_collecting: bool = None, last_poll: datetime = None):
    """Update the collection status."""
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if is_collecting is not None:
        updates.append('is_collecting = ?')
        params.append(int(is_collecting))

    if last_poll is not None:
        updates.append('last_poll = ?')
        params.append(last_poll)

    if updates:
        query = f'UPDATE collection_status SET {", ".join(updates)} WHERE id = 1'
        cursor.execute(query, params)
        conn.commit()

    conn.close()


def get_data_quality_stats() -> Dict:
    """Get statistics about collected data quality."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            segment_id,
            COUNT(*) as total_samples,
            MIN(timestamp) as first_sample,
            MAX(timestamp) as last_sample
        FROM travel_times
        GROUP BY segment_id
    ''')

    rows = cursor.fetchall()
    conn.close()

    return {
        'segments': [dict(row) for row in rows],
        'total_samples': sum(row['total_samples'] for row in rows)
    }
