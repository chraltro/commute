"""
FastAPI backend for Oslo Commute Time Optimizer.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

# Import our modules
from database import (
    init_database, get_all_segments, get_selected_segments,
    set_selected_segments, get_collection_status
)
from google_maps import analyze_commute_times as google_analyze, test_api_key
from datex_analyzer import (
    analyze_commute_times as datex_analyze,
    get_data_quality, check_readiness_for_analysis
)
from datex_collector import (
    get_collector, start_collection, stop_collection,
    initialize_segments, get_status
)
from datex_client import test_datex_credentials

# Initialize FastAPI app
app = FastAPI(title="Oslo Commute Time Optimizer", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()


# Pydantic models for request/response
class AnalyzeRequest(BaseModel):
    home: str
    work: str
    day: str  # Monday, Tuesday, etc.
    mode: str  # "google" or "datex"


class SegmentSelection(BaseModel):
    segment_ids: List[str]


class CollectionControl(BaseModel):
    action: str  # "start" or "stop"


# API Endpoints
@app.post("/api/analyze")
async def analyze_commute(request: AnalyzeRequest):
    """
    Analyze commute times for a given route and day.
    """
    # Convert day name to number
    days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    day_lower = request.day.lower()
    if day_lower not in days:
        raise HTTPException(status_code=400, detail="Invalid day of week")

    day_num = days[day_lower]

    if request.mode == "google":
        # Use Google Maps API
        if not test_api_key():
            raise HTTPException(
                status_code=400,
                detail="Google Maps API key not configured or invalid"
            )

        try:
            result = google_analyze(request.home, request.work, day_num)
            if 'error' in result:
                raise HTTPException(status_code=500, detail=result['error'])
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif request.mode == "datex":
        # Use collected DATEX data
        readiness = check_readiness_for_analysis()
        if not readiness['ready']:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': readiness['reason'],
                    'recommendation': readiness['recommendation']
                }
            )

        try:
            result = datex_analyze(day_num)
            if 'error' in result:
                raise HTTPException(status_code=400, detail=result)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Mode must be 'google' or 'datex'")


@app.get("/api/datex/status")
async def datex_status():
    """
    Get DATEX collection status.
    """
    status = get_status()
    readiness = check_readiness_for_analysis()

    return {
        **status,
        'readiness': readiness
    }


@app.post("/api/datex/segments")
async def set_segments(selection: SegmentSelection):
    """
    Set which DATEX segments to use for analysis.
    """
    try:
        set_selected_segments(selection.segment_ids)
        return {
            'success': True,
            'selected_count': len(selection.segment_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datex/segments/available")
async def get_available_segments():
    """
    Get list of available DATEX segments.
    """
    segments = get_all_segments()
    selected = get_selected_segments()

    # Mark which segments are selected
    for segment in segments:
        segment['is_selected'] = segment['segment_id'] in selected

    return {
        'segments': segments,
        'total_count': len(segments),
        'selected_count': len(selected)
    }


@app.post("/api/datex/collection")
async def control_collection(control: CollectionControl):
    """
    Start or stop DATEX data collection.
    """
    if control.action == "start":
        start_collection()
        return {'success': True, 'message': 'Collection started'}
    elif control.action == "stop":
        stop_collection()
        return {'success': True, 'message': 'Collection stopped'}
    else:
        raise HTTPException(status_code=400, detail="Action must be 'start' or 'stop'")


@app.post("/api/datex/initialize-segments")
async def init_segments():
    """
    Fetch and store segment definitions from DATEX API.
    Should be run once during setup.
    """
    if not test_datex_credentials():
        raise HTTPException(
            status_code=400,
            detail="DATEX credentials not configured or invalid"
        )

    try:
        success = initialize_segments()
        if success:
            segments = get_all_segments()
            return {
                'success': True,
                'message': f'Initialized {len(segments)} segments',
                'segment_count': len(segments)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch segments")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datex/quality")
async def data_quality():
    """
    Get data quality statistics.
    """
    return get_data_quality()


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        'status': 'healthy',
        'google_maps_configured': test_api_key(),
        'datex_configured': test_datex_credentials()
    }


# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')

@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    return FileResponse(os.path.join(frontend_path, 'index.html'))


# Mount static files for CSS/JS
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
