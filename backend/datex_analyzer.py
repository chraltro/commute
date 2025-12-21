"""
Analyzer for aggregating and analyzing collected DATEX travel time data.
"""
from typing import Dict, List
from database import get_aggregated_travel_times, get_selected_segments, get_data_quality_stats


def analyze_commute_times(day_of_week: int, start_hour: int = 6, end_hour: int = 10) -> Dict:
    """
    Analyze collected travel time data for a specific day of week.

    Args:
        day_of_week: 0 = Monday, 6 = Sunday
        start_hour: Start hour for analysis (default 6)
        end_hour: End hour for analysis (default 10)

    Returns:
        Dict with best, worst, and all travel times, or error if insufficient data
    """
    selected_segments = get_selected_segments()

    if not selected_segments:
        return {
            'error': 'No DATEX segments selected. Please select segments in settings.',
            'all': []
        }

    # Get aggregated data
    data = get_aggregated_travel_times(day_of_week, start_hour, end_hour)

    if not data:
        return {
            'error': 'Insufficient data collected. Need at least 2-3 weeks of data for reliable analysis.',
            'all': [],
            'help': 'Make sure data collection is running and check back after a few weeks.'
        }

    # Check if we have enough samples
    min_samples_needed = 3  # At least 3 samples per time slot for reliability
    low_quality_slots = [d for d in data if d['sample_count'] < min_samples_needed]

    if len(low_quality_slots) > len(data) * 0.5:  # More than 50% of slots have low quality
        return {
            'error': 'Insufficient data quality. Need more data collection time.',
            'all': [],
            'help': f'Only {len(data) - len(low_quality_slots)} out of {len(data)} time slots have enough samples.'
        }

    # Build results
    results = []
    for entry in data:
        time_str = f"{entry['hour']:02d}:{entry['minute_bucket']:02d}"
        duration_minutes = round(entry['avg_travel_time'] / 60, 1)

        results.append({
            'time': time_str,
            'duration_seconds': int(entry['avg_travel_time']),
            'duration_minutes': duration_minutes,
            'sample_count': entry['sample_count']
        })

    if not results:
        return {
            'error': 'No data available for the selected time range.',
            'all': []
        }

    # Find best and worst times
    best = min(results, key=lambda x: x['duration_seconds'])
    worst = max(results, key=lambda x: x['duration_seconds'])
    difference_minutes = round((worst['duration_seconds'] - best['duration_seconds']) / 60, 1)

    return {
        'best': {
            'time': best['time'],
            'duration_minutes': best['duration_minutes'],
            'sample_count': best['sample_count']
        },
        'worst': {
            'time': worst['time'],
            'duration_minutes': worst['duration_minutes'],
            'sample_count': worst['sample_count']
        },
        'difference_minutes': difference_minutes,
        'all': results,
        'metadata': {
            'day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week],
            'segments_used': len(selected_segments),
            'data_source': 'DATEX (collected)'
        }
    }


def get_data_quality() -> Dict:
    """
    Get information about data quality and collection status.

    Returns:
        Dict with statistics about collected data
    """
    stats = get_data_quality_stats()
    selected = get_selected_segments()

    segment_stats = []
    for seg in stats['segments']:
        segment_stats.append({
            'segment_id': seg['segment_id'],
            'total_samples': seg['total_samples'],
            'first_sample': seg['first_sample'],
            'last_sample': seg['last_sample'],
            'is_selected': seg['segment_id'] in selected
        })

    # Calculate days of data
    days_collected = set()
    for seg in stats['segments']:
        if seg['first_sample'] and seg['last_sample']:
            # This is simplified - actual day count is in get_collection_status
            pass

    return {
        'total_samples': stats['total_samples'],
        'segments': segment_stats,
        'selected_segments': len(selected),
        'quality': _assess_quality(stats)
    }


def _assess_quality(stats: Dict) -> str:
    """Assess overall data quality."""
    total = stats['total_samples']

    if total == 0:
        return 'No data'
    elif total < 500:
        return 'Insufficient (need more time)'
    elif total < 2000:
        return 'Fair (1-2 weeks of data)'
    elif total < 5000:
        return 'Good (2-3 weeks of data)'
    else:
        return 'Excellent (3+ weeks of data)'


def check_readiness_for_analysis() -> Dict:
    """
    Check if there's enough data for meaningful analysis.

    Returns:
        Dict with readiness status and recommendations
    """
    selected = get_selected_segments()
    stats = get_data_quality_stats()

    if not selected:
        return {
            'ready': False,
            'reason': 'No segments selected',
            'recommendation': 'Select DATEX segments that match your route in the settings.'
        }

    if stats['total_samples'] == 0:
        return {
            'ready': False,
            'reason': 'No data collected yet',
            'recommendation': 'Start data collection and wait 2-3 weeks for reliable results.'
        }

    if stats['total_samples'] < 500:
        return {
            'ready': False,
            'reason': 'Insufficient data (less than 1 week)',
            'recommendation': 'Keep collecting data. You have some data, but need 2-3 weeks for reliable patterns.'
        }

    if stats['total_samples'] < 2000:
        return {
            'ready': True,
            'reason': 'Limited data (1-2 weeks)',
            'recommendation': 'You can see trends, but results will improve with more data collection time.'
        }

    return {
        'ready': True,
        'reason': 'Sufficient data available',
        'recommendation': 'Data quality is good. Analysis results should be reliable.'
    }
