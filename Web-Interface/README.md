# Loki IDS - Web Interface (Static Frontend)

## Overview

This directory contains the **static frontend** for the Loki IDS Web Dashboard. It's a pure HTML/CSS/JavaScript client that communicates with the IDS Core API.

## Architecture

```
┌──────────────────────────────────────┐
│      IDS Core (Backend)              │
│   ┌─────────────────────────┐        │
│   │  FastAPI Server         │        │
│   │  (port 8080)            │        │
│   │  - Owns Database        │        │
│   │  - Exposes REST API     │        │
│   │  - Serves Static Files  │        │
│   │  - WebSocket Updates    │        │
│   └────────▲────────────────┘        │
└────────────┼────────────────────────────┘
             │
             │ HTTP API
             │
   ┌─────────▼───────────┐
   │  Web Interface      │
   │  (Static Frontend)  │
   │  - HTML/CSS/JS      │
   │  - Dashboard UI     │
   │  - IoT Controls     │
   └─────────────────────┘
```

## Contents

- **static/** - All static web assets
  - `index.html` - Main dashboard page
  - `css/` - Stylesheets
  - `js/` - Client-side JavaScript

## How It Works

1. **IDS Core** runs the FastAPI server and serves these static files
2. The **frontend** (this directory) makes API calls to the backend
3. All data operations go through the API (no direct database access)
4. Real-time updates via WebSocket connection

## Access

Once the system is running, access the dashboard at:

**http://localhost:8080** (or your Raspberry Pi IP)

## Starting the System

This frontend is automatically served by the IDS Core. You don't need to start it separately.

```bash
# Start the complete system
cd /home/zaher/Loki-IDS
sudo bash start_loki_system.sh
```

This will:
1. Start the Core API Server (which serves these static files)
2. Start the IDS packet processing
3. Make the dashboard available at http://localhost:8080

## Features

- **Dashboard Tab**: Real-time statistics and system status
- **Alerts Tab**: View and manage security alerts
- **Signatures Tab**: Manage detection signatures
- **IoT Control Tab**: Control connected ESP32 devices

## API Endpoints

The frontend communicates with these API endpoints:

- `GET /api/alerts` - Fetch alerts
- `GET /api/stats` - Get statistics
- `GET /api/signatures` - List signatures
- `POST /api/signatures` - Create signature
- `GET /api/iot/devices` - List IoT devices
- `POST /api/iot/devices/{id}/command` - Control IoT devices
- `WS /ws/alerts` - Real-time alert stream

## Development

To modify the frontend:

1. Edit files in `static/` directory
2. Refresh browser to see changes (served by Core API)
3. No build step required (pure HTML/CSS/JS)

## Documentation

- **Architecture Guide**: `/home/zaher/Loki-IDS/NEW_ARCHITECTURE_GUIDE.md`
- **IoT Integration**: `/home/zaher/Loki-IDS/IOT_INTEGRATION_GUIDE.md`
- **API Docs**: http://localhost:8080/docs (when server is running)

## Troubleshooting

### Dashboard not loading

1. Check if API server is running:
   ```bash
   curl http://localhost:8080/api/system/health
   ```

2. Check browser console for errors (F12)

3. Verify static files exist:
   ```bash
   ls -lh static/
   ```

### Can't connect to API

- Ensure IDS Core API server is running
- Check firewall rules
- Verify port 8080 is accessible

## Notes

- This directory contains **ONLY** static frontend files
- All backend code is in `Core/loki/api/`
- Database is owned by Core (`Core/loki/database/loki_ids.db`)
- No Python code should exist in this directory

## Cleanup Script

If you see a root-owned `integration/` directory still present, run:

```bash
sudo bash cleanup_root_files.sh
```

This will remove any remaining root-owned files from the old architecture.
