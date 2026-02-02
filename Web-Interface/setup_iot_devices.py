#!/usr/bin/env python3
"""
Setup script to register default IoT devices in the database.
Run this after initializing the database to register ESP32 devices.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.models.database import AsyncSessionLocal, IoTDevice


async def setup_default_devices():
    """Register default ESP32 devices."""
    print("=" * 60)
    print("    Setting up IoT Devices")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # ESP32-1: Motion Detection Hub
        device1 = IoTDevice(
            device_id="esp32-1",
            device_type="motion_sensor",
            name="ESP32 Motion Sensor & Buzzer",
            description="Motion detection hub with PIR sensor, buzzer control, and LED indicator",
            mqtt_topic="esp32/sensor1",
            enabled=1,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # ESP32-2: RGB Controller
        device2 = IoTDevice(
            device_id="esp32-2",
            device_type="rgb_controller",
            name="ESP32 RGB Controller",
            description="RGB LED strip controller with NeoPixel support",
            mqtt_topic="rpi/broadcast",
            enabled=1,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Check if devices already exist
        from sqlalchemy import select
        result1 = await session.execute(select(IoTDevice).where(IoTDevice.device_id == "esp32-1"))
        existing1 = result1.scalar_one_or_none()
        
        result2 = await session.execute(select(IoTDevice).where(IoTDevice.device_id == "esp32-2"))
        existing2 = result2.scalar_one_or_none()
        
        if existing1:
            print("[!] ESP32-1 already registered. Skipping...")
        else:
            session.add(device1)
            print("[✓] Registered ESP32-1 (Motion Sensor)")
        
        if existing2:
            print("[!] ESP32-2 already registered. Skipping...")
        else:
            session.add(device2)
            print("[✓] Registered ESP32-2 (RGB Controller)")
        
        await session.commit()
        print("[✓] IoT devices setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_default_devices())
