# Complete Fix for Dashboard Freezing During Detection

## Problem
Dashboard works fine initially, but freezes/keeps loading once IDS detection starts.

## Root Cause
When detection starts, the IDS sends hundreds of alert requests per second to the API, overwhelming it and blocking the dashboard.

## Solution Applied

### 1. ✅ Static Files Simplified
- Moved from `Web-Interface/static/` to `Core/loki/api/static/`
- No more complex path calculation
- Faster file serving

### 2. ✅ Fast Alert Processing (202 Accepted)
- API now returns `202 Accepted` immediately
- No heavy response building
- Alerts still saved to database

### 3. ✅ Database Optimizations
- WAL mode enabled (concurrent reads/writes)
- Connection pool: 20 + 40 overflow
- 30-second timeout
- 64MB cache

### 4. ✅ Server Capacity Increased
- 1000 concurrent connections
- 2048 connection backlog
- Automatic worker restarts

## Apply the Fix

**1. Enable WAL mode on database:**
```bash
cd /home/zaher/Loki-IDS
bash enable_wal_mode.sh
```

**2. Restart the system:**
```bash
# Stop everything
sudo pkill -f "uvicorn.*api.main"
sudo pkill -f "nfqueue_app"
cd Scripts && sudo bash iptables_down.sh

# Start fresh
cd /home/zaher/Loki-IDS
sudo bash start_loki_system.sh
```

**3. Watch startup - should see:**
```
[✓] Static files: /home/zaher/Loki-IDS/Core/loki/api/static
[*] Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**4. Test dashboard:**
- Open http://localhost:8080
- Should load immediately
- When detection starts, should STAY responsive

## If Still Freezing

Add rate limiting on the IDS side. Edit `Core/loki/logger.py`:

```python
import time

class AlertLogger:
    def __init__(self):
        self.last_api_call = 0
        self.api_call_interval = 0.1  # Max 10 alerts/second to API

    def _should_send_to_api(self):
        """Rate limit API calls."""
        now = time.time()
        if now - self.last_api_call >= self.api_call_interval:
            self.last_api_call = now
            return True
        return False

    def _log_new_alert(self, ...):
        # Always log to file
        self._write_to_file(record)

        # Rate-limited API calls
        if db_integration.enabled and self._should_send_to_api():
            db_integration.insert_alert(record)
```

This limits API calls to 10/second instead of unlimited.

## Verification

Dashboard should:
- ✅ Load instantly
- ✅ Stay responsive during detection
- ✅ Show alerts in real-time
- ✅ No freezing or infinite loading

Log file should show:
- All alerts (not rate-limited)
- Full details for debugging

Database should show:
- Rate-limited alerts (enough for dashboard)
- No locking issues
