#!/usr/bin/env python3
"""Quick script to check if IoT devices are registered."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.models.database import AsyncSessionLocal, IoTDevice
from sqlalchemy import select

async def check_devices():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(IoTDevice))
        devices = result.scalars().all()
        
        print(f"\nFound {len(devices)} device(s) in database:\n")
        
        if len(devices) == 0:
            print("❌ No devices found!")
            print("\nTo register devices, run:")
            print("  python3 setup_iot_devices.py\n")
        else:
            for device in devices:
                status = "✓ Enabled" if device.enabled else "✗ Disabled"
                print(f"  • {device.device_id}: {device.name} ({status})")
            print()

if __name__ == "__main__":
    asyncio.run(check_devices())
