# IoT Web Interface - Testing Guide

This guide provides step-by-step instructions for testing the IoT device control web interface.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Testing MQTT Connection](#testing-mqtt-connection)
4. [Testing RGB LED Control](#testing-rgb-led-control)
5. [Testing Buzzer Control](#testing-buzzer-control)
6. [Testing Motion Sensor](#testing-motion-sensor)
7. [Testing Alarm System](#testing-alarm-system)
8. [End-to-End Testing](#end-to-end-testing)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements
- Raspberry Pi (acting as access point)
- ESP32-1 (Motion sensor with buzzer)
- ESP32-2 (RGB LED controller)
- MQTT broker running on Raspberry Pi

### Software Requirements
- Web interface running on Raspberry Pi
- MQTT broker (Mosquitto) installed and running
- ESP32 devices connected to WiFi and subscribed to MQTT topics

## Initial Setup

### Step 1: Verify MQTT Broker

```bash
# Check if Mosquitto is installed
which mosquitto

# Check if service is running
sudo systemctl status mosquitto

# If not running, start it
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Step 2: Test MQTT Broker Manually

Open two terminal windows:

**Terminal 1 - Subscribe:**
```bash
mosquitto_sub -h localhost -t "rpi/broadcast" -v
```

**Terminal 2 - Publish:**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"test": "message"}'
```

You should see the message appear in Terminal 1. If not, check broker configuration.

### Step 3: Register IoT Devices

```bash
cd Web-Interface
source venv/bin/activate
python3 setup_iot_devices.py
```

Expected output:
```
============================================================
    Setting up IoT Devices
============================================================
[✓] Registered ESP32-1 (Motion Sensor & Buzzer)
[✓] Registered ESP32-2 (RGB Controller)
[✓] IoT devices setup complete!
```

### Step 4: Start Web Server

```bash
cd Web-Interface
./start_web_server.sh
```

Expected output:
```
======================================================
    Starting Loki IDS Web Interface
======================================================
[*] Using Python 3.13
[*] Checking dependencies...
[✓] All critical packages are installed
[*] Starting FastAPI server...
[*] Dashboard will be available at: http://localhost:8080
[*] API documentation at: http://localhost:8080/docs
[*] Database initialized
[*] MQTT client connected to 127.0.0.1:1883
```

### Step 5: Open Web Interface

Open browser and navigate to:
- **Local**: http://localhost:8080
- **From another device**: http://<raspberry-pi-ip>:8080

Click on the **"IoT Control"** tab.

## Testing MQTT Connection

### Test 1: Check MQTT Status Indicator

1. Open IoT Control tab
2. Look at the MQTT status indicator (top right)
3. **Expected**: Green badge showing "MQTT: Connected"

**If disconnected:**
- Click "Connect MQTT" button
- Status should change to green

### Test 2: Verify MQTT Connection via API

```bash
curl http://localhost:8080/api/iot/mqtt/status
```

**Expected response:**
```json
{
  "available": true,
  "connected": true,
  "broker_host": "127.0.0.1",
  "broker_port": 1883
}
```

### Test 3: Monitor MQTT Messages

In a terminal, subscribe to see all commands:

```bash
mosquitto_sub -h localhost -t "rpi/broadcast" -v
```

Keep this running while testing - you should see JSON commands appear when you use the web interface.

## Testing RGB LED Control

### Test 1: Basic Color Change

1. In IoT Control tab, find "ESP32 RGB Controller"
2. Click the color picker
3. Select a color (e.g., red #FF0000)
4. Click "Apply"
5. **Expected**: 
   - Success message appears
   - ESP32-2 LED changes to selected color
   - MQTT message appears in terminal (if monitoring)

**Verify MQTT message:**
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

### Test 2: Brightness Control

1. Select any color
2. Move brightness slider to 50 (low brightness)
3. Click "Apply"
4. **Expected**: LED dims
5. Move slider to 255 (full brightness)
6. Click "Apply"
7. **Expected**: LED brightens

### Test 3: Effect Selection

Test each effect:
1. Select color (e.g., blue)
2. Select "Solid" effect → Click Apply
   - **Expected**: Static blue color
3. Select "Fade" effect → Click Apply
   - **Expected**: Smooth color transitions
4. Select "Rainbow" effect → Click Apply
   - **Expected**: Color cycling through spectrum
5. Select "Blink" effect → Click Apply
   - **Expected**: Flashing effect

### Test 4: API Direct Test

```bash
# Test RGB control via API
curl -X POST "http://localhost:8080/api/iot/devices/esp32-2/rgb?color=%23FF0000&brightness=255&effect=solid"
```

**Expected response:**
```json
{
  "success": true,
  "message": "RGB command sent to esp32-2",
  "color": "#FF0000",
  "brightness": 255,
  "effect": "solid"
}
```

## Testing Buzzer Control

### Test 1: Buzzer ON

1. Find "ESP32 Motion Sensor & Buzzer" device
2. Click "Buzzer ON" button
3. **Expected**: 
   - Buzzer turns on continuously
   - Success message appears
   - MQTT message sent

**Verify MQTT message:**
```json
{
  "device": "esp32-1",
  "command": "buzzer_control",
  "action": "on",
  "duration": 1000,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Test 2: Buzzer OFF

1. Click "Buzzer OFF" button
2. **Expected**: Buzzer stops immediately

### Test 3: Beep Durations

Test each beep button:
1. Click "Beep (0.5s)"
   - **Expected**: Short beep (~0.5 seconds)
2. Click "Beep (1s)"
   - **Expected**: Standard beep (~1 second)
3. Click "Beep (2s)"
   - **Expected**: Long beep (~2 seconds)

### Test 4: API Direct Test

```bash
# Test buzzer ON
curl -X POST "http://localhost:8080/api/iot/devices/esp32-1/buzzer?action=on"

# Test buzzer OFF
curl -X POST "http://localhost:8080/api/iot/devices/esp32-1/buzzer?action=off"

# Test beep
curl -X POST "http://localhost:8080/api/iot/devices/esp32-1/buzzer?action=beep&duration=1000"
```

## Testing Motion Sensor

### Test 1: Motion Detection Display

1. In IoT Control tab, find "ESP32 Motion Sensor & Buzzer"
2. Look at "Motion Sensor Status"
3. **Expected**: Shows "Motion Detected: YES" or "NO" with color coding
   - Green = No motion
   - Red = Motion detected

### Test 2: Real-time Updates

1. Trigger motion sensor (wave hand in front of PIR sensor)
2. **Expected**: 
   - Status changes to "YES" (red)
   - ESP32-1 publishes to `esp32/sensor1` topic

**Verify MQTT message:**
```bash
mosquitto_sub -h localhost -t "esp32/sensor1" -v
```

**Expected message:**
```json
{
  "motion_detected": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Test 3: Motion Event Frequency

1. Monitor `esp32/sensor1` topic
2. Trigger motion sensor multiple times
3. **Expected**: Multiple messages published (typically every 4 seconds as per your ESP32 code)

## Testing Alarm System

### Test 1: Enable Alarm

1. Find "ESP32 Motion Sensor & Buzzer"
2. Click "Enable Alarm" button
3. **Expected**: 
   - Success message
   - Alarm system activates
   - MQTT command sent

**Verify MQTT message:**
```json
{
  "device": "esp32-1",
  "command": "alarm_control",
  "action": "enable",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Test 2: Disable Alarm

1. Click "Disable Alarm" button
2. **Expected**: Alarm system deactivates

### Test 3: Test Alarm

1. Click "Test Alarm" button
2. **Expected**: 
   - Alarm triggers (buzzer + LED)
   - Test sequence completes

### Test 4: Alarm with Motion

1. Enable alarm
2. Trigger motion sensor
3. **Expected**: 
   - Motion detected
   - Alarm activates (buzzer + LED)
   - Visual and auditory alerts

## End-to-End Testing

### Scenario 1: Complete Workflow

1. **Setup**: Ensure all devices connected
2. **Enable Alarm**: Click "Enable Alarm"
3. **Trigger Motion**: Wave hand in front of sensor
4. **Expected**: 
   - Motion detected (status shows YES)
   - Alarm activates (buzzer + LED)
   - Web interface updates in real-time
5. **Change RGB**: Select red color, apply
6. **Expected**: RGB LED changes to red
7. **Disable Alarm**: Click "Disable Alarm"
8. **Expected**: Alarm stops

### Scenario 2: Multiple Commands

1. Send RGB command (blue, brightness 128, fade effect)
2. Send buzzer beep (1 second)
3. Send alarm enable
4. **Expected**: All commands execute correctly

### Scenario 3: Device State Persistence

1. Set RGB to green, brightness 200
2. Refresh page
3. **Expected**: Device state persists (stored in database)

## API Testing

### Test All Endpoints

```bash
# Get all devices
curl http://localhost:8080/api/iot/devices

# Get device state
curl http://localhost:8080/api/iot/devices/esp32-1/state

# Get MQTT status
curl http://localhost:8080/api/iot/mqtt/status

# Connect MQTT
curl -X POST "http://localhost:8080/api/iot/mqtt/connect?host=127.0.0.1&port=1883"
```

## Troubleshooting

### Issue: MQTT Not Connecting

**Symptoms:**
- Status shows "Disconnected" or "Not Available"
- Commands don't work

**Solutions:**
1. Check broker status:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Restart broker:
   ```bash
   sudo systemctl restart mosquitto
   ```

3. Check broker logs:
   ```bash
   sudo journalctl -u mosquitto -f
   ```

4. Test broker manually:
   ```bash
   mosquitto_pub -h localhost -t test -m "test"
   mosquitto_sub -h localhost -t test
   ```

5. Check firewall:
   ```bash
   sudo ufw allow 1883/tcp
   ```

### Issue: Commands Not Reaching ESP32

**Symptoms:**
- Web interface shows success
- ESP32 doesn't respond

**Solutions:**
1. Verify ESP32 is connected to WiFi
2. Verify ESP32 is subscribed to `rpi/broadcast`
3. Monitor MQTT messages:
   ```bash
   mosquitto_sub -h localhost -t "rpi/broadcast" -v
   ```
4. Check ESP32 serial output for errors
5. Verify ESP32 code parses JSON correctly

### Issue: Motion Sensor Not Updating

**Symptoms:**
- Motion detected but web interface doesn't update

**Solutions:**
1. Check ESP32-1 is publishing to `esp32/sensor1`:
   ```bash
   mosquitto_sub -h localhost -t "esp32/sensor1" -v
   ```
2. Verify MQTT client is subscribed to sensor topic
3. Check database for stored states:
   ```bash
   sqlite3 loki_ids.db "SELECT * FROM iot_device_states ORDER BY timestamp DESC LIMIT 10;"
   ```

### Issue: RGB LED Not Responding

**Symptoms:**
- Command sent but LED doesn't change

**Solutions:**
1. Verify ESP32-2 is connected
2. Check ESP32-2 code handles `rgb_control` command
3. Verify color format (hex string like "#FF0000")
4. Test with simple color first (solid, full brightness)
5. Check ESP32 serial output for parsing errors

### Issue: Buzzer Not Working

**Symptoms:**
- Command sent but no sound

**Solutions:**
1. Test buzzer directly on ESP32 (bypass MQTT)
2. Verify GPIO pin connection
3. Check ESP32 code handles `buzzer_control` command
4. Test with different actions (on, off, beep)
5. Check ESP32 serial output

## Test Checklist

Use this checklist to verify all functionality:

### Setup
- [ ] MQTT broker running
- [ ] Web server running
- [ ] Devices registered in database
- [ ] ESP32-1 connected to WiFi
- [ ] ESP32-2 connected to WiFi
- [ ] ESP32-1 subscribed to `rpi/broadcast`
- [ ] ESP32-2 subscribed to `rpi/broadcast`

### MQTT Connection
- [ ] MQTT status shows "Connected" (green)
- [ ] Can connect manually via "Connect MQTT" button
- [ ] API returns connected status

### RGB LED Control
- [ ] Color picker works
- [ ] Brightness slider works
- [ ] Effect selector works
- [ ] Apply button sends command
- [ ] LED changes color
- [ ] LED changes brightness
- [ ] LED shows effects (solid, fade, rainbow, blink)

### Buzzer Control
- [ ] Buzzer ON works
- [ ] Buzzer OFF works
- [ ] Beep (0.5s) works
- [ ] Beep (1s) works
- [ ] Beep (2s) works

### Motion Sensor
- [ ] Motion status displays correctly
- [ ] Motion events published to `esp32/sensor1`
- [ ] Status updates in real-time
- [ ] Color coding works (green/red)

### Alarm System
- [ ] Enable alarm works
- [ ] Disable alarm works
- [ ] Test alarm works
- [ ] Alarm activates on motion (if enabled)

### API Endpoints
- [ ] GET /api/iot/devices returns devices
- [ ] POST /api/iot/devices/{id}/rgb works
- [ ] POST /api/iot/devices/{id}/buzzer works
- [ ] POST /api/iot/devices/{id}/alarm works
- [ ] GET /api/iot/devices/{id}/state returns state
- [ ] GET /api/iot/mqtt/status returns status
- [ ] POST /api/iot/mqtt/connect works

## Performance Testing

### Test Command Latency

1. Monitor MQTT messages
2. Click command in web interface
3. Measure time until MQTT message appears
4. **Expected**: < 100ms latency

### Test Multiple Rapid Commands

1. Rapidly click multiple buttons (RGB, buzzer, alarm)
2. **Expected**: All commands execute correctly
3. No commands lost or delayed

### Test Concurrent Users

1. Open web interface in multiple browsers
2. Send commands from different browsers
3. **Expected**: All commands work correctly
4. No conflicts or errors

## Logging and Debugging

### View Web Server Logs

```bash
# If running with uvicorn directly
# Logs appear in terminal

# If running as service
sudo journalctl -u loki-web -f
```

### View MQTT Broker Logs

```bash
sudo journalctl -u mosquitto -f
```

### View Database

```bash
sqlite3 Web-Interface/loki_ids.db

# View devices
SELECT * FROM iot_devices;

# View device states
SELECT * FROM iot_device_states ORDER BY timestamp DESC LIMIT 20;
```

### Monitor MQTT Traffic

```bash
# Monitor all commands
mosquitto_sub -h localhost -t "rpi/broadcast" -v

# Monitor motion events
mosquitto_sub -h localhost -t "esp32/sensor1" -v

# Monitor all topics
mosquitto_sub -h localhost -t "#" -v
```

## Success Criteria

All tests pass if:
- ✅ MQTT connection is stable
- ✅ All commands reach ESP32 devices
- ✅ ESP32 devices respond correctly
- ✅ Motion sensor updates in real-time
- ✅ Device states persist in database
- ✅ Web interface is responsive
- ✅ No errors in logs

## Next Steps

After successful testing:
1. Document any customizations needed
2. Note any ESP32 code changes required
3. Create user guide for end users
4. Set up monitoring/alerting if needed
