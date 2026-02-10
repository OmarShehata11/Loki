# Loki IDS - New Architecture Guide

## ✅ Architecture Restructure Complete!

The Loki IDS has been successfully restructured where **IDS Core now owns the database and exposes APIs**, while the Web Interface is a pure static client.

## New Architecture

```
┌──────────────────────────────────────┐
│         IDS Core (Backend)           │
│                                      │
│  ┌────────────┐   ┌──────────────┐  │
│  │  FastAPI   │   │   nfqueue    │  │
│  │   Server   │   │ Packet       │  │
│  │ (port 8080)│   │ Processing   │  │
│  └─────┬──────┘   └──────┬───────┘  │
│        │                 │          │
│        └────────┬────────┘          │
│                 │                   │
│         ┌───────▼────────┐          │
│         │    Database    │          │
│         │  (loki_ids.db) │          │
│         └────────────────┘          │
└──────────────────────────────────────┘
                 ▲
                 │ HTTP API
                 │
      ┌──────────┴──────────┐
      │   Web Interface     │
      │  (Static HTML/CSS/JS)│
      └─────────────────────┘
```

## Directory Structure

```
Core/loki/
├── api/                          # NEW - Backend API
│   ├── main.py                   # FastAPI application
│   ├── models/
│   │   ├── database.py           # Database models
│   │   ├── schemas.py            # API schemas
│   │   └── crud.py               # Database operations
│   ├── routes/
│   │   ├── alerts.py             # Alert endpoints
│   │   ├── signatures.py         # Signature endpoints
│   │   ├── stats.py              # Statistics endpoints
│   │   ├── system.py             # System endpoints
│   │   ├── iot.py                # IoT control endpoints
│   │   └── websocket.py          # WebSocket for real-time updates
│   └── iot/
│       └── mqtt_client.py        # MQTT client for IoT devices
├── database/
│   └── loki_ids.db               # SQLite database (MOVED from Web-Interface)
├── api_server.py                 # FastAPI startup script (NEW)
├── start_api.sh                  # API server launcher (NEW)
├── nfqueue_app.py                # Packet processing
├── logger.py                     # Alert logging
├── db_integration.py             # HTTP client to own API
├── signature_engine.py           # Signature detection
├── detectore_engine.py           # Behavior detection
└── packet_parser.py              # Packet parsing

Web-Interface/
└── static/                       # Pure static files (NO Python code)
    ├── index.html                # Dashboard UI
    ├── css/                      # Styles
    └── js/                       # Client-side JavaScript
```

## How to Use

### Option 1: Automated Startup (Recommended)

Start everything with one command:

```bash
cd /home/zaher/Loki-IDS
sudo bash start_loki_system.sh
```

This will:
1. Start the Core API Server (port 8080)
2. Start the IDS packet processing
3. Handle graceful shutdown on Ctrl+C

### Option 2: Manual Startup (Two Terminals)

**Terminal 1: Start API Server**
```bash
cd /home/zaher/Loki-IDS/Core/loki
bash start_api.sh
```

Wait for:
```
[*] Starting API Server on http://localhost:8080
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Terminal 2: Start IDS Core**
```bash
cd /home/zaher/Loki-IDS
sudo bash run_loki.sh
```

You should see:
```
[*] API integration enabled - alerts will be sent to Web Interface
```

## Access Points

- **Dashboard**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **API Base URL**: http://localhost:8080/api
- **WebSocket**: ws://localhost:8080/ws/alerts

## What Changed

### Before
- Web-Interface owned database and ran FastAPI server
- IDS Core sent HTTP requests TO Web-Interface
- Had to start Web-Interface before IDS

### After
- IDS Core owns database and runs FastAPI server
- Web-Interface is pure static HTML/CSS/JS client
- Start Core API server, then IDS packet processing

## Benefits

1. **Proper Ownership**: Core generates data, so it owns it
2. **Better Architecture**: Clean separation (backend owns data, frontend is client)
3. **No Database Locking**: Only Core accesses database directly
4. **Better Performance**: API and packet processing in separate processes
5. **Scalability**: Can deploy static files to CDN, add multiple frontends
6. **Maintainability**: Clear boundaries, easier to debug

## Testing the New Setup

### 1. Test API Server Alone
```bash
cd Core/loki
bash start_api.sh

