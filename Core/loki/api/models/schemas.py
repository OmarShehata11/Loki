"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    """High-level alert types."""
    SIGNATURE = "SIGNATURE"
    BEHAVIOR = "BEHAVIOR"
    SYSTEM = "SYSTEM"


class AlertSubtype(str, Enum):
    """Sub-categories for behavior alerts."""
    PORT_SCAN = "PORT_SCAN"
    TCP_FLOOD = "TCP_FLOOD"
    UDP_FLOOD = "UDP_FLOOD"
    ICMP_FLOOD = "ICMP_FLOOD"


class AlertStatus(str, Enum):
    """Alert lifecycle status."""
    STARTED = "STARTED"
    ONGOING = "ONGOING"
    ENDED = "ENDED"


class AlertBase(BaseModel):
    timestamp: str
    status: Optional[AlertStatus] = None
    type: AlertType
    subtype: Optional[AlertSubtype] = None
    pattern: Optional[str] = None  # Pattern for SIGNATURE alerts
    src_ip: str
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    severity: Optional[str] = "MEDIUM"
    
    # New fields for alert lifecycle
    duration_seconds: Optional[float] = None  # For ONGOING alerts
    packet_count: Optional[int] = None  # For ONGOING alerts
    attack_rate_pps: Optional[float] = None  # For ONGOING alerts
    total_duration_seconds: Optional[float] = None  # For ENDED alerts
    total_packets: Optional[int] = None  # For ENDED alerts
    average_rate_pps: Optional[float] = None  # For ENDED alerts
    first_seen: Optional[str] = None  # For ENDED alerts
    last_seen: Optional[str] = None  # For ENDED alerts


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int


class SignatureBase(BaseModel):
    name: str
    pattern: str
    action: str = "alert"  # Only 'alert' now (drop removed)
    description: Optional[str] = None
    enabled: Optional[int] = 1
    
    @validator('action')
    def validate_action(cls, v):
        if v != 'alert':
            raise ValueError('Action must be "alert" (drop action has been removed)')
        return v


class SignatureCreate(SignatureBase):
    pass


class SignatureUpdate(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    action: Optional[str] = "alert"  # Only 'alert' now
    description: Optional[str] = None
    enabled: Optional[int] = None
    
    @validator('action')
    def validate_action(cls, v):
        if v is not None and v != 'alert':
            raise ValueError('Action must be "alert" (drop action has been removed)')
        return v


class SignatureResponse(SignatureBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class SystemStatus(BaseModel):
    ids_running: bool
    uptime: Optional[str] = None
    packets_processed: Optional[int] = None
    alerts_count_24h: Optional[int] = None


class StatsResponse(BaseModel):
    total_alerts: int
    alerts_by_type: Dict[str, int]
    top_attacking_ips: List[Dict[str, Any]]
    alerts_last_24h: int
    alerts_last_hour: int


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str


