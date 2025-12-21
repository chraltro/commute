"""
Google Maps Directions API integration for predicting travel times.
"""
import os
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional


API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
DIRECTIONS_URL = 'https://maps.googleapis.com/maps/api/directions/json'


def get_next_weekday_date(target_weekday: int) -> datetime:
    """
    Get the next occurrence of a specific weekday.

    Args:
        target_weekday: 0 = Monday, 6 = Sunday

    Returns:
        datetime object for the next occurrence of that weekday
    """
    today = datetime.now()
    days_ahead = target_weekday - today.weekday()

    # If the target day is today or has passed this week, get next week's
    if days_ahead <= 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead)


def get_travel_time(origin: str, destination: str, departure_time: datetime) -> Optional[Dict]:
    """
    Get predicted travel time from Google Maps API.

    Args:
        origin: Starting address
        destination: Ending address
        departure_time: When to depart

    Returns:
        Dict with duration and duration_in_traffic in seconds, or None if error
    """
    if not API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    params = {
        'origin': origin,
        'destination': destination,
        'departure_time': int(departure_time.timestamp()),
        'traffic_model': 'best_guess',
        'key': API_KEY
    }

    try:
        response = requests.get(DIRECTIONS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            print(f"Google Maps API error: {data['status']}")
            if 'error_message' in data:
                print(f"Error message: {data['error_message']}")
            return None

        route = data['routes'][0]
        leg = route['legs'][0]

        return {
            'duration': leg['duration']['value'],  # Normal duration in seconds
            'duration_in_traffic': leg.get('duration_in_traffic', {}).get('value', leg['duration']['value']),
            'distance': leg['distance']['value'],  # Distance in meters
            'start_address': leg['start_address'],
            'end_address': leg['end_address']
        }

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


def analyze_commute_times(origin: str, destination: str, day_of_week: int,
                          start_hour: int = 6, end_hour: int = 10,
                          interval_minutes: int = 15) -> Dict:
    """
    Analyze commute times throughout the morning for a specific day.

    Args:
        origin: Home address
        destination: Work address
        day_of_week: 0 = Monday, 6 = Sunday
        start_hour: Start hour for analysis (default 6)
        end_hour: End hour for analysis (default 10)
        interval_minutes: Minutes between each query (default 15)

    Returns:
        Dict with best, worst, and all travel times
    """
    target_date = get_next_weekday_date(day_of_week)
    results = []

    # Generate all departure times
    current_hour = start_hour
    current_minute = 0

    while current_hour < end_hour or (current_hour == end_hour and current_minute == 0):
        departure_time = target_date.replace(
            hour=current_hour,
            minute=current_minute,
            second=0,
            microsecond=0
        )

        travel_data = get_travel_time(origin, destination, departure_time)

        if travel_data:
            duration_minutes = travel_data['duration_in_traffic'] / 60
            results.append({
                'time': f"{current_hour:02d}:{current_minute:02d}",
                'duration_seconds': travel_data['duration_in_traffic'],
                'duration_minutes': round(duration_minutes, 1),
                'distance_km': round(travel_data['distance'] / 1000, 1)
            })

        # Increment time
        current_minute += interval_minutes
        if current_minute >= 60:
            current_minute = 0
            current_hour += 1

    if not results:
        return {
            'error': 'No data could be retrieved from Google Maps API',
            'all': []
        }

    # Find best and worst times
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
            'origin': origin,
            'destination': destination,
            'day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week],
            'analysis_date': target_date.strftime('%Y-%m-%d')
        }
    }


def test_api_key() -> bool:
    """Test if the Google Maps API key is valid."""
    if not API_KEY:
        return False

    params = {
        'origin': 'Oslo',
        'destination': 'Bergen',
        'key': API_KEY
    }

    try:
        response = requests.get(DIRECTIONS_URL, params=params, timeout=5)
        data = response.json()
        return data['status'] in ['OK', 'ZERO_RESULTS']
    except Exception:
        return False
