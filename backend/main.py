"""
FastAPI backend for Oslo Commute Time Optimizer - Enhanced Version.
Includes configuration management, logging, and improved scheduling.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging

# Initialize configuration and logging first
from config import config
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

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
from datex_client import test_datex_credentials
from datex_collector import initialize_segments

# Try to use new scheduler, fall back to old collector
try:
    from scheduler import (
        get_scheduler_status, start_scheduler, stop_scheduler, run_collection_now
    )
    USE_SCHEDULER = True
    logger.info("Using APScheduler for data collection")
except ImportError:
    from datex_collector import get_status as get_scheduler_status
    from datex_collector import start_collection as start_scheduler
    from datex_collector import stop_collection as stop_scheduler
    USE_SCHEDULER = False
    logger.warning("APScheduler not available, using threading-based collector")

# Initialize FastAPI app with enhanced documentation
app = FastAPI(
    title="Oslo Commute Time Optimizer",
    version="2.0.0",
    description="""
    Analyze commute times in Oslo, Norway using Google Maps predictions
    or self-collected DATEX data from Statens vegvesen.

    ## Features
    * Google Maps mode: Instant traffic predictions
    * DATEX mode: Free self-collected data
    * Visual analysis with best/worst time identification
    * Background data collection
    * Data quality monitoring

    ## Getting Started
    1. Configure API keys in .env file
    2. Initialize DATEX segments (if using DATEX)
    3. Start data collection (if using DATEX)
    4. Analyze your commute!
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models with documentation
class AnalyzeRequest(BaseModel):
    """Request model for commute analysis."""
    home: str = Field(..., description="Home address", example="Grønland, Oslo")
    work: str = Field(..., description="Work address", example="Aker Brygge, Oslo")
    day: str = Field(..., description="Day of week", example="Friday")
    mode: str = Field(..., description="Data source: 'google' or 'datex'", example="google")


class SegmentSelection(BaseModel):
    """Model for selecting DATEX segments."""
    segment_ids: List[str] = Field(..., description="List of segment IDs to track")


class CollectionControl(BaseModel):
    """Model for controlling data collection."""
    action: str = Field(..., description="Action: 'start' or 'stop'", example="start")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("=" * 60)
    logger.info("Oslo Commute Time Optimizer Starting")
    logger.info("=" * 60)

    # Log configuration
    config_summary = config.get_summary()
    for key, value in config_summary.items():
        logger.info(f"  {key}: {value}")

    # Initialize database
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialized")

    # Auto-start DATEX collection if configured
    if config.DATEX_AUTO_START and config.is_datex_configured():
        logger.info("Auto-starting DATEX collection...")
        try:
            start_scheduler()
            logger.info("DATEX collection started automatically")
        except Exception as e:
            logger.error(f"Failed to auto-start collection: {e}")

    logger.info("Application started successfully")
    logger.info(f"API documentation available at http://{config.HOST}:{config.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down...")
    try:
        stop_scheduler()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# API Endpoints with enhanced documentation
