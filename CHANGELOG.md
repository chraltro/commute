# Changelog

All notable changes to the Oslo Commute Time Optimizer project will be documented in this file.

## [2.0.0] - 2024-12-21

### Added - Major Enhancements

#### Configuration Management
- **New `config.py` module**: Centralized configuration with environment variable support
- All settings now configurable via environment variables
- Configuration validation and summary endpoints
- Support for custom analysis time ranges, polling intervals, and more

#### Advanced Scheduling
- **New `scheduler.py` module**: Robust APScheduler-based data collection
- Automatic retry on failures
- Job execution monitoring with success/error tracking
- Manual trigger capability for immediate collection
- Falls back to threading-based collector if APScheduler unavailable

#### Comprehensive Logging
- **New `logging_config.py` module**: Structured logging throughout application
- Console and file logging support
- Configurable log levels
- Rotating file handler (10MB max, 5 backups)
- Detailed error tracking with stack traces

#### Docker Support
- **Dockerfile**: Production-ready containerization
- **docker-compose.yml**: One-command deployment
- **.dockerignore**: Optimized build context
- Health checks and automatic restart
- Volume mounting for data persistence

#### Enhanced API
- **Upgraded to FastAPI 2.0.0**: Enhanced documentation and performance
- Interactive API docs at `/docs` (Swagger UI)
- Alternative docs at `/redoc` (ReDoc)
- New `/api/config` endpoint: View configuration
- New `/api/datex/collection/run-now` endpoint: Trigger immediate collection
- Enhanced `/api/health` endpoint: Detailed health status
- Better error messages and validation

#### Demo/Testing Tools
- **New `demo_data.py` module**: Generate realistic test data
- Seed database with 21 days of historical data
- No API keys required for testing
- Realistic Oslo traffic patterns
- Command-line interface for easy data generation

#### System Monitoring
- **New `system_status.py` module**: System health monitoring
- CPU, memory, and disk usage tracking
- Database statistics (size, record counts, date ranges)
- Collection status tracking
- Comprehensive status endpoint

### Changed

#### Backend Improvements
- `main.py`: Completely rewritten with enhanced features
- `database.py`: Now uses centralized configuration
- Better error handling throughout
- Improved startup/shutdown procedures
- Auto-start capability for DATEX collection
- Enhanced CORS configuration

#### Frontend Improvements
- Planned: System status dashboard tab
- Planned: Real-time health monitoring display
- Planned: Manual collection trigger button

### Configuration

#### New Environment Variables
```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
LOG_FILE=/path/to/logfile.log

# Database
DB_PATH=/path/to/commute.db

# DATEX Collection
DATEX_POLL_INTERVAL_SECONDS=300
DATEX_TIMEOUT_SECONDS=30
DATEX_AUTO_START=false

# Analysis
ANALYSIS_START_HOUR=6
ANALYSIS_END_HOUR=10
ANALYSIS_INTERVAL_MINUTES=15
MIN_SAMPLES_FOR_QUALITY=3

# Google Maps
GOOGLE_MAPS_TIMEOUT_SECONDS=10
GOOGLE_MAPS_TRAFFIC_MODEL=best_guess

# CORS
CORS_ORIGINS=*
```

### Deployment

#### Quick Start with Docker
```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t oslo-commute-optimizer .
docker run -p 8000:8000 -v $(pwd)/data:/app/data oslo-commute-optimizer
```

#### Quick Start with Demo Data
```bash
# Seed 21 days of demo data
python backend/demo_data.py --seed 21

# Start the application
./run.sh
```

### API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- Try-it-out functionality
- Request/response schemas
- Example values
- Parameter descriptions

### Backward Compatibility

- Original `main.py` backed up as `main_old.py`
- All original endpoints remain functional
- No breaking changes to API responses
- Existing databases work without migration

## [1.0.0] - 2024-12-21

### Initial Release

- Google Maps integration for instant predictions
- DATEX integration for free data collection
- SQLite database for local storage
- Background data collection (threading-based)
- FastAPI REST API
- Simple HTML/CSS/JS frontend
- Chart.js visualization
- Best/worst time analysis
- Basic configuration via .env file
