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


@app.get("/")
async def root():
    """Serve the dashboard frontend."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Loki IDS API", "docs": "/docs"}


# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

