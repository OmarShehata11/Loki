"""
IoT Device Control API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
from typing import List, Optional
import json

from ..models.database import get_db, IoTDevice, IoTDeviceState
from ..iot import get_mqtt_client, MQTT_AVAILABLE
from ..models import crud

router = APIRouter(prefix="/iot", tags=["iot"])


@router.get("/devices")
async def get_devices(db: AsyncSession = Depends(get_db)):
    """Get all registered IoT devices."""
    result = await db.execute(select(IoTDevice))
    devices = result.scalars().all()
    
    device_list = []
    for device in devices:
        # Get latest state for each device
        state_result = await db.execute(
            select(IoTDeviceState)
            .where(IoTDeviceState.device_id == device.device_id)
            .order_by(IoTDeviceState.timestamp.desc())
            .limit(1)
        )
        latest_state = state_result.scalar_one_or_none()
        
        device_dict = {
            "id": device.id,
            "device_id": device.device_id,
            "device_type": device.device_type,
            "name": device.name,
            "description": device.description,
            "mqtt_topic": device.mqtt_topic,
            "enabled": bool(device.enabled),
            "last_seen": device.last_seen,
            "state": {}
        }
        
        # Parse state values
        if latest_state:
            try:
                device_dict["state"][latest_state.state_key] = json.loads(latest_state.state_value) if latest_state.state_value.startswith('{') else latest_state.state_value
            except:
                device_dict["state"][latest_state.state_key] = latest_state.state_value
        
        device_list.append(device_dict)
    
    return {"devices": device_list}


@router.post("/devices/{device_id}/bulb")
async def control_bulb(
    device_id: str,
    state: str,  # "on" or "off"
    brightness: int = 255,
    db: AsyncSession = Depends(get_db)
):
    """Control bulb on ESP32-2."""
    if not MQTT_AVAILABLE:
        raise HTTPException(status_code=503, detail="MQTT client not available")
    
    if state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")
    
    if brightness < 0 or brightness > 255:
        raise HTTPException(status_code=400, detail="Brightness must be between 0 and 255")
    
    client = get_mqtt_client()
    if not client or not client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT broker not connected")
    
    # Send command
    success = client.send_bulb_command(device_id, state, brightness)
    
    if success:
        # Update device state in database
        device_state = IoTDeviceState(
            device_id=device_id,
            state_key="bulb_state",
            state_value=json.dumps({
                "state": state,
                "brightness": brightness
            }),
            timestamp=datetime.utcnow().isoformat()
        )
        db.add(device_state)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Bulb command sent to {device_id}",
            "state": state,
            "brightness": brightness
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send bulb command")


@router.post("/devices/{device_id}/alarm")
async def control_alarm(
    device_id: str,
    action: str,  # "enable", "disable", "test"
    db: AsyncSession = Depends(get_db)
):
    """Control alarm on ESP32-1."""
    if not MQTT_AVAILABLE:
        raise HTTPException(status_code=503, detail="MQTT client not available")
    
    if action not in ["enable", "disable", "test"]:
        raise HTTPException(status_code=400, detail="Action must be 'enable', 'disable', or 'test'")
    
    client = get_mqtt_client()
    if not client or not client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT broker not connected")
    
    # Send command
    success = client.send_alarm_command(device_id, action)
    
    if success:
        # Update device state in database
        state = IoTDeviceState(
            device_id=device_id,
            state_key="alarm_enabled",
            state_value="true" if action == "enable" else "false",
            timestamp=datetime.utcnow().isoformat()
        )
        db.add(state)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Alarm {action} command sent to {device_id}",
            "action": action
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send alarm command")


@router.post("/devices/{device_id}/buzzer")
async def control_buzzer(
    device_id: str,
    action: str,  # "on", "off", "beep"
    duration: int = 1000,  # Duration in milliseconds for beep
    db: AsyncSession = Depends(get_db)
):
    """Control buzzer on ESP32-1."""
    if not MQTT_AVAILABLE:
        raise HTTPException(status_code=503, detail="MQTT client not available")
    
    if action not in ["on", "off", "beep"]:
        raise HTTPException(status_code=400, detail="Action must be 'on', 'off', or 'beep'")
    
    client = get_mqtt_client()
    if not client or not client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT broker not connected")
    
    # Send command
    success = client.send_buzzer_command(device_id, action, duration)
    
    if success:
        # Update device state in database
        state = IoTDeviceState(
            device_id=device_id,
            state_key="buzzer_state",
            state_value=action,
            timestamp=datetime.utcnow().isoformat()
        )
        db.add(state)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Buzzer {action} command sent to {device_id}",
            "action": action,
            "duration": duration if action == "beep" else None
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send buzzer command")


@router.post("/devices/{device_id}/led")
async def control_led(
    device_id: str,
    action: str,  # "on", "off", "auto"
    db: AsyncSession = Depends(get_db)
):
    """Control LED on ESP32-1."""
    if not MQTT_AVAILABLE:
        raise HTTPException(status_code=503, detail="MQTT client not available")
    
    if action not in ["on", "off", "auto"]:
        raise HTTPException(status_code=400, detail="Action must be 'on', 'off', or 'auto'")
    
    client = get_mqtt_client()
    if not client or not client.is_connected():
        raise HTTPException(status_code=503, detail="MQTT broker not connected")
    
    # Send command
    success = client.send_led_command(device_id, action)
    
    if success:
        # Update device state in database
        state = IoTDeviceState(
            device_id=device_id,
            state_key="led_state",
            state_value=action,
            timestamp=datetime.utcnow().isoformat()
        )
        db.add(state)
        await db.commit()
        
        return {
            "success": True,
            "message": f"LED {action} command sent to {device_id}",
            "action": action
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send LED command")


@router.get("/devices/{device_id}/state")
async def get_device_state(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current state of an IoT device."""
    result = await db.execute(
        select(IoTDeviceState)
        .where(IoTDeviceState.device_id == device_id)
        .order_by(IoTDeviceState.timestamp.desc())
    )
    states = result.scalars().all()
    
    state_dict = {}
    for state in states:
        try:
            state_dict[state.state_key] = json.loads(state.state_value) if state.state_value.startswith('{') else state.state_value
        except:
            state_dict[state.state_key] = state.state_value
    
    return {
        "device_id": device_id,
        "state": state_dict,
        "last_updated": states[0].timestamp if states else None
    }


@router.get("/mqtt/status")
async def get_mqtt_status():
    """Get MQTT broker connection status."""
    if not MQTT_AVAILABLE:
        return {
            "available": False,
            "connected": False,
            "message": "MQTT library not installed"
        }
    
    client = get_mqtt_client()
    if client:
        return {
            "available": True,
            "connected": client.is_connected(),
            "broker_host": client.broker_host,
            "broker_port": client.broker_port
        }
    else:
        return {
            "available": True,
            "connected": False,
            "message": "MQTT client not initialized"
        }


@router.post("/mqtt/connect")
async def connect_mqtt(host: str = "127.0.0.1", port: int = 1883):
    """Connect to MQTT broker."""
    if not MQTT_AVAILABLE:
        raise HTTPException(status_code=503, detail="MQTT library not installed")
    
    from ..iot import initialize_mqtt
    success = initialize_mqtt(broker_host=host, broker_port=port)
    
    if success:
        return {"success": True, "message": f"Connected to MQTT broker at {host}:{port}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to MQTT broker")
