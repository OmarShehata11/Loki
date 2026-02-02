"""
System status and control endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..models.database import get_db
from ..models.schemas import SystemStatus, HealthResponse
from ..models import crud

router = APIRouter(prefix="/system", tags=["system"])


def check_ids_running() -> bool:
    """
    Check if the IDS process is running.
    Uses two reliable methods that work even for root/sudo processes:
    1. systemctl service check (most reliable)
    2. pgrep process check (works for all processes including root)
    """
    import subprocess
    
    # Method 1: Check systemd service status (most reliable, works for root processes)
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', '--quiet', 'loki'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Method 2: Use pgrep to find processes (works even for root processes)
    # pgrep can see all processes regardless of user
    try:
        # Check for nfqueue_app.py process
        result = subprocess.run(
            ['pgrep', '-f', 'nfqueue_app.py'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
        
        # Also check for 'nfqueue_app' without .py extension
        result = subprocess.run(
            ['pgrep', '-f', 'nfqueue_app'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    return False


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """Get system status."""
    # Get alerts count for last 24h
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    alerts, _ = await crud.get_alerts(db, skip=0, limit=1, start_time=yesterday)
    alerts_count_24h = len(alerts) if alerts else 0
    
    # Check if IDS is actually running
    ids_running = check_ids_running()
    
    return SystemStatus(
        ids_running=ids_running,
        alerts_count_24h=alerts_count_24h
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db)
):
    """Health check endpoint."""
    try:
        # Test database connection
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/reload-signatures")
async def reload_signatures():
    """
    Reload signatures from database.
    This endpoint is kept for API compatibility but does not interact with IDS.
    """
    raise HTTPException(
        status_code=501,
        detail="Signature reloading is not available. This is a standalone API without IDS integration."
    )
