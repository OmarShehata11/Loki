"""
Database models and connection for Loki IDS Web Interface.
Uses SQLite for lightweight, file-based storage.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

# Get project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
db_path = os.path.join(project_root, "Web-Interface", "loki_ids.db")

# Create async engine for SQLite
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


class Alert(Base):
    """Alert/Event records from IDS detection."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False, index=True)
    status = Column(String, index=True)  # STARTED, ONGOING, ENDED
    type = Column(String, nullable=False, index=True)  # SIGNATURE, BEHAVIOR, SYSTEM
    subtype = Column(String, index=True)  # PORT_SCAN, TCP_FLOOD, UDP_FLOOD, ICMP_FLOOD, etc.
    pattern = Column(String, index=True)  # Pattern for SIGNATURE alerts (e.g., "UNION SELECT", "<script>")
    src_ip = Column(String, nullable=False, index=True)
    dst_ip = Column(String, index=True)
    src_port = Column(Integer)
    dst_port = Column(Integer)
    message = Column(Text, nullable=False)
    details = Column(Text)  # JSON string
    severity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # New fields for alert lifecycle tracking
    duration_seconds = Column(String)  # For ONGOING alerts
    packet_count = Column(Integer)  # For ONGOING alerts
    attack_rate_pps = Column(String)  # For ONGOING alerts
    total_duration_seconds = Column(String)  # For ENDED alerts
    total_packets = Column(Integer)  # For ENDED alerts
    average_rate_pps = Column(String)  # For ENDED alerts
    first_seen = Column(String)  # For ENDED alerts
    last_seen = Column(String)  # For ENDED alerts
    
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
        Index('idx_src_ip', 'src_ip'),
        Index('idx_type', 'type'),
        Index('idx_status', 'status'),
        Index('idx_subtype', 'subtype'),
        Index('idx_pattern', 'pattern'),
    )


class Signature(Base):
    """Signature rules for detection."""
    __tablename__ = "signatures"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    pattern = Column(Text, nullable=False)
    action = Column(String, nullable=False, default="alert")  # Only 'alert' now
    description = Column(Text)
    enabled = Column(Integer, default=1)  # 1 = enabled, 0 = disabled
    created_at = Column(String)
    updated_at = Column(String)


class StatsCache(Base):
    """Cached statistics for performance."""
    __tablename__ = "stats_cache"
    
    key = Column(String, primary_key=True)
    value = Column(Text)  # JSON string
    updated_at = Column(String)


class IoTDevice(Base):
    """IoT device registration and configuration."""
    __tablename__ = "iot_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, nullable=False, index=True)  # e.g., "esp32-1", "esp32-2"
    device_type = Column(String, nullable=False)  # "motion_sensor", "rgb_controller", etc.
    name = Column(String, nullable=False)
    description = Column(Text)
    mqtt_topic = Column(String)  # MQTT topic for this device
    enabled = Column(Integer, default=1)  # 1 = enabled, 0 = disabled
    last_seen = Column(String)  # Last time device was seen/heard from
    created_at = Column(String)
    updated_at = Column(String)
    
    __table_args__ = (
        Index('idx_device_id', 'device_id'),
        Index('idx_device_type', 'device_type'),
    )


class IoTDeviceState(Base):
    """Current state of IoT devices."""
    __tablename__ = "iot_device_states"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, nullable=False, index=True)
    state_key = Column(String, nullable=False)  # e.g., "motion_detected", "rgb_color", "alarm_enabled"
    state_value = Column(Text)  # JSON string or simple value
    timestamp = Column(String, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_device_id_timestamp', 'device_id', 'timestamp'),
    )


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


