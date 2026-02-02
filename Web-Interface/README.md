# Loki IDS Web Interface

A lightweight standalone web dashboard and API for managing security alerts and signatures. Optimized for Raspberry Pi 5.

## Features

- 📊 **Real-time Dashboard**: Live monitoring and statistics
- 🚨 **Alert Management**: View, filter, and manage security alerts with lifecycle tracking
- 🔍 **Signature Management**: Add, edit, and manage detection signatures via web UI
- 📈 **Analytics**: Statistics and visualizations of security events
- 🔌 **WebSocket Support**: Real-time alert streaming
- 💾 **Database-Backed**: SQLite database for persistent storage
- 🚀 **Standalone API**: RESTful API that can be integrated with external systems

## Quick Start

### 1. Setup Environment

**For Python 3.13.5 (Raspberry Pi 5):**
```bash
cd /home/zaher/Loki-IDS/Web-Interface

# Create virtual environment with Python 3.13.5
python3.13 -m venv venv

# Install dependencies
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

**For other Python versions:**
```bash
cd /home/zaher/Loki-IDS/Web-Interface

# Create virtual environment
env -i PATH=/usr/bin:/bin /usr/bin/python3 -m venv venv

# Install dependencies
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

**Note:** See [PYTHON313_SETUP.md](PYTHON313_SETUP.md) for complete Python 3.13.5 setup instructions on Raspberry Pi 5.

### 2. Start the Web Interface

```bash
# Start server
venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

Or use the startup script:
```bash
./start_web_server.sh
```

### 3. Access the Dashboard

Open your browser:
- **Dashboard**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## Installation

### Prerequisites

- Python 3.12+ (Python 3.13.5 recommended for Raspberry Pi 5)
- pip (Python package manager)
- Network access

### Step-by-Step Installation

1. **Navigate to Web-Interface directory:**
   ```bash
   cd /home/zaher/Loki-IDS/Web-Interface
   ```

2. **Create virtual environment:**
   ```bash
   python3.13 -m venv venv
   ```

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Verify installation:**
   ```bash
   python3 --version
   pip list
   ```

### Python 3.13.5 Setup (Raspberry Pi 5)

For detailed instructions on installing Python 3.13.5 on Raspberry Pi 5, see [PYTHON313_SETUP.md](PYTHON313_SETUP.md).

## Database Setup

### Automatic Initialization

The database is **automatically created** when you start the web server. The `start_web_server.sh` script will:
1. Create the virtual environment (if needed)
2. Install dependencies
3. Start the FastAPI server
4. Initialize the database on first startup

### Manual Initialization (Optional)

If you want to initialize the database manually (e.g., after pulling code), you can run:

```bash
cd /path/to/Loki-IDS/Web-Interface

# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the initialization script
python3 init_database.py
```

Or using the virtual environment's Python directly:
```bash
venv/bin/python3 init_database.py
```

### Database Location

The SQLite database file is created at:
```
Web-Interface/loki_ids.db
```

### Database Schema

The database contains three main tables:
- **`alerts`**: Stores all IDS alerts and events
- **`signatures`**: Stores detection signature rules
- **`stats_cache`**: Cached statistics for performance

## Architecture

### Database-First Design
- **Signatures**: Stored and managed in database
- **Alerts**: Stored in database (queryable, searchable)

### Components
- **FastAPI Backend**: RESTful API with WebSocket support
- **SQLite Database**: File-based, zero-configuration
- **Frontend Dashboard**: Vanilla JavaScript (lightweight)

### Project Structure
```
Web-Interface/
├── api/                    # FastAPI backend
│   ├── main.py            # Main application
│   ├── models/            # Database models and schemas
│   └── routes/            # API endpoints
├── static/                # Frontend files
│   ├── index.html
│   ├── css/
│   └── js/
├── requirements.txt
├── start_web_server.sh
└── loki_ids.db           # SQLite database (auto-created)
```

## API Documentation

### Base URL
All API endpoints are prefixed with `/api`:
- Base: `http://localhost:8080/api`
- Interactive docs: `http://localhost:8080/docs`

### Alerts

#### List Alerts
```http
GET /api/alerts?page=1&page_size=10&alert_type=signature_match&start_time=2024-01-01T00:00:00
```