@app.post(
    "/api/analyze",
    summary="Analyze Commute Times",
    description="Analyze best and worst commute times for a specific route and day",
    response_description="Best/worst times and complete timeline"
)
async def analyze_commute(request: AnalyzeRequest):
    """
    Analyze commute times for a given route and day.

    - **Google Maps mode**: Provides instant predictions (requires API key)
    - **DATEX mode**: Uses collected historical data (requires 2-3 weeks of data)
    """
    logger.info(f"Analysis request: {request.mode} mode, {request.day}, {request.home} → {request.work}")

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
        if not config.is_google_maps_configured():
            raise HTTPException(
                status_code=400,
                detail="Google Maps API key not configured"
            )

        try:
            result = google_analyze(request.home, request.work, day_num)
            if 'error' in result:
                raise HTTPException(status_code=500, detail=result['error'])
            logger.info(f"Google Maps analysis completed: {len(result.get('all', []))} data points")
            return result
        except Exception as e:
            logger.error(f"Google Maps analysis failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    elif request.mode == "datex":
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
            logger.info(f"DATEX analysis completed: {len(result.get('all', []))} data points")
            return result
        except Exception as e:
            logger.error(f"DATEX analysis failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Mode must be 'google' or 'datex'")


@app.get(
    "/api/datex/status",
    summary="Get Collection Status",
    description="Get current DATEX data collection status and readiness"
)
async def datex_status():
    """Get detailed DATEX collection status."""
    status = get_scheduler_status()
    readiness = check_readiness_for_analysis()

    return {
        **status,
        'readiness': readiness
    }


@app.post(
    "/api/datex/segments",
    summary="Set Selected Segments",
    description="Configure which DATEX segments to use for analysis"
)
async def set_segments(selection: SegmentSelection):
    """Set which DATEX segments to track."""
    try:
        set_selected_segments(selection.segment_ids)
        logger.info(f"Selected {len(selection.segment_ids)} DATEX segments")
        return {
            'success': True,
            'selected_count': len(selection.segment_ids)
        }
    except Exception as e:
        logger.error(f"Failed to set segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/datex/segments/available",
    summary="Get Available Segments",
    description="List all available DATEX road segments"
)
async def get_available_segments():
    """Get list of available DATEX segments."""
    segments = get_all_segments()
    selected = get_selected_segments()

    for segment in segments:
        segment['is_selected'] = segment['segment_id'] in selected

    return {
        'segments': segments,
        'total_count': len(segments),
        'selected_count': len(selected)
    }


@app.post(
    "/api/datex/collection",
    summary="Control Data Collection",
    description="Start or stop background DATEX data collection"
)
async def control_collection(control: CollectionControl):
    """Start or stop DATEX data collection."""
    if control.action == "start":
        logger.info("Starting data collection...")
        start_scheduler()
        return {'success': True, 'message': 'Collection started'}
    elif control.action == "stop":
        logger.info("Stopping data collection...")
        stop_scheduler()
        return {'success': True, 'message': 'Collection stopped'}
    else:
        raise HTTPException(status_code=400, detail="Action must be 'start' or 'stop'")


@app.post(
    "/api/datex/collection/run-now",
    summary="Run Collection Now",
    description="Trigger an immediate data collection cycle"
)
async def trigger_collection():
    """Trigger immediate data collection."""
    if USE_SCHEDULER:
        try:
            success = run_collection_now()
            if success:
                return {'success': True, 'message': 'Collection triggered'}
            else:
                raise HTTPException(status_code=400, detail='Scheduler not running')
        except Exception as e:
            logger.error(f"Failed to trigger collection: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=501,
            detail="Manual trigger not supported with threading-based collector"
        )


@app.post(
    "/api/datex/initialize-segments",
    summary="Initialize Segments",
    description="Fetch segment definitions from DATEX API (run once)"
)
async def init_segments():
    """Fetch and store segment definitions from DATEX API."""
    if not config.is_datex_configured():
        raise HTTPException(
            status_code=400,
            detail="DATEX credentials not configured"
        )

    try:
        logger.info("Initializing DATEX segments...")
        success = initialize_segments()
        if success:
            segments = get_all_segments()
            logger.info(f"Initialized {len(segments)} segments")
            return {
                'success': True,
                'message': f'Initialized {len(segments)} segments',
                'segment_count': len(segments)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch segments")
    except Exception as e:
        logger.error(f"Segment initialization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/datex/quality",
    summary="Get Data Quality",
    description="Get statistics about collected data quality"
)
async def data_quality():
    """Get data quality statistics."""
    return get_data_quality()


@app.get(
    "/api/health",
    summary="Health Check",
    description="Check application health and configuration status"
)
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'version': '2.0.0',
        'google_maps_configured': config.is_google_maps_configured(),
        'datex_configured': config.is_datex_configured(),
        'database': 'ok',
        'scheduler_type': 'apscheduler' if USE_SCHEDULER else 'threading'
    }


@app.get(
    "/api/config",
    summary="Get Configuration",
    description="Get current application configuration (excludes sensitive data)"
)
async def get_config():
    """Get configuration summary."""
    return config.get_summary()


# Serve frontend
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the main HTML page."""
    return FileResponse(os.path.join(frontend_path, 'index.html'))


# Mount static files
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {config.HOST}:{config.PORT}")

    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
