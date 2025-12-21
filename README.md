# Oslo Commute Time Optimizer

A personal web application to find the best and worst times to drive to work in Oslo, Norway. Analyze your commute using either Google Maps predictions or self-collected data from Norway's free DATEX traffic system.

## Features

- **Two Data Sources:**
  - **Google Maps Mode:** Instant results using Google Maps Directions API with traffic predictions
  - **DATEX Mode:** Free, self-collected data from Statens vegvesen (Norwegian Public Roads Administration)

- **Visual Analysis:** Beautiful charts showing travel times throughout the morning (06:00-10:00)
- **Best/Worst Times:** Clear identification of optimal and worst departure times
- **Background Collection:** Automated DATEX data polling every 5 minutes
- **Data Quality Tracking:** Monitor collection status and data reliability

## Screenshots

The app provides:
- Simple input form for home/work addresses and day selection
- Summary cards showing best time, worst time, and potential time savings
- Interactive line chart visualizing travel times throughout the morning
- Settings interface for DATEX segment selection and collection management

## Prerequisites

- Python 3.8 or higher
- (Optional) Google Maps API key for instant predictions
- (Optional) DATEX credentials for free data collection

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd commute-optimizer
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys (see Configuration section below).

4. **Initialize the database:**
   The database will be automatically created when you first run the application.

## Configuration

### Google Maps API (Optional - for instant results)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Directions API**
4. Create an API key
5. Add the key to `.env`:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

**Note:** Google Maps requires a credit card on file but provides $200/month free credit (approximately 40,000 Directions API calls).

### DATEX API (Optional - for free data collection)

1. Register at [Statens vegvesen DATEX](https://www.vegvesen.no/trafikkdata/datex/)
2. Wait 1-2 business days to receive credentials via email
3. Add credentials to `.env`:
   ```
   DATEX_USERNAME=your_username_here
   DATEX_PASSWORD=your_password_here
   ```

**Note:** DATEX is completely free but requires 2-3 weeks of data collection for reliable results.

## Running the Application

1. **Start the backend server:**
   ```bash
   cd backend
   python main.py
   ```

   The server will start on `http://localhost:8000`

2. **Open your browser:**
   Navigate to `http://localhost:8000`

3. **You're ready to go!**

## Usage Guide

### Quick Start with Google Maps

1. Go to the "Analyze Commute" tab
2. Enter your home address (e.g., "Grønland, Oslo")
3. Enter your work address (e.g., "Aker Brygge, Oslo")
4. Select a day of the week
5. Choose "Google Maps" as the data source
6. Click "Analyze Commute"
7. Results appear instantly!

### Setting Up DATEX Collection

DATEX mode requires initial setup and 2-3 weeks of data collection:

1. **Initialize Segments:**
   - Go to "DATEX Settings" tab
   - Click "Initialize Segments" to fetch available road segments
   - This only needs to be done once

2. **Select Your Route Segments:**
   - Browse the list of Oslo-area road segments
   - Select segments that approximate your commute route
   - Click "Save Selection"

3. **Start Data Collection:**
   - Click "Start Collection" to begin background polling
   - Data is collected every 5 minutes automatically
   - Leave the application running or set up as a service

4. **Wait for Data:**
   - After 2-3 weeks, you'll have reliable patterns
   - Check "Data Quality" to see collection progress

5. **Analyze with Collected Data:**
   - Go to "Analyze Commute" tab
   - Select "DATEX Collected Data" as the data source
   - No need to enter addresses (uses your selected segments)
   - Click "Analyze Commute"

## File Structure

```
commute-optimizer/
├── backend/
│   ├── main.py              # FastAPI application and endpoints
│   ├── google_maps.py       # Google Maps API integration
│   ├── datex_client.py      # DATEX API client
│   ├── datex_collector.py   # Background data collection
│   ├── datex_analyzer.py    # Data aggregation and analysis
│   └── database.py          # SQLite database operations
├── frontend/
│   ├── index.html           # Main HTML interface
│   ├── app.js               # JavaScript functionality
│   └── style.css            # Styling
├── data/
│   └── commute.db           # SQLite database (auto-created)
├── .env                     # Your environment variables (create from .env.example)
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

The backend provides the following REST API endpoints:

### Analysis
- `POST /api/analyze` - Analyze commute times
  - Body: `{ home, work, day, mode }`
  - Returns: Best/worst times and full timeline

### DATEX Management
- `GET /api/datex/status` - Get collection status
- `POST /api/datex/collection` - Start/stop collection
  - Body: `{ action: "start" | "stop" }`
- `GET /api/datex/segments/available` - Get available segments
- `POST /api/datex/segments` - Set selected segments
  - Body: `{ segment_ids: ["id1", "id2", ...] }`
- `POST /api/datex/initialize-segments` - Fetch segments from API
- `GET /api/datex/quality` - Get data quality statistics

### Health
- `GET /api/health` - Health check and configuration status

## Running as a Background Service

To keep DATEX collection running continuously, you can set up the application as a systemd service (Linux) or use a process manager like PM2.

### Using systemd (Linux)

Create a service file at `/etc/systemd/system/commute-optimizer.service`:

```ini
[Unit]
Description=Oslo Commute Time Optimizer
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/commute-optimizer/backend
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/path/to/your/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable commute-optimizer
sudo systemctl start commute-optimizer
```

## Troubleshooting

### Google Maps API Issues

**"GOOGLE_MAPS_API_KEY environment variable not set"**
- Make sure you created `.env` file from `.env.example`
- Verify the API key is correctly set in `.env`
- Restart the backend server after changing `.env`

**"API key not configured or invalid"**
- Check that the Directions API is enabled in Google Cloud Console
- Verify the API key has no restrictions that block localhost
- Check your Google Cloud billing is set up

### DATEX Issues

**"DATEX credentials not configured or invalid"**
- Verify `DATEX_USERNAME` and `DATEX_PASSWORD` in `.env`
- Registration can take 1-2 business days
- Test credentials by clicking "Initialize Segments"

**"Insufficient data for analysis"**
- DATEX mode requires 2-3 weeks of continuous data collection
- Check that collection is running in DATEX Settings
- Verify selected segments are receiving data in Data Quality section

**"No segments available"**
- Click "Initialize Segments" in DATEX Settings
- Requires valid DATEX credentials
- Only Oslo-area segments are shown by default

## Data Storage

- All data is stored locally in `data/commute.db` (SQLite database)
- DATEX travel times are stored with timestamp, segment ID, and travel time
- No personal data or addresses are stored
- Database can be deleted at any time to reset

## Performance Notes

- **Google Maps:** Each analysis makes 17 API calls (one per 15-minute interval)
- **DATEX:** Polls every 5 minutes, storing ~100-200 measurements per hour
- **Database Size:** Expect ~1MB per week of DATEX collection
- **Background Impact:** Minimal CPU/memory usage during collection

## Oslo-Specific Notes

- DATEX covers major routes: E18, E6, Ring 3, and main arteries
- Most commuter routes in the Oslo area have coverage
- Segments include areas like Lysaker, Sandvika, Asker, Drammen, Lørenskog
- For best results, select 2-3 segments that closely match your route

## Future Enhancements

Potential features to add:

- Reverse commute analysis (work → home, afternoon times)
- Push notifications: "Leave now for optimal commute"
- Weather correlation analysis
- Historical prediction accuracy tracking
- Multi-route comparison
- Weekly/monthly trend reports

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Credits

- Built with FastAPI, SQLite, and Chart.js
- Traffic data provided by Statens vegvesen (DATEX II)
- Predictions powered by Google Maps Directions API