**Response:**
```json
{
  "alerts": [...],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

#### Get Alert by ID
```http
GET /api/alerts/{id}
```

#### Add Alert
```http
POST /api/alerts
Content-Type: application/json

{
  "alert_type": "signature_match",
  "src_ip": "192.168.1.100",
  "dst_ip": "192.168.1.1",
  "src_port": 12345,
  "dst_port": 80,
  "message": "Test alert",
  "details": {"signature": "test_pattern"}
}
```

#### Delete Alert
```http
DELETE /api/alerts/{id}
```

### Signatures

#### List Signatures
```http
GET /api/signatures
```

#### Add Signature
```http
POST /api/signatures
Content-Type: application/json

{
  "name": "test_signature",
  "pattern": "test.*pattern",
  "action": "alert",
  "description": "Test signature",
  "enabled": true
}
```

#### Update Signature
```http
PUT /api/signatures/{id}
Content-Type: application/json

{
  "name": "updated_signature",
  "pattern": "updated.*pattern",
  "action": "alert",
  "description": "Updated description",
  "enabled": true
}
```

#### Delete Signature
```http
DELETE /api/signatures/{id}
```

#### Import from YAML
```http
POST /api/signatures/reload
Content-Type: multipart/form-data

file: <yaml_file>
```

### System

#### Get Statistics
```http
GET /api/stats
```

**Response:**
```json
{
  "total_alerts": 1000,
  "alerts_by_type": {...},
  "recent_alerts": [...],
  "signature_count": 50
}
```

#### Get System Status
```http
GET /api/system/status
```

#### Health Check
```http
GET /api/system/health
```

### WebSocket

#### Real-time Alert Stream
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/alerts');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('New alert:', data);
};
```

## Testing

### Quick Test

```bash
# Health check
curl http://localhost:8080/api/system/health

# Get statistics
curl http://localhost:8080/api/stats
```

### Comprehensive Testing

#### 1. Test Alert Management

```bash
# Add an alert
curl -X POST http://localhost:8080/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "signature_match",
    "src_ip": "192.168.1.100",
    "dst_ip": "192.168.1.1",
    "src_port": 12345,
    "dst_port": 80,
    "message": "Test alert from API",
    "details": {"signature": "test_pattern"}
  }'

# List alerts
curl http://localhost:8080/api/alerts?page=1&page_size=10 | python3 -m json.tool
```

#### 2. Test Signature Management

```bash
# Add signature
curl -X POST http://localhost:8080/api/signatures \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_signature",
    "pattern": "test.*pattern",
    "action": "alert",
    "description": "Test signature",
    "enabled": true
  }'

# List signatures
curl http://localhost:8080/api/signatures | python3 -m json.tool
```


#### 4. Test WebSocket

```python
import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8080/ws/alerts"
    async with websockets.connect(uri) as websocket:
        await websocket.send("ping")
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

### Test Checklist

- [ ] Web interface starts without errors
- [ ] Health check returns healthy status
- [ ] Dashboard loads in browser
- [ ] Can add signature via API
- [ ] Can add signature via dashboard
- [ ] Can add alert via API
- [ ] Can view alerts in dashboard
- [ ] Statistics endpoint returns data
- [ ] WebSocket connection works

## Deployment

### Systemd Service Setup

Create `/etc/systemd/system/loki-web.service`:

```ini
[Unit]
Description=Loki IDS Web Interface
After=network.target

[Service]
Type=simple
User=zaher
WorkingDirectory=/home/zaher/Loki-IDS/Web-Interface
Environment="PATH=/home/zaher/Loki-IDS/Web-Interface/venv/bin"
ExecStart=/home/zaher/Loki-IDS/Web-Interface/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable loki-web
sudo systemctl start loki-web
sudo systemctl status loki-web
```

**View logs:**
```bash
sudo journalctl -u loki-web -f
```

### Production Deployment with Nginx

Install nginx:
```bash
sudo apt-get install nginx
```

Create `/etc/nginx/sites-available/loki-web`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/loki-web /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Database

### SQLite Database

**Location**: `Web-Interface/loki_ids.db`

**Features:**
- Auto-created on first startup
- No configuration required
- No separate server needed
- File-based (easy backup)

### Backup and Restore

**Backup:**
```bash
# Simple copy
cp /home/zaher/Loki-IDS/Web-Interface/loki_ids.db \
   /home/zaher/Loki-IDS/Web-Interface/loki_ids.db.backup.$(date +%Y%m%d_%H%M%S)

