# Setup Instructions

## Quick Start

After pulling the code, follow these steps:

### 1. Navigate to Web-Interface directory
```bash
cd /path/to/Loki-IDS/Web-Interface
```

### 2. Initialize the Database
**IMPORTANT:** Always use `venv/bin/python3` (not system `python3`)

```bash
venv/bin/python3 init_database.py
```

This creates the database file `loki_ids.db` with all required tables.

### 3. Register IoT Devices (Optional - only if using IoT features)
```bash
venv/bin/python3 setup_iot_devices.py
```

This registers ESP32-1 and ESP32-2 devices in the database.

### 4. Start the Web Server
```bash
./start_web_server.sh
```

Or manually:
```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Available Scripts

All scripts must be run with `venv/bin/python3`:

- **`init_database.py`** - Creates/initializes the database
- **`setup_iot_devices.py`** - Registers IoT devices
- **`check_devices.py`** - Lists registered IoT devices
- **`create_test_alerts.py`** - Creates test alerts for dashboard testing

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'aiosqlite'`

**Solution:** You're using system Python instead of venv Python.

**Fix:** Always use `venv/bin/python3`:
```bash
venv/bin/python3 init_database.py
```

### Alternative: Activate venv first
```bash
source venv/bin/activate
python3 init_database.py
```

## Notes

- The database file `loki_ids.db` is created in the `Web-Interface/` directory
- If the database already exists, `init_database.py` will update the schema if needed
- IoT device registration is idempotent (safe to run multiple times)
