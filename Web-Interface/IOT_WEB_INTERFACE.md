# IoT Device Web Interface - Quick Reference

## Overview

The web interface provides complete control over your IoT devices:
- **RGB LED Light** (ESP32-2)
- **Motion Sensor** (ESP32-1)
- **Buzzer** (ESP32-1)

## Access the Interface

1. Start the web server:
   ```bash
   cd Web-Interface
   ./start_web_server.sh
   ```

2. Open browser: http://localhost:8080 (or http://<raspberry-pi-ip>:8080)

3. Click on **"IoT Control"** tab

## Device Controls

### RGB LED Light (ESP32-2)

**Controls:**
- **Color Picker**: Click to select any color
- **Brightness Slider**: Adjust from 0-255
- **Effect Selector**: Choose from:
  - Solid: Static color
  - Fade: Smooth color transitions
  - Rainbow: Color cycling effect
  - Blink: Flashing effect
- **Apply Button**: Sends command to device

**MQTT Command Format:**
```json
{
  "device": "esp32-2",
  "command": "rgb_control",
  "color": "#FF0000",
  "brightness": 255,
  "effect": "solid"
}
```

### Motion Sensor (ESP32-1)

**Status Display:**
- Shows real-time motion detection status (YES/NO)
- Updates automatically when motion is detected

**MQTT Topic:** `esp32/sensor1`

### Buzzer Control (ESP32-1)

**Control Buttons:**
- **Buzzer ON**: Turns buzzer on continuously
- **Buzzer OFF**: Turns buzzer off
- **Beep (0.5s)**: Short beep
- **Beep (1s)**: Standard beep
- **Beep (2s)**: Long beep

**MQTT Command Format:**
```json
{
  "device": "esp32-1",
  "command": "buzzer_control",
  "action": "beep",
  "duration": 1000
}
```

### Alarm System (ESP32-1)

**Control Buttons:**
- **Enable Alarm**: Activates the alarm system
- **Disable Alarm**: Deactivates the alarm system
- **Test Alarm**: Triggers a test alarm

**MQTT Command Format:**
```json
{
  "device": "esp32-1",
  "command": "alarm_control",
  "action": "enable"
}
```

## MQTT Connection

### Status Indicator

The interface shows MQTT connection status:
- **Green**: Connected to broker
- **Yellow**: Disconnected (broker available)
- **Red**: Not available

### Manual Connection

If disconnected, click **"Connect MQTT"** button. The system will try:
1. `127.0.0.1` (localhost - since RPi is the AP)
2. `localhost`
3. `10.0.0.1` (common AP IP)

### MQTT Broker Setup

Since the Raspberry Pi is the access point, the MQTT broker should be running on the Pi:

```bash
# Install Mosquitto (if not already installed)
sudo apt-get install mosquitto mosquitto-clients

# Start MQTT broker
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Verify it's running
sudo systemctl status mosquitto
```

## API Endpoints

All endpoints are under `/api/iot/`:

- `GET /api/iot/devices` - List all devices
- `POST /api/iot/devices/{id}/rgb` - Control RGB LED
- `POST /api/iot/devices/{id}/buzzer` - Control buzzer
- `POST /api/iot/devices/{id}/alarm` - Control alarm
- `GET /api/iot/devices/{id}/state` - Get device state
- `GET /api/iot/mqtt/status` - Check MQTT status
- `POST /api/iot/mqtt/connect` - Connect to broker

## Initial Setup

1. **Register Devices:**
   ```bash
   cd Web-Interface
   venv/bin/python3 setup_iot_devices.py
   ```

2. **Start Web Server:**
   ```bash
   ./start_web_server.sh
   ```

3. **Ensure MQTT Broker is Running:**
   ```bash
   sudo systemctl status mosquitto
   ```

## Troubleshooting

### Devices Not Showing

Run the setup script:
```bash
venv/bin/python3 setup_iot_devices.py
```

### MQTT Not Connecting

1. Check broker status:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Test MQTT connection:
   ```bash
   mosquitto_pub -h localhost -t test -m "hello"
   mosquitto_sub -h localhost -t test
   ```

3. Check firewall:
   ```bash
   sudo ufw allow 1883/tcp
   ```

### Commands Not Working

1. Verify MQTT status shows "Connected"
2. Check ESP32 devices are connected to WiFi
3. Verify ESP32s are subscribed to `rpi/broadcast` topic
4. Check MQTT broker logs:
   ```bash
   sudo journalctl -u mosquitto -f
   ```

## ESP32 Requirements

Your ESP32 devices should:

1. **Connect to WiFi** (Raspberry Pi access point)
2. **Connect to MQTT broker** at `127.0.0.1` or the RPi's IP
3. **Subscribe to** `rpi/broadcast` for commands
4. **Publish to** `esp32/sensor1` for motion events (ESP32-1)

### Command Parsing

ESP32s should parse JSON commands from `rpi/broadcast`:

```c
// Example command structure
{
  "device": "esp32-1",  // or "esp32-2"
  "command": "buzzer_control",  // or "rgb_control", "alarm_control"
  "action": "beep",  // or "on", "off", "enable", "disable", "test"
  "duration": 1000,  // for buzzer beep
  "color": "#FF0000",  // for RGB
  "brightness": 255,  // for RGB
  "effect": "solid"  // for RGB
}
```

## Quick Test

1. Open IoT Control tab
2. Click "Buzzer ON" - should hear buzzer
3. Click "Buzzer OFF" - buzzer stops
4. Change RGB color and click "Apply" - LED should change
5. Enable alarm - alarm system activates

All commands are sent via MQTT and logged in the database!