# SQLite backup command
sqlite3 /home/zaher/Loki-IDS/Web-Interface/loki_ids.db \
  ".backup /home/zaher/Loki-IDS/Web-Interface/loki_ids.db.backup"
```

**Restore:**
```bash
# Stop service
sudo systemctl stop loki-web

# Restore from backup
cp /home/zaher/Loki-IDS/Web-Interface/loki_ids.db.backup \
   /home/zaher/Loki-IDS/Web-Interface/loki_ids.db

# Start service
sudo systemctl start loki-web
```

## Implementation Details

### Backend API (FastAPI)

**Database Layer:**
- SQLite database with automatic schema creation
- Models: Alerts, Signatures, StatsCache
- Async database operations (SQLAlchemy + aiosqlite)
- CRUD operations for all entities

**API Endpoints:**
- **Alerts**: List, view, delete (with pagination and filtering)
- **Signatures**: Full CRUD operations, import from YAML
- **Statistics**: Alert statistics and analytics
- **System**: Status, health check
- **WebSocket**: Real-time alert streaming

**Features:**
- RESTful API design
- Automatic API documentation (Swagger UI)
- Input validation (Pydantic schemas)
- Error handling
- CORS support

### Frontend Dashboard

**UI Components:**
- Real-time dashboard with statistics
- Alert management interface
- Signature management interface
- Responsive design (mobile-friendly)
- Dark theme

**Features:**
- Interactive charts (Chart.js)
- Real-time updates via WebSocket
- Filtering and search
- Pagination
- Modal dialogs for forms

**JavaScript:**
- Vanilla JavaScript (no framework dependencies)
- WebSocket client for real-time updates
- API client for all endpoints
- Chart rendering

### Database Schema

**Tables:**
- `alerts` - Security alerts/events
- `signatures` - Detection signatures
- `stats_cache` - Cached statistics (for performance)

**Features:**
- Automatic schema creation
- Indexes for performance
- Foreign key relationships
- Timestamps and metadata

### Performance

**Resource Usage (Raspberry Pi 5):**
- API Server: ~50-80MB RAM
- Database: ~10-20MB (for 10K alerts)
- Frontend: ~500KB (static files)
- **Total**: ~100-150MB RAM

**Optimizations:**
- In-memory signature cache
- Database indexes
- Async operations
- Static file serving
- Connection pooling

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8080
sudo lsof -i :8080

# Use different port
venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8081
```

### Import Errors
```bash
# Reinstall dependencies
venv/bin/pip install -r requirements.txt --force-reinstall
```

### Database Errors
```bash
# Check database file
ls -la Web-Interface/loki_ids.db

# Verify database integrity
sqlite3 Web-Interface/loki_ids.db "PRAGMA integrity_check;"

# Recreate database (will lose data)
rm Web-Interface/loki_ids.db
# Restart server (will auto-create)
```

### Service Won't Start

1. Check logs:
   ```bash
   sudo journalctl -u loki-web -n 50
   ```

2. Verify Python and dependencies:
   ```bash
   cd /home/zaher/Loki-IDS/Web-Interface
   venv/bin/python3 --version
   venv/bin/pip list
   ```

3. Test manually:
   ```bash
   cd /home/zaher/Loki-IDS/Web-Interface
   venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080
   ```

### API Not Responding
```bash
# Check server logs
# Look for errors in terminal where uvicorn is running

# Test basic connectivity
curl -v http://localhost:8080/api/system/health
```

## Security Considerations

1. **Firewall**: Only expose port 8080 to trusted networks
2. **Authentication**: Consider adding authentication for production use
3. **HTTPS**: Use a reverse proxy (nginx) with SSL for production
4. **Database**: Ensure database file has proper permissions (600 recommended)

## Standalone API

This is a standalone web interface and API. It does not require or integrate with the core IDS system.

**To use with external systems:**
- Add alerts via `POST /api/alerts`
- Manage signatures via CRUD endpoints
- Stream alerts via WebSocket at `WS /ws/alerts`

## License

See main project LICENSE file.
