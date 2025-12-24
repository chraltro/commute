"""
Demo data generator for testing without API keys.
Creates realistic sample travel time data for demonstration purposes.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict
from database import store_travel_time, store_segment, set_selected_segments, init_database


def generate_realistic_travel_times(base_time: int, time_of_day: str) -> int:
    """
    Generate realistic travel times based on time of day.

    Args:
        base_time: Base travel time in seconds
        time_of_day: Morning hour (0-23)

    Returns:
        Travel time in seconds with realistic variation
    """
    hour = int(time_of_day.split(':')[0])

    # Peak traffic multipliers for Oslo
    if 7 <= hour <= 9:  # Morning rush hour
        multiplier = random.uniform(1.4, 1.8)
    elif 6 <= hour < 7:  # Early morning
        multiplier = random.uniform(1.1, 1.3)
    elif 9 <= hour < 10:  # Late morning
        multiplier = random.uniform(1.2, 1.4)
    else:  # Off-peak
        multiplier = random.uniform(1.0, 1.1)

    # Add some random variation
    variation = random.uniform(0.95, 1.05)

    return int(base_time * multiplier * variation)


def generate_demo_segments() -> List[Dict]:
    """Generate demo DATEX segments."""
    segments = [
        {
            'segment_id': 'DEMO_E18_LYSAKER_OSLO',
            'name': 'E18 Lysaker - Oslo sentrum',
            'from_location': 'Lysaker',
            'to_location': 'Oslo sentrum',
            'description': 'E18 Lysaker → Oslo sentrum'
        },
        {
            'segment_id': 'DEMO_E6_ROMERIKE_OSLO',
            'name': 'E6 Romerike - Oslo',
            'from_location': 'Romerike',
            'to_location': 'Oslo',
            'description': 'E6 Romerike → Oslo'
        },
        {
            'segment_id': 'DEMO_RING3_NORD',
            'name': 'Ring 3 Nord',
            'from_location': 'Nydalen',
            'to_location': 'Sinsen',
            'description': 'Ring 3 Nydalen → Sinsen'
        }
    ]
    return segments


def seed_demo_data(days: int = 21, segments: List[str] = None):
    """
    Seed database with demo data.

    Args:
        days: Number of days of historical data to generate (default 21 = 3 weeks)
        segments: List of segment IDs to generate data for (uses demo segments if None)
    """
    print("Seeding demo data...")

    # Initialize database
    init_database()

    # Create demo segments
    demo_segments = generate_demo_segments()
    for segment in demo_segments:
        store_segment(**segment)
        print(f"Created segment: {segment['name']}")

    # Select demo segments
    segment_ids = [s['segment_id'] for s in demo_segments]
    set_selected_segments(segment_ids)
    print(f"Selected {len(segment_ids)} segments for tracking")

    # Base travel times for each segment (in seconds)
    base_times = {
        'DEMO_E18_LYSAKER_OSLO': 900,  # 15 minutes base
        'DEMO_E6_ROMERIKE_OSLO': 1200,  # 20 minutes base
        'DEMO_RING3_NORD': 600,  # 10 minutes base
    }

    # Generate data for past N days
    total_records = 0
    start_date = datetime.now() - timedelta(days=days)

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        # Generate data every 5 minutes from 5:00 to 11:00
        for hour in range(5, 11):
            for minute in range(0, 60, 5):
                timestamp = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                time_str = f"{hour:02d}:{minute:02d}"

                # Generate travel times for each segment
                for segment_id, base_time in base_times.items():
                    travel_time = generate_realistic_travel_times(base_time, time_str)

                    store_travel_time(
                        segment_id=segment_id,
                        travel_time_seconds=travel_time,
                        timestamp=timestamp
                    )
                    total_records += 1

        if (day_offset + 1) % 7 == 0:
            print(f"Generated data for {day_offset + 1}/{days} days ({total_records} records)...")

    print(f"✅ Demo data seeded successfully!")
    print(f"   Total records: {total_records}")
    print(f"   Date range: {start_date.date()} to {datetime.now().date()}")
    print(f"   Segments: {len(segment_ids)}")


def generate_google_maps_demo_response(day: str = "Friday") -> Dict:
    """
    Generate a demo response that looks like Google Maps results.
    Useful for frontend testing without API keys.
    """
    results = []

    for hour in range(6, 10):
        for minute in [0, 15, 30, 45]:
            if hour == 10 and minute > 0:
                break

            time_str = f"{hour:02d}:{minute:02d}"

            # Simulate realistic Oslo commute times
            base_duration = 25  # 25 minutes base
            if 7 <= hour <= 8:  # Peak hour
                duration = base_duration + random.uniform(10, 20)
            elif hour == 9:  # Late morning
                duration = base_duration + random.uniform(5, 10)
            else:
                duration = base_duration + random.uniform(0, 5)

            results.append({
                'time': time_str,
                'duration_seconds': int(duration * 60),
                'duration_minutes': round(duration, 1),
                'distance_km': round(random.uniform(12, 15), 1)
            })

    best = min(results, key=lambda x: x['duration_seconds'])
    worst = max(results, key=lambda x: x['duration_seconds'])
    difference_minutes = round((worst['duration_seconds'] - best['duration_seconds']) / 60, 1)

    return {
        'best': {
            'time': best['time'],
            'duration_minutes': best['duration_minutes']
        },
        'worst': {
            'time': worst['time'],
            'duration_minutes': worst['duration_minutes']
        },
        'difference_minutes': difference_minutes,
        'all': results,
        'metadata': {
            'origin': 'Demo: Grønland, Oslo',
            'destination': 'Demo: Aker Brygge, Oslo',
            'day': day,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'note': 'This is demo data for testing purposes'
        }
    }


if __name__ == '__main__':
    import sys

    if '--seed' in sys.argv:
        # Seed demo data
        days = 21
        if len(sys.argv) > sys.argv.index('--seed') + 1:
            try:
                days = int(sys.argv[sys.argv.index('--seed') + 1])
            except ValueError:
                pass

        seed_demo_data(days=days)

    elif '--demo-response' in sys.argv:
        # Generate demo response
        import json
        response = generate_google_maps_demo_response()
        print(json.dumps(response, indent=2))

    else:
        print("Usage:")
        print("  python demo_data.py --seed [days]        # Seed demo DATEX data")
        print("  python demo_data.py --demo-response      # Generate demo Google Maps response")
