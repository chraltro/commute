# Oslo Commute Time Optimizer

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](Dockerfile)

A production-ready web application to find the best and worst times to drive to work in Oslo, Norway. Analyze your commute using either Google Maps predictions or self-collected data from Norway's free DATEX traffic system.

## ✨ Features

### Core Functionality
- **Dual Data Sources:**
  - **Google Maps Mode:** Instant results using traffic predictions API
  - **DATEX Mode:** Free self-collected data from Statens vegvesen
- **Visual Analysis:** Beautiful Chart.js visualizations of travel times (06:00-10:00)
- **Smart Insights:** Best/worst time identification with time savings calculation
- **Background Collection:** Automated DATEX polling with APScheduler
- **Data Quality Tracking:** Real-time monitoring and readiness indicators

### Version 2.0 Enhancements 🚀
- **📝 Configuration Management:** Centralized config with environment variables
- **🔄 Advanced Scheduling:** APScheduler-based collection with retry logic
- **📊 System Monitoring:** CPU, memory, disk, and database statistics
- **🐳 Docker Support:** Production-ready containerization
- **📚 API Documentation:** Interactive Swagger UI and ReDoc
- **🧪 Demo Mode:** Test with realistic data (no API keys required)
- **📈 Enhanced Logging:** Structured logging with file rotation
- **⚡ Health Checks:** Comprehensive status endpoints

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd commute-optimizer

# Create .env file
cp .env.example .env
# Edit .env with your API keys (optional for demo)

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8000
```

### Option 2: Python (Local Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with demo data (no API keys needed)
python backend/demo_data.py --seed 21
./run.sh

# Access the application
open http://localhost:8000
```

### Option 3: Try Demo Mode First

```bash
# Seed 3 weeks of realistic demo data
python backend/demo_data.py --seed 21

# Start the application
./run.sh

# Use DATEX mode in the web UI (works without API keys!)
```

## 📖 Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment, systemd, nginx setup
- **[Changelog](CHANGELOG.md)** - Version history and release notes
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

## 🔧 Configuration

### Minimal Setup (.env)

```bash
# Required: At least one data source
GOOGLE_MAPS_API_KEY=your_key_here        # For instant predictions
# OR
DATEX_USERNAME=your_username             # For free data collection
DATEX_PASSWORD=your_password
```

### Advanced Configuration

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
LOG_FILE=/var/log/commute-optimizer.log

# DATEX Collection
DATEX_POLL_INTERVAL_SECONDS=300          # Poll every 5 minutes
DATEX_AUTO_START=true                    # Auto-start collection on startup

# Analysis
ANALYSIS_START_HOUR=6                    # Morning start time
ANALYSIS_END_HOUR=10                     # Morning end time
ANALYSIS_INTERVAL_MINUTES=15             # Query interval

# See .env.example for all options
```

## 🏗️ Architecture

```
commute-optimizer/
├── backend/                    # Python backend
│   ├── main.py                # FastAPI application (v2.0)
│   ├── config.py              # Configuration management
│   ├── logging_config.py      # Logging setup
│   ├── scheduler.py           # APScheduler-based collection
│   ├── database.py            # SQLite operations
│   ├── google_maps.py         # Google Maps integration
│   ├── datex_client.py        # DATEX API client
│   ├── datex_analyzer.py      # Data analysis
│   ├── demo_data.py           # Demo data generator
│   └── system_status.py       # Health monitoring
├── frontend/                   # HTML/CSS/JS frontend
│   ├── index.html
│   ├── app.js
│   └── style.css
├── data/                       # SQLite database (auto-created)
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Docker Compose config
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── DEPLOYMENT.md              # Deployment guide
└── CHANGELOG.md               # Version history
```

## 🎯 Usage

### Web Interface

1. **Analyze Commute Tab:**
   - Enter home and work addresses
   - Select day of week
   - Choose Google Maps or DATEX mode
   - Click "Analyze Commute"

2. **DATEX Settings Tab:**
   - Initialize segments (one-time setup)
   - Select route segments
   - Start/stop data collection
   - Monitor data quality

### API Endpoints

```bash
# Analyze commute
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"home":"Grønland, Oslo","work":"Aker Brygge, Oslo","day":"Friday","mode":"google"}'

