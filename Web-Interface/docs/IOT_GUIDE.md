# IoT Device Control - Complete Guide

This guide covers everything you need to know about controlling ESP32 IoT devices through the web interface.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Device Setup](#device-setup)
3. [Using the Web Interface](#using-the-web-interface)
4. [MQTT Configuration](#mqtt-configuration)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

## Quick Start

### 1. Register Devices
```bash
cd Web-Interface
venv/bin/python3 setup_iot_devices.py
```

### 2. Start Web Server
```bash
./start_web_server.sh
```

### 3. Access Interface
Open http://localhost:8080 and click "IoT Control" tab

## Device Setup

### Register Devices in Database

Devices must be registered before they appear in the web interface:

```bash
cd Web-Interface
venv/bin/python3 setup_iot_devices.py
```

This registers:
- **ESP32-1**: Motion Sensor & Buzzer
- **ESP32-2**: RGB LED Controller

### Verify Devices

```bash
sqlite3 loki_ids.db "SELECT device_id, name, device_type FROM iot_devices;"
```

## Using the Web Interface

### Accessing IoT Control

1. Open: http://localhost:8080
2. Click **"IoT Control"** tab
3. Check MQTT status indicator (should be green)

### RGB LED Control (ESP32-2)

- **Color Picker**: Select any color
- **Brightness**: Slider (0-255)
- **Effects**: Solid, Fade, Rainbow, Blink
- **Apply**: Sends command to device

### Buzzer Control (ESP32-1)

- **Buzzer ON**: Continuous sound
- **Buzzer OFF**: Stop buzzer
- **Beep**: Short beeps (0.5s, 1s, 2s)

### Motion Sensor (ESP32-1)

- Real-time motion detection status
- Shows YES/NO with color coding
- Updates automatically

### Alarm System (ESP32-1)

- **Enable Alarm**: Activate alarm system
- **Disable Alarm**: Deactivate alarm system
- **Test Alarm**: Trigger test sequence

## MQTT Configuration

### MQTT Broker Setup

The MQTT broker should be running on your Raspberry Pi:

```bash
# Check status
sudo systemctl status mosquitto

# Start if needed
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Connection Status

The web interface shows MQTT status:
- **Green**: Connected
- **Yellow**: Disconnected (broker available)
- **Red**: Not available

### Manual Connection

If disconnected, click "Connect MQTT" button. It will try:
1. `127.0.0.1` (localhost)
2. `localhost`
3. `10.0.0.1` (common AP IP)

If auto-connect fails, you'll be prompted to enter the Raspberry Pi IP address.

### MQTT Topics

- **`rpi/broadcast`**: Commands from web interface to ESP32s
- **`esp32/sensor1`**: Motion events from ESP32-1

## Testing

### Test Checklist

- [ ] Devices registered in database
- [ ] Web server running
- [ ] MQTT broker running
- [ ] MQTT status shows "Connected"
- [ ] ESP32-1 connected to WiFi
- [ ] ESP32-1 connected to MQTT
- [ ] ESP32-2 connected to WiFi
- [ ] ESP32-2 connected to MQTT
- [ ] Devices appear in web interface
- [ ] Buzzer commands work
- [ ] RGB commands work

### Quick Tests

**Test Buzzer:**
1. Click "Buzzer ON" → Should hear buzzer
2. Click "Buzzer OFF" → Buzzer stops

**Test RGB:**
1. Select color (e.g., red)
2. Adjust brightness
3. Click "Apply" → LED should change

**Test Motion:**
1. Trigger motion sensor
2. Status should update to "YES"

## Troubleshooting

### Devices Not Showing

**Solution:**
```bash
venv/bin/python3 setup_iot_devices.py
```

**Verify:**
```bash
sqlite3 loki_ids.db "SELECT * FROM iot_devices;"
```

### MQTT Not Connecting

**Check broker:**
```bash
sudo systemctl status mosquitto
```

**Test connection:**
```bash
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

**Check firewall:**
```bash
sudo ufw allow 1883/tcp
```

**See:** [MQTT Troubleshooting Guide](MQTT_TROUBLESHOOTING.md)

### Commands Not Working

1. Verify MQTT status shows "Connected"
2. Check ESP32 Serial Monitor for errors
3. Verify ESP32s are subscribed to `rpi/broadcast`
4. Check MQTT broker logs: `sudo journalctl -u mosquitto -f`

### ESP32 Not Responding

1. Check Serial Monitor (115200 baud)
2. Verify WiFi connection
3. Verify MQTT connection
4. Check device ID matches (`esp32-1` or `esp32-2`)

## API Reference

### Endpoints

- `GET /api/iot/devices` - List all devices
- `GET /api/iot/devices/{id}/state` - Get device state
- `POST /api/iot/devices/{id}/rgb` - Control RGB LED
- `POST /api/iot/devices/{id}/buzzer` - Control buzzer
- `POST /api/iot/devices/{id}/alarm` - Control alarm
- `GET /api/iot/mqtt/status` - Check MQTT status
- `POST /api/iot/mqtt/connect` - Connect to broker

### Command Formats

**RGB Control:**
```json
POST /api/iot/devices/esp32-2/rgb?color=#FF0000&brightness=255&effect=solid
```

**Buzzer Control:**
```json
POST /api/iot/devices/esp32-1/buzzer?action=beep&duration=1000
```

**Alarm Control:**
```json
POST /api/iot/devices/esp32-1/alarm?action=enable
```

## ESP32 Firmware

See [ESP32_FIRMWARE_REQUIREMENTS.md](../ESP32_FIRMWARE_REQUIREMENTS.md) for firmware details.

## Related Documentation

- [MQTT Troubleshooting](MQTT_TROUBLESHOOTING.md)
- [Database Schema](../DATABASE_SCHEMA.md)
- [ESP32 Firmware Requirements](../ESP32_FIRMWARE_REQUIREMENTS.md)
