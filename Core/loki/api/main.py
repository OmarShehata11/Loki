"""
Main FastAPI application for Loki IDS Web Interface.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from .models.database import init_db
from .routes import alerts, signatures, stats, system, websocket, iot

# Create FastAPI app
app = FastAPI(
    title="Loki IDS API",
    description="Web Interface API for Loki Intrusion Detection System",
    version="1.0.0"
)

# CORS middleware (allow local network access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(alerts.router, prefix="/api")
app.include_router(signatures.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(websocket.router)
app.include_router(iot.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize database and IoT services on startup."""
    await init_db()
    print("[*] Database initialized")
    
    # Initialize MQTT client (optional, won't fail if unavailable)
    try:
        from .iot import initialize_mqtt, MQTT_AVAILABLE
        if MQTT_AVAILABLE:
            # Try to connect to MQTT broker (default: 127.0.0.1:1883 since RPi is the AP)
            # Try localhost first, then common AP IPs
            hosts = ["127.0.0.1", "localhost", "10.0.0.1"]
            connected = False
            for host in hosts:
                if initialize_mqtt(broker_host=host):
                    print(f"[*] MQTT client connected to {host}:1883")
                    connected = True
                    break
            if not connected:
                print("[!] MQTT broker not available (will retry on first use)")
        else:
            print("[!] MQTT library not installed (IoT features disabled)")
    except Exception as e:
        print(f"[!] Failed to initialize MQTT: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        from .iot import shutdown_mqtt
        shutdown_mqtt()
        print("[*] MQTT client disconnected")
    except Exception:
        pass


# Calculate static files path - Web-Interface/static
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Core/loki/api
LOKI_DIR = os.path.dirname(CURRENT_DIR)  # Core/loki
CORE_DIR = os.path.dirname(LOKI_DIR)  # Core
PROJECT_ROOT = os.path.dirname(CORE_DIR)  # Project root
STATIC_DIR = os.path.join(PROJECT_ROOT, "Web-Interface", "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")


# Serve index.html at root
@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard page."""
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"error": "Dashboard not found", "path": INDEX_PATH}


# Mount static files (CSS, JS, etc.)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[✓] Static files: {STATIC_DIR}")
else:
    print(f"[!] ERROR: Static directory not found: {STATIC_DIR}")