# In another terminal:
curl http://localhost:8080/api/system/health
# Should return: {"status":"healthy","database":"healthy","timestamp":"..."}

curl http://localhost:8080/api/alerts?page=1&page_size=5
# Should return JSON with alerts
```

### 2. Test Dashboard
Open browser to http://localhost:8080
- Should see the Loki IDS Dashboard
- All tabs should work (Dashboard, Alerts, Signatures, IoT)

### 3. Test With IDS Running
```bash
# Terminal 1: API Server
cd Core/loki && bash start_api.sh

# Terminal 2: IDS Core
sudo bash run_loki.sh
```

Generate test traffic and verify alerts appear in real-time on the dashboard.

## Troubleshooting

### "Virtual environment not found"
```bash
cd /home/zaher/Loki-IDS
bash setup_venv.sh
```

### "API integration failed"
Make sure API server is running first:
```bash
cd Core/loki && bash start_api.sh
```

### "Database not found"
Check that database exists:
```bash
ls -lh Core/loki/database/loki_ids.db
```

If missing, reinitialize:
```bash
cd Core/loki
../../loki_env/bin/python3 ../../Web-Interface/init_database.py
mv ../../Web-Interface/loki_ids.db database/
```

### Dashboard not loading
1. Check API server logs for errors
2. Try hard refresh in browser (Ctrl+Shift+R)
3. Check browser console for JavaScript errors (F12)

### Alerts not appearing
1. Check IDS logs: `sudo bash run_loki.sh` output
2. Check API server logs in Terminal 1
3. Verify API health: `curl http://localhost:8080/api/system/health`

## Stopping the System

### If using automated start:
Press `Ctrl+C` in the terminal running `start_loki_system.sh`

### If using manual start:
```bash
# Stop IDS
sudo pkill -f nfqueue_app

# Stop API Server
pkill -f "uvicorn.*api.main"

# Clean up iptables
cd Scripts && sudo bash iptables_down.sh
```

## Key Files Modified

- `Core/loki/api/models/database.py` - Database path updated to Core
- `Core/loki/api/main.py` - Static files path updated
- `Core/loki/api_server.py` - NEW FastAPI launcher
- `Core/loki/start_api.sh` - NEW startup script
- `start_loki_system.sh` - Updated to start Core API

## Database Location

**Old**: `/home/zaher/Loki-IDS/Web-Interface/loki_ids.db`
**New**: `/home/zaher/Loki-IDS/Core/loki/database/loki_ids.db`

## API Endpoints

All API endpoints remain the same:
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert (used by IDS)
- `GET /api/signatures` - List signatures
- `POST /api/signatures` - Create signature
- `GET /api/stats` - Get statistics
- `GET /api/system/health` - Health check
- `GET /api/iot/devices` - List IoT devices
- `WS /ws/alerts` - Real-time alert stream

## Next Steps

1. **Test on Raspberry Pi**: Deploy and test the new architecture
2. **Clean up Web-Interface**: Remove old Python files once everything works
3. **Update documentation**: Update any references to old architecture
4. **Monitor performance**: Verify no database locking issues

## Cleanup Old Files (After Testing)

Once everything is confirmed working, you can remove old Web-Interface Python code:

```bash
cd Web-Interface
rm -rf api/ venv/ *.py
# Keep only static/ directory
```

**⚠️ Only do this after thoroughly testing the new setup!**

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs in `/tmp/loki_api.log`
3. Test each component independently
4. Verify all prerequisites are met (venv, database, etc.)

---

**The new architecture is ready to use!** Start with the automated startup script and verify everything works before cleaning up old files.
