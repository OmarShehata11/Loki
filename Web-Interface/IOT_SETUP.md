# IoT Device Control Setup Guide

This guide explains how to set up and use the IoT device control system for ESP32 devices connected via MQTT.

## Overview

The IoT control system allows you to:
- Control RGB LED strips on ESP32-2
- Monitor and control motion sensors and alarms on ESP32-1
- View real-time device states
- Send commands via MQTT protocol

## Architecture

```
Raspberry Pi (10.0.0.1)
├── MQTT Broker (port 1883)
├── Loki IDS Web Interface
└── ESP32 Devices
    ├── ESP32-1: Motion Sensor (PIR, Buzzer, LED)
    └── ESP32-2: RGB Controller (NeoPixel LED Strip)
```

## Prerequisites

1. **MQTT Broker** running on Raspberry Pi at `10.0.0.1:1883`
   - Install Mosquitto: `sudo apt-get install mosquitto mosquitto-clients`
   - Start service: `sudo systemctl start mosquitto`

2. **ESP32 Devices** configured and connected to WiFi
   - ESP32-1 publishes to: `esp32/sensor1`
   - ESP32-2 subscribes to: `rpi/broadcast`

3. **Python Dependencies**
   - `paho-mqtt` (automatically installed with requirements.txt)

## Setup Steps

### 1. Install Dependencies

```bash
cd /path/to/Loki-IDS/Web-Interface
source venv/bin/activate
pip install -r requirements.txt
```

This will install `paho-mqtt>=2.0.0` along with other dependencies.

### 2. Initialize Database

The database is automatically initialized when you start the web server. If you need to initialize manually:

```bash
python3 init_database.py
```

### 3. Register IoT Devices

Register the default ESP32 devices in the database:

```bash
# Using venv Python
venv/bin/python3 setup_iot_devices.py

# Or if venv is activated
python3 setup_iot_devices.py
```

This will register:
- **ESP32-1**: Motion sensor device
- **ESP32-2**: RGB LED controller

### 4. Start Web Server

```bash
./start_web_server.sh
```

The MQTT client will automatically try to connect to the broker at `10.0.0.1:1883` on startup.

### 5. Access IoT Control Panel

1. Open the dashboard: http://localhost:8080
2. Click on the **"IoT Control"** tab
3. Check MQTT connection status
4. If disconnected, click "Connect MQTT" button

## MQTT Topics

### Published by Raspberry Pi (Commands)
- **`rpi/broadcast`**: Broadcast commands to all devices
  - Format: JSON with `device`, `command`, and parameters

### Published by ESP32 Devices (Sensor Data)
- **`esp32/sensor1`**: Motion detection events from ESP32-1
- **`esp32/status`**: Device status updates

## Device Control

### RGB LED Control (ESP32-2)

1. Navigate to IoT Control tab
2. Find the RGB Controller device
3. Select color using color picker
4. Adjust brightness (0-255)
5. Choose effect: Solid, Fade, Rainbow, Blink
6. Click "Apply" to send command

**API Endpoint:**
```http
POST /api/iot/devices/esp32-2/rgb?color=#FF0000&brightness=255&effect=solid
```

### Alarm Control (ESP32-1)

1. Navigate to IoT Control tab
2. Find the Motion Sensor device
3. View current motion detection status
4. Control alarm:
   - **Enable Alarm**: Activates alarm system
   - **Disable Alarm**: Deactivates alarm system
   - **Test Alarm**: Triggers test alarm

**API Endpoint:**
```http
POST /api/iot/devices/esp32-1/alarm?action=enable
POST /api/iot/devices/esp32-1/alarm?action=disable
POST /api/iot/devices/esp32-1/alarm?action=test
```

## API Endpoints

### Get All Devices
```http
GET /api/iot/devices
```

### Get Device State
```http
GET /api/iot/devices/{device_id}/state
```

### MQTT Status
```http
GET /api/iot/mqtt/status
```

### Connect to MQTT
```http
POST /api/iot/mqtt/connect?host=10.0.0.1&port=1883
```

## Troubleshooting

### MQTT Not Connecting

1. **Check MQTT Broker Status:**
   ```bash
   sudo systemctl status mosquitto
   ```

2. **Test MQTT Connection:**
   ```bash
   mosquitto_pub -h 10.0.0.1 -t test/topic -m "test"
   mosquitto_sub -h 10.0.0.1 -t test/topic
   ```

3. **Check Firewall:**
   ```bash
   sudo ufw allow 1883/tcp
   ```

4. **Verify IP Address:**
   - Ensure Raspberry Pi IP is `10.0.0.1`
   - Or update in `api/iot/mqtt_client.py` and reconnect

### Devices Not Appearing

1. **Check Database:**
   ```bash
   python3 setup_iot_devices.py
   ```

2. **Verify Device Registration:**
   - Check database: `sqlite3 loki_ids.db "SELECT * FROM iot_devices;"`

### Commands Not Working

1. **Check MQTT Connection Status** in the IoT Control tab
2. **Verify ESP32 Devices** are connected to WiFi and subscribed to topics
3. **Check MQTT Broker Logs:**
   ```bash
   sudo journalctl -u mosquitto -f
   ```

## ESP32 Code Requirements

### ESP32-1 (Motion Sensor)

Your ESP32-1 code should:
- Connect to WiFi
- Connect to MQTT broker at `10.0.0.1:1883`
- Subscribe to `rpi/broadcast` for commands
- Publish motion events to `esp32/sensor1`
- Handle alarm commands: `enable`, `disable`, `test`

### ESP32-2 (RGB Controller)

Your ESP32-2 code should:
- Connect to WiFi
- Connect to MQTT broker at `10.0.0.1:1883`
- Subscribe to `rpi/broadcast` for commands
- Parse RGB commands with `color`, `brightness`, `effect` parameters
- Update NeoPixel LED strip accordingly

## Example MQTT Message Format

### RGB Command
```json
{
  "device": "esp32-2",
  "command": "rgb_control",
  "color": "#FF0000",
  "brightness": 255,
  "effect": "solid",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Alarm Command
```json
{
  "device": "esp32-1",
  "command": "alarm_control",
  "action": "enable",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Motion Event (from ESP32-1)
```json
{
  "motion_detected": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

## Security Notes

- MQTT broker should be on a private network (10.0.0.0/8)
- Consider adding MQTT authentication in production
- Use TLS/SSL for MQTT in production environments
- Restrict MQTT broker access to local network only

## Next Steps

- Add more ESP32 devices by running `setup_iot_devices.py` with custom device IDs
- Integrate motion detection with IDS alerts
- Create automation rules (e.g., flash RGB when motion detected)
- Add device status monitoring and health checks
