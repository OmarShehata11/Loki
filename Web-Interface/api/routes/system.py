"""
System status and control endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import psutil

from ..models.database import get_db
from ..models.schemas import SystemStatus, HealthResponse
from ..models import crud

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """Get system status."""
    # Get alerts count for last 24h
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    alerts, _ = await crud.get_alerts(db, skip=0, limit=1, start_time=yesterday)
    alerts_count_24h = len(alerts) if alerts else 0
    
    return SystemStatus(
        ids_running=False,  # No longer tracking IDS status
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
