# Web-Interface Directory (Deprecated)

## ⚠️ This directory is no longer used

**The static frontend has been moved to:** `Core/loki/api/static/`

## New Architecture (Simplified)

```
Core/loki/
├── api/
│   ├── main.py           # FastAPI server
│   ├── static/           # ← Frontend is now here
│   │   ├── index.html
│   │   ├── css/
│   │   └── js/
│   ├── models/           # Database models
│   └── routes/           # API endpoints
├── database/
│   └── loki_ids.db       # SQLite database
└── ...
```

## Why the change?

Moving static files next to the API code:
- ✅ **Eliminates path calculation complexity**
- ✅ **Simpler deployment** - everything in one place
- ✅ **No more path resolution errors**
- ✅ **Easier to understand** - API and frontend together

## Accessing the Dashboard

Start the system normally:
```bash
cd /home/zaher/Loki-IDS
sudo bash start_loki_system.sh
```

Then open: **http://localhost:8080**

## This Directory

This directory now contains only:
- Old documentation
- Cleanup scripts
- Can be safely removed after verifying the new setup works

## Documentation

See the updated guides:
- **Architecture**: `/home/zaher/Loki-IDS/NEW_ARCHITECTURE_GUIDE.md`
- **IoT Setup**: `/home/zaher/Loki-IDS/IOT_INTEGRATION_GUIDE.md`
