## Deployment Guide

This guide covers various deployment options for the Oslo Commute Time Optimizer.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Systemd Service](#systemd-service)
5. [Environment Variables](#environment-variables)
6. [Demo/Testing Mode](#demotesting-mode)

---

## Local Development

### Prerequisites
- Python 3.8+
- pip

### Setup Steps

1. **Clone and navigate:**
   ```bash
   cd commute-optimizer
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application:**
   ```bash
   ./run.sh
   # Or manually:
   cd backend && python main.py
   ```

6. **Access the application:**
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Create .env file:**
   ```bash
   cp .env.example .env
   # Add your API keys
   ```

2. **Start the container:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop the container:**
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the image:**
   ```bash
   docker build -t oslo-commute-optimizer .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name commute-optimizer \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/.env:/app/.env:ro \
     --restart unless-stopped \
     oslo-commute-optimizer
   ```

3. **View logs:**
   ```bash
   docker logs -f commute-optimizer
   ```

### Docker Environment Variables

Pass environment variables directly:

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e GOOGLE_MAPS_API_KEY=your_key \
  -e DATEX_USERNAME=your_username \
  -e DATEX_PASSWORD=your_password \
  -e DATEX_AUTO_START=true \
  --restart unless-stopped \
  oslo-commute-optimizer
```

---

## Production Deployment

### Using Nginx as Reverse Proxy

1. **Install Nginx:**
   ```bash
   sudo apt-get update
   sudo apt-get install nginx
   ```

2. **Create Nginx configuration:**
   ```nginx
   # /etc/nginx/sites-available/commute-optimizer
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable the site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/commute-optimizer /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Add SSL with Let's Encrypt:**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Security Considerations

1. **Firewall configuration:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Environment file permissions:**
   ```bash
   chmod 600 .env
   ```

3. **Update CORS settings:**
   ```bash
   # In .env
   CORS_ORIGINS=https://your-domain.com
   ```

4. **Enable HTTPS only:**
   ```bash
   # In .env
   DEBUG=false
   ```

---

## Systemd Service

Run the application as a system service on Linux.

### Create Service File

```ini
# /etc/systemd/system/commute-optimizer.service
[Unit]
Description=Oslo Commute Time Optimizer
After=network.target

[Service]
Type=simple
User=your-username
Group=your-username
WorkingDirectory=/path/to/commute-optimizer
Environment="PATH=/path/to/commute-optimizer/venv/bin"
EnvironmentFile=/path/to/commute-optimizer/.env
ExecStart=/path/to/commute-optimizer/venv/bin/python backend/main.py
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/commute-optimizer/output.log
StandardError=append:/var/log/commute-optimizer/error.log

[Install]
WantedBy=multi-user.target
```

### Service Management

```bash
# Create log directory
sudo mkdir -p /var/log/commute-optimizer
sudo chown your-username:your-username /var/log/commute-optimizer

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable commute-optimizer
sudo systemctl start commute-optimizer

# Check status
sudo systemctl status commute-optimizer

# View logs
sudo journalctl -u commute-optimizer -f

# Restart service
sudo systemctl restart commute-optimizer

# Stop service
sudo systemctl stop commute-optimizer
```

---

## Environment Variables

### Required Variables

```bash
# At least one of these pairs is required:
GOOGLE_MAPS_API_KEY=your_key          # For Google Maps mode
# OR
DATEX_USERNAME=your_username          # For DATEX mode
DATEX_PASSWORD=your_password
```

### Optional Variables

```bash
# Server Configuration
HOST=0.0.0.0                          # Listen address
PORT=8000                             # Port number
DEBUG=false                           # Debug mode

# Logging
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/path/to/logfile.log        # Optional log file

# Database
DB_PATH=/custom/path/commute.db      # Custom database location

# DATEX Collection
DATEX_POLL_INTERVAL_SECONDS=300      # Poll every 5 minutes
DATEX_TIMEOUT_SECONDS=30             # API timeout
DATEX_AUTO_START=true                # Auto-start collection

# Analysis Configuration
ANALYSIS_START_HOUR=6                # Morning start time
ANALYSIS_END_HOUR=10                 # Morning end time
ANALYSIS_INTERVAL_MINUTES=15         # Query interval
MIN_SAMPLES_FOR_QUALITY=3            # Min samples for quality

# Google Maps
GOOGLE_MAPS_TIMEOUT_SECONDS=10       # API timeout
GOOGLE_MAPS_TRAFFIC_MODEL=best_guess # Traffic model

# CORS (comma-separated)
CORS_ORIGINS=*                       # Allowed origins
```

### Priority Order

1. Environment variables (highest priority)
2. .env file
3. Default values in config.py (lowest priority)

---

## Demo/Testing Mode

Run the application with demo data (no API keys required).

### Seed Demo Data

```bash
# Seed 21 days (3 weeks) of data
python backend/demo_data.py --seed 21

# Seed custom number of days
python backend/demo_data.py --seed 30
```

### Generated Demo Data

- **3 demo segments**: E18 Lysaker-Oslo, E6 Romerike-Oslo, Ring 3 Nord
- **Data points**: Every 5 minutes from 05:00 to 11:00
- **Realistic patterns**: Morning rush hour simulation
- **Total records**: ~7,500 records for 21 days

### Using Demo Mode

1. Seed the data:
   ```bash
   python backend/demo_data.py --seed 21
   ```

2. Start the application:
   ```bash
   ./run.sh
   ```

3. Use DATEX mode (no API keys needed):
   - Go to "Analyze Commute" tab
   - Select "DATEX Collected Data"
   - Choose any day
   - Click "Analyze Commute"

---

## Health Checks

### Manual Health Check

```bash
curl http://localhost:8000/api/health
```

### Expected Response

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

### Monitoring Endpoints

- `/api/health` - Basic health check
- `/api/config` - Configuration summary
- `/api/datex/status` - Collection status
- `/api/datex/quality` - Data quality stats

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=8080 python backend/main.py
```

### Database Locked

```bash
# Stop all instances
pkill -f "python backend/main.py"

# Remove lock file
rm data/commute.db-journal

# Restart
./run.sh
```

### Permission Denied

```bash
# Make scripts executable
chmod +x run.sh test_setup.py

# Fix data directory permissions
chmod 755 data
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Verify installation
python test_setup.py
```

---

## Performance Tuning

### For High Traffic

```bash
# Use multiple workers with uvicorn
uvicorn backend.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### For Low Resources

```bash
# Reduce polling frequency
DATEX_POLL_INTERVAL_SECONDS=600  # 10 minutes instead of 5
```

### Database Optimization

```bash
# Vacuum database periodically
sqlite3 data/commute.db "VACUUM;"

# Analyze for query optimization
sqlite3 data/commute.db "ANALYZE;"
```

---

## Backup and Restore

### Backup Database

```bash
# Simple copy
cp data/commute.db data/commute.db.backup

# Or use sqlite3
sqlite3 data/commute.db ".backup data/commute.db.backup"
```

### Restore Database

```bash
# Simple copy
cp data/commute.db.backup data/commute.db

# Or use sqlite3
sqlite3 data/commute.db ".restore data/commute.db.backup"
```

### Automated Backups

```bash
# Add to crontab (daily backup)
0 2 * * * cp /path/to/data/commute.db /path/to/backups/commute.db.$(date +\%Y\%m\%d)
```

---

## Support

For issues or questions:
- Check the logs: `docker logs commute-optimizer` or `/var/log/commute-optimizer/`
- Review the API docs: http://localhost:8000/docs
- Run health check: `curl http://localhost:8000/api/health`
