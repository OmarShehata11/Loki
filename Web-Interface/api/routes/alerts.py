"""
Alert management endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import json

from ..models.database import get_db
from ..models.schemas import AlertResponse, AlertListResponse, AlertType, AlertSubtype, AlertStatus
from ..models import crud

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (SIGNATURE, BEHAVIOR, SYSTEM)"),
    subtype: Optional[str] = Query(None, description="Filter by subtype (PORT_SCAN, TCP_FLOOD, UDP_FLOOD, ICMP_FLOOD)"),
    pattern: Optional[str] = Query(None, description="Filter by pattern (for SIGNATURE alerts, case-insensitive search)"),
    status: Optional[str] = Query(None, description="Filter by status (STARTED, ONGOING, ENDED)"),
    src_ip: Optional[str] = Query(None, description="Filter by source IP address"),
    dst_ip: Optional[str] = Query(None, description="Filter by destination IP address"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get alerts with filtering and pagination."""
    # Validate enum values
    if alert_type and alert_type not in [e.value for e in AlertType]:
        raise HTTPException(status_code=400, detail=f"Invalid alert_type. Must be one of: {[e.value for e in AlertType]}")
    if subtype and subtype not in [e.value for e in AlertSubtype]:
        raise HTTPException(status_code=400, detail=f"Invalid subtype. Must be one of: {[e.value for e in AlertSubtype]}")
    if status and status not in [e.value for e in AlertStatus]:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {[e.value for e in AlertStatus]}")
    
    skip = (page - 1) * page_size
    alerts, total = await crud.get_alerts(
        db=db,
        skip=skip,
        limit=page_size,
        alert_type=alert_type,
        subtype=subtype,
        pattern=pattern,
        status=status,
        src_ip=src_ip,
        dst_ip=dst_ip,
        start_time=start_time,
        end_time=end_time
    )
    
    # Parse details JSON strings and include new fields
    alert_list = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "timestamp": alert.timestamp,
            "status": AlertStatus(alert.status).value if alert.status and alert.status in [e.value for e in AlertStatus] else alert.status,
            "type": AlertType(alert.type).value if alert.type in [e.value for e in AlertType] else alert.type,
            "subtype": AlertSubtype(alert.subtype).value if alert.subtype and alert.subtype in [e.value for e in AlertSubtype] else alert.subtype,
            "pattern": alert.pattern,
            "src_ip": alert.src_ip,
            "dst_ip": alert.dst_ip,
            "src_port": alert.src_port,
            "dst_port": alert.dst_port,
            "message": alert.message,
            "details": json.loads(alert.details) if alert.details else {},
            "severity": alert.severity,
            # New lifecycle fields
            "duration_seconds": float(alert.duration_seconds) if alert.duration_seconds and alert.duration_seconds != "" else None,
            "packet_count": alert.packet_count,
            "attack_rate_pps": float(alert.attack_rate_pps) if alert.attack_rate_pps and alert.attack_rate_pps != "" else None,
            "total_duration_seconds": float(alert.total_duration_seconds) if alert.total_duration_seconds and alert.total_duration_seconds != "" else None,
            "total_packets": alert.total_packets,
            "average_rate_pps": float(alert.average_rate_pps) if alert.average_rate_pps and alert.average_rate_pps != "" else None,
            "first_seen": alert.first_seen,
            "last_seen": alert.last_seen
        }
        alert_list.append(alert_dict)
    
    return AlertListResponse(
        alerts=alert_list,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single alert by ID."""
    alert = await crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse(
        id=alert.id,
        timestamp=alert.timestamp,
        status=AlertStatus(alert.status).value if alert.status and alert.status in [e.value for e in AlertStatus] else alert.status,
        type=AlertType(alert.type).value if alert.type in [e.value for e in AlertType] else alert.type,
        subtype=AlertSubtype(alert.subtype).value if alert.subtype and alert.subtype in [e.value for e in AlertSubtype] else alert.subtype,
        pattern=alert.pattern,
        src_ip=alert.src_ip,
        dst_ip=alert.dst_ip,
        src_port=alert.src_port,
        dst_port=alert.dst_port,
        message=alert.message,
        details=json.loads(alert.details) if alert.details else {},
        severity=alert.severity,
        # New lifecycle fields
        duration_seconds=float(alert.duration_seconds) if alert.duration_seconds and alert.duration_seconds != "" else None,
        packet_count=alert.packet_count,
        attack_rate_pps=float(alert.attack_rate_pps) if alert.attack_rate_pps and alert.attack_rate_pps != "" else None,
        total_duration_seconds=float(alert.total_duration_seconds) if alert.total_duration_seconds and alert.total_duration_seconds != "" else None,
        total_packets=alert.total_packets,
        average_rate_pps=float(alert.average_rate_pps) if alert.average_rate_pps and alert.average_rate_pps != "" else None,
        first_seen=alert.first_seen,
        last_seen=alert.last_seen
    )


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert."""
    success = await crud.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}