# Get health status
curl http://localhost:8000/api/health

# View API documentation
open http://localhost:8000/docs
```

### Demo Data

```bash
# Generate demo data (21 days)
python backend/demo_data.py --seed 21

# Generate more data (30 days)
python backend/demo_data.py --seed 30

# Generate demo response (testing)
python backend/demo_data.py --demo-response
```

## 🔍 API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze commute times |
| `/api/health` | GET | Health check |
| `/api/config` | GET | Configuration summary |
| `/api/datex/status` | GET | Collection status |
| `/api/datex/collection` | POST | Start/stop collection |
| `/api/datex/collection/run-now` | POST | Trigger immediate collection |
| `/api/datex/segments/available` | GET | List available segments |
| `/api/datex/segments` | POST | Set selected segments |
| `/api/datex/initialize-segments` | POST | Fetch segments from API |
| `/api/datex/quality` | GET | Data quality stats |

## 🐳 Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Or use Docker CLI
docker build -t oslo-commute-optimizer .
docker run -d -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e GOOGLE_MAPS_API_KEY=your_key \
  --restart unless-stopped \
  oslo-commute-optimizer
```

## 🔐 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive production deployment guides including:
- Nginx reverse proxy setup
- SSL/TLS configuration with Let's Encrypt
- Systemd service configuration
- Security best practices
- Performance tuning
- Backup strategies

## 🧪 Testing

```bash
# Run setup test
python test_setup.py

# Expected output:
# ✅ Dependencies: PASS
# ✅ Imports: PASS
# ✅ Database: PASS
# ⚠️  Google Maps: NOT CONFIGURED (optional)
# ⚠️  DATEX: NOT CONFIGURED (optional)
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "google_maps_configured": true,
  "datex_configured": true,
  "database": "ok",
  "scheduler_type": "apscheduler"
}
```

### System Status

```bash
curl http://localhost:8000/api/config
```

## 🛠️ Development

### Prerequisites
- Python 3.8+
- pip
- (Optional) Docker

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in debug mode
DEBUG=true python backend/main.py
```

### Project Structure

- **Backend:** FastAPI with SQLite
- **Frontend:** Vanilla HTML/CSS/JS with Chart.js
- **Scheduling:** APScheduler for background tasks
- **Containerization:** Docker with multi-stage builds

## 🐛 Troubleshooting

### Common Issues

**Import Errors:**
```bash
pip install -r requirements.txt --upgrade
```

**Port Already in Use:**
```bash
PORT=8080 python backend/main.py
```

**Database Locked:**
```bash
pkill -f "python backend/main.py"
rm data/commute.db-journal
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more troubleshooting tips.

## 📈 Performance

- **Google Maps:** Each analysis makes 17 API calls (15-min intervals)
- **DATEX:** Polls every 5 minutes, storing ~100-200 measurements/hour
- **Database:** ~1MB per week of DATEX collection
- **Memory:** ~50-100MB typical usage
- **CPU:** Minimal (<5% on modern hardware)

## 🗺️ Oslo Coverage

DATEX covers major Oslo routes:
- E18 (Drammen - Oslo)
- E6 (Romerike - Oslo)
- Ring 3
- Rv 4
- Major arteries (Lysaker, Sandvika, Asker, Lørenskog)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues or questions:
1. Check the [DEPLOYMENT.md](DEPLOYMENT.md) guide
2. Review the [CHANGELOG.md](CHANGELOG.md)
3. Visit the [API docs](http://localhost:8000/docs)
4. Open an issue on the repository

## 🙏 Credits

- Built with [FastAPI](https://fastapi.tiangolo.com/), [Chart.js](https://www.chartjs.org/), and [APScheduler](https://apscheduler.readthedocs.io/)
- Traffic data from [Statens vegvesen](https://www.vegvesen.no/) (DATEX II)
- Predictions from [Google Maps Directions API](https://developers.google.com/maps/documentation/directions)

---

**Version 2.0.0** - See [CHANGELOG.md](CHANGELOG.md) for release notes
