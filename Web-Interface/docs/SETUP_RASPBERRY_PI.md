# Database Setup Guide for Raspberry Pi

This guide explains how to set up the database after pulling the code on your Raspberry Pi.

## Quick Setup (Recommended)

The database is **automatically created** when you start the web server. Simply run:

```bash
cd /path/to/Loki-IDS/Web-Interface
./start_web_server.sh
```

The script will:
1. Create virtual environment (if needed)
2. Install dependencies
3. Start the server
4. **Automatically initialize the database** on first startup

## Manual Database Initialization

If you want to initialize the database manually (e.g., after pulling fresh code), follow these steps:

### Step 1: Navigate to Web-Interface Directory

```bash
cd /path/to/Loki-IDS/Web-Interface
```

### Step 2: Create Virtual Environment (if not exists)

```bash
# For Python 3.13
python3.13 -m venv venv

# Or for system Python 3
python3 -m venv venv
```

### Step 3: Install Dependencies

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Initialize Database

**Option A: Using the initialization script (Recommended)**
```bash
# Using venv Python
venv/bin/python3 init_database.py

# Or if venv is activated
python3 init_database.py
```

**Option B: Using Python directly**
```bash
# Activate venv first
source venv/bin/activate

# Then run initialization
python3 -c "from api.models.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Step 5: Verify Database Creation

Check if the database file was created:

```bash
ls -lh loki_ids.db
```

You should see the database file in the `Web-Interface` directory.

## Database Location

The SQLite database file is located at:
```
Web-Interface/loki_ids.db
```

## Database Schema

The database contains three main tables:

1. **`alerts`** - Stores all IDS alerts and events
   - Includes: timestamp, type, subtype, pattern, IPs, ports, status, lifecycle data
   
2. **`signatures`** - Stores detection signature rules
   - Includes: name, pattern, action, description, enabled status
   
3. **`stats_cache`** - Cached statistics for performance
   - Includes: cached stats data

## Troubleshooting

### Error: "No module named 'aiosqlite'"

Make sure you're using the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Permission denied"

Make sure you have write permissions in the Web-Interface directory:
```bash
chmod -R u+w /path/to/Loki-IDS/Web-Interface
```

### Database Already Exists

If the database already exists, running the initialization script is safe - it will only create missing tables and won't delete existing data.

## Next Steps

After initializing the database:

1. **Start the web server:**
   ```bash
   ./start_web_server.sh
   ```

2. **Access the dashboard:**
   - Open browser: http://localhost:8080
   - Or from another device: http://<raspberry-pi-ip>:8080

3. **Add signatures:**
   - Use the web interface to add detection signatures
   - Or import from YAML file using the "Import from YAML" button

## Notes

- The database is automatically initialized when the FastAPI server starts (see `api/main.py`)
- The database file is SQLite, so it's a single file that's easy to backup
- To backup the database, simply copy `loki_ids.db` to another location
- The database is created in the same directory as the Web-Interface code
