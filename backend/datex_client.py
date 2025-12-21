"""
DATEX II API client for fetching travel time data from Statens vegvesen.
"""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET


DATEX_USERNAME = os.getenv('DATEX_USERNAME')
DATEX_PASSWORD = os.getenv('DATEX_PASSWORD')

TRAVEL_TIME_URL = 'https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/GetTravelTimeData/pullsnapshotdata'
LOCATIONS_URL = 'https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/GetPredefinedTravelTimeLocations/pullsnapshotdata'


def parse_datex_namespace(element):
    """Extract namespace from DATEX XML."""
    tag = element.tag
    if '}' in tag:
        return tag.split('}')[0] + '}'
    return ''


def fetch_travel_time_data() -> Optional[List[Dict]]:
    """
    Fetch current travel time data from DATEX API.

    Returns:
        List of dicts with segment_id, travel_time_seconds, timestamp
    """
    if not DATEX_USERNAME or not DATEX_PASSWORD:
        raise ValueError("DATEX_USERNAME and DATEX_PASSWORD environment variables must be set")

    try:
        response = requests.get(
            TRAVEL_TIME_URL,
            auth=(DATEX_USERNAME, DATEX_PASSWORD),
            timeout=30
        )
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)
        ns = parse_datex_namespace(root)

        travel_times = []
        timestamp = datetime.now()

        # Find all elaboratedData elements
        for elaborated_data in root.findall(f'.//{ns}elaboratedData'):
            # Look for travelTimeData elements
            for travel_time_elem in elaborated_data.findall(f'.//{ns}travelTimeData'):
                try:
                    # Get segment ID
                    segment_id_elem = travel_time_elem.find(f'.//{ns}id')
                    if segment_id_elem is None:
                        continue

                    segment_id = segment_id_elem.text

                    # Get travel time
                    travel_time_elem_data = travel_time_elem.find(f'.//{ns}travelTime')
                    if travel_time_elem_data is None:
                        continue

                    travel_time_seconds = int(float(travel_time_elem_data.text))

                    # Check if free flow (we want actual travel time, not free flow)
                    free_flow = travel_time_elem.find(f'.//{ns}freeFlowTravelTime')
                    if free_flow is not None:
                        # Use actual travel time
                        pass

                    travel_times.append({
                        'segment_id': segment_id,
                        'travel_time_seconds': travel_time_seconds,
                        'timestamp': timestamp
                    })

                except (ValueError, AttributeError) as e:
                    # Skip malformed entries
                    continue

        return travel_times if travel_times else None

    except requests.exceptions.RequestException as e:
        print(f"DATEX API request error: {e}")
        return None
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return None


def fetch_segment_locations() -> Optional[List[Dict]]:
    """
    Fetch segment location definitions from DATEX API.

    Returns:
        List of dicts with segment info (id, name, from, to, description)
    """
    if not DATEX_USERNAME or not DATEX_PASSWORD:
        raise ValueError("DATEX_USERNAME and DATEX_PASSWORD environment variables must be set")

    try:
        response = requests.get(
            LOCATIONS_URL,
            auth=(DATEX_USERNAME, DATEX_PASSWORD),
            timeout=30
        )
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)
        ns = parse_datex_namespace(root)

        segments = []

        # Find all predefinedLocationContainer elements
        for container in root.findall(f'.//{ns}predefinedLocationContainer'):
            for location in container.findall(f'.//{ns}predefinedLocation'):
                try:
                    # Get segment ID
                    id_elem = location.find(f'.//{ns}id')
                    if id_elem is None:
                        continue

                    segment_id = id_elem.text

                    # Get name/description
                    name_elem = location.find(f'.//{ns}name') or location.find(f'.//{ns}descriptor')
                    name = name_elem.find(f'.//{ns}value').text if name_elem is not None else segment_id

                    # Try to find from/to locations
                    from_loc = None
                    to_loc = None

                    # Look for linear location which contains from/to
                    linear = location.find(f'.//{ns}linear')
                    if linear is not None:
                        from_elem = linear.find(f'.//{ns}from')
                        to_elem = linear.find(f'.//{ns}to')

                        if from_elem is not None:
                            from_name = from_elem.find(f'.//{ns}name')
                            if from_name is not None:
                                from_value = from_name.find(f'.//{ns}value')
                                if from_value is not None:
                                    from_loc = from_value.text

                        if to_elem is not None:
                            to_name = to_elem.find(f'.//{ns}name')
                            if to_name is not None:
                                to_value = to_name.find(f'.//{ns}value')
                                if to_value is not None:
                                    to_loc = to_value.text

                    # Filter for Oslo area segments (optional, can be removed for all Norway)
                    # Common Oslo keywords: Oslo, E18, E6, Ring 3, Rv 4, etc.
                    oslo_keywords = ['oslo', 'e18', 'e6', 'ring 3', 'rv 4', 'lysaker', 'sandvika',
                                   'asker', 'drammen', 'lørenskog', 'romerike']

                    name_lower = name.lower()
                    is_oslo_area = any(keyword in name_lower for keyword in oslo_keywords)
                    if from_loc:
                        is_oslo_area = is_oslo_area or any(keyword in from_loc.lower() for keyword in oslo_keywords)
                    if to_loc:
                        is_oslo_area = is_oslo_area or any(keyword in to_loc.lower() for keyword in oslo_keywords)

                    # Only include Oslo-area segments to keep the list manageable
                    if is_oslo_area:
                        segments.append({
                            'segment_id': segment_id,
                            'name': name,
                            'from_location': from_loc,
                            'to_location': to_loc,
                            'description': f"{from_loc} → {to_loc}" if from_loc and to_loc else name
                        })

                except (ValueError, AttributeError) as e:
                    continue

        return segments if segments else None

    except requests.exceptions.RequestException as e:
        print(f"DATEX API request error: {e}")
        return None
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return None


def test_datex_credentials() -> bool:
    """Test if DATEX credentials are valid."""
    if not DATEX_USERNAME or not DATEX_PASSWORD:
        return False

    try:
        response = requests.get(
            TRAVEL_TIME_URL,
            auth=(DATEX_USERNAME, DATEX_PASSWORD),
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False
