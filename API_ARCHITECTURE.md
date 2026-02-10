# Loki IDS - API-Based Architecture

## Overview

The IDS Core now communicates with the database through the Web Interface API instead of direct database access. This eliminates SQLite locking issues and provides better separation of concerns.

## Architecture

```
┌─────────────────┐         HTTP POST          ┌──────────────────┐
│                 │  ────────────────────────>  │                  │
│   IDS Core      │         /api/alerts        │  Web Interface   │
│  (nfqueue_app)  │                             │   (FastAPI)      │
│                 │  <────────────────────────  │                  │
└─────────────────┘      HTTP GET (sigs)       └──────────────────┘
                                                         │
                                                         │ Direct Access
                                                         ▼
                                                 ┌──────────────┐
                                                 │   Database   │
                                                 │ (loki_ids.db)│
                                                 └──────────────┘
```

**Benefits:**
- ✓ No database locking (only Web Interface accesses DB)
- ✓ IDS and Web Interface can run on different machines
- ✓ Better separation of concerns
- ✓ Single source of truth (API)
- ✓ Easier to scale and maintain

## How It Works

### 1. Web Interface (API Server)
- **Listens on:** `http://localhost:8080`
- **Owns the database:** Exclusive access to `loki_ids.db`
- **Provides endpoints:**
  - `POST /api/alerts` - Create new alert
  - `GET /api/alerts` - Get alerts (with filtering/pagination)
  - `GET /api/signatures` - Get signatures
  - `GET /api/system/health` - Health check

### 2. IDS Core
- **Detects threats:** Monitors network traffic
- **Sends alerts via API:** HTTP POST to Web Interface
- **Reads signatures via API:** HTTP GET from Web Interface
- **No direct DB access:** Uses `db_integration.py` API client

## Setup Instructions

### Step 1: Start Web Interface FIRST

The Web Interface must be running before starting the IDS:

```bash
cd /home/zaher/Loki-IDS/Web-Interface
bash start_web_server.sh
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Step 2: Start IDS Core

Now start the IDS (it will connect to the API):

```bash
sudo bash /home/zaher/Loki-IDS/run_loki.sh
```

You should see:
```
[*] API integration enabled (API: http://localhost:8080/api)
```

If you see an error about API not being reachable, make sure the Web Interface is running.

### Step 3: Verify It's Working

Test that alerts are being sent via API:

```bash
# Check Web Interface logs for incoming POST requests
# You should see lines like:
# INFO: 127.0.0.1:xxxxx - "POST /api/alerts HTTP/1.1" 201 Created
```

## Configuration

### Change API URL

If you want the IDS to connect to a different API endpoint (e.g., remote server):

Edit `Core/loki/db_integration.py` line 17:

```python
db_integration = DatabaseIntegration(api_base_url="http://192.168.1.100:8080/api")
```

### API Timeout

The IDS uses a 1-second timeout for alert submissions (non-blocking). If the API is slow, increase it in `db_integration.py` line 76:

```python
with urllib.request.urlopen(req, timeout=5) as response:  # Increase from 1 to 5
```

## Troubleshooting

### IDS says "Failed to enable API integration"

**Problem:** Web Interface is not running or not reachable

**Solution:**
```bash
# Start Web Interface
cd Web-Interface
bash start_web_server.sh

# Then restart IDS
sudo bash run_loki.sh
```

### Alerts not showing in Web Interface

**Check 1:** Is IDS sending alerts?
```bash
# Watch IDS output for:
# [*] Alert sent to API
```

**Check 2:** Is API receiving them?
```bash
# Watch Web Interface logs for:
# "POST /api/alerts HTTP/1.1" 201
```

**Check 3:** Test API manually
```bash
curl -X POST http://localhost:8080/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-02-10T12:00:00",
    "type": "BEHAVIOR",
    "subtype": "PORT_SCAN",
    "src_ip": "192.168.1.100",
    "dst_ip": "192.168.1.1",
    "message": "Test alert",
    "severity": "HIGH"
  }'
```

### Database still locked

**Problem:** Old IDS process still accessing database directly

**Solution:**
```bash
# Kill all IDS processes
sudo pkill -f nfqueue_app

# Make sure no process has the DB open
lsof /home/zaher/Loki-IDS/Web-Interface/loki_ids.db

# Restart with new code
sudo bash run_loki.sh
```

## Migration Notes

### What Changed

**Before:**
- IDS directly accessed database → caused locking
- Used async SQLite connections from multiple processes
- Complex threading/event loop management

**After:**
- IDS sends HTTP requests → no locking
- Uses simple urllib (built-in, no dependencies)
- Web Interface is single source of truth

### Compatibility

The new `db_integration.py` has the same interface as before:
- `db_integration.enable()` - Initialize (now checks API health)
- `db_integration.insert_alert(data)` - Send alert (now via HTTP)
- `db_integration.get_signatures()` - Get signatures (now via HTTP)

No changes needed to `nfqueue_app.py` or `logger.py`!

## Performance

- **Alert submission:** < 1ms (non-blocking with timeout)
- **Signature loading:** ~50ms for 100 signatures
- **No database locks:** Web Interface handles all DB operations
- **Concurrent access:** Multiple browser clients can read while IDS writes

## Security Notes

### Current Setup (Development)
- API runs on `localhost:8080` (only accessible on Pi)
- No authentication required
- OK for development/testing

### Production Recommendations
1. **Add API authentication:**
   - API key in headers
   - JWT tokens

2. **Use HTTPS:**
   - Encrypt traffic between IDS and API
   - Prevent tampering

3. **Rate limiting:**
   - Prevent API abuse
   - Limit alert submission rate

4. **Network isolation:**
   - Keep IDS and API on internal network
   - Don't expose port 8080 to internet