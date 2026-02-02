# Serial Monitor Logging Guide

## Serial Monitor Setup

**Important Settings:**
- **Baud Rate**: `115200`
- **Line Ending**: `Newline` or `Both NL & CR`
- **Port**: Select the correct COM port (Windows) or `/dev/ttyUSB0` (Linux)

## What You Should See

### ESP32-1 (Motion Sensor & Buzzer)

**On Startup:**
```
========================================
ESP32-1: Motion Sensor & Buzzer
========================================
Starting up...
PIR Motion Sensor System Ready
Waiting for motion...

Initializing WiFi...
Connecting to Mikro
[WiFi] ✓ Connected successfully!
[WiFi] IP address: 10.0.0.5
[WiFi] Signal strength (RSSI): -45 dBm

Configuring MQTT...
Attempting MQTT connection...
[MQTT] ✓ Connected successfully!
[MQTT] ✓ Subscribed to: rpi/broadcast
[MQTT] Ready to receive commands from web interface

Setup complete! Entering main loop...
```

**Every 10 Seconds (Status Update):**
```
Status - WiFi: Connected | MQTT: Connected | Motion: NO | Alarm: DISABLED | IP: 10.0.0.5
```

**When Motion Detected:**
```
[Motion] ⚠ MOTION DETECTED!
Published motion event: {"motion_detected":true,"timestamp":12345}
```

**When Command Received:**
```
[MQTT] >>> Message received!
[MQTT] Topic: rpi/broadcast
[MQTT] Data: {"device":"esp32-1","command":"buzzer_control","action":"on",...}
[MQTT] Processing command: buzzer_control
[Buzzer] ✓ Turned ON
```

### ESP32-2 (RGB Controller)

**On Startup:**
```
========================================
ESP32-2: RGB LED Controller
========================================
Starting up...
NeoPixel strip initialized

Initializing WiFi...
Connecting to Mikro
[WiFi] ✓ Connected successfully!
[WiFi] IP address: 10.0.0.6
[WiFi] Signal strength (RSSI): -50 dBm

Configuring MQTT...
Attempting MQTT connection...
[MQTT] ✓ Connected successfully!
[MQTT] ✓ Subscribed to: rpi/broadcast
[MQTT] Ready to receive RGB commands from web interface

Setup complete! Entering main loop...
```

**Every 10 Seconds (Status Update):**
```
Status - WiFi: Connected | MQTT: Connected | RGB: R=255 G=0 B=0 | Brightness: 255 | Effect: solid | IP: 10.0.0.6
```

**When Command Received:**
```
[MQTT] >>> Message received!
[MQTT] Topic: rpi/broadcast
[MQTT] Data: {"device":"esp32-2","command":"rgb_control","color":"#FF0000",...}
[MQTT] Processing command: rgb_control
[RGB] ✓ Command received - Color: #FF0000 | Brightness: 255 | Effect: solid
RGB set to: R=255 G=0 B=0 Brightness=255
```

## Troubleshooting: No Serial Output

### Issue 1: Serial Monitor Not Configured

**Check:**
1. Baud rate is set to **115200**
2. Correct COM port selected
3. Serial Monitor is open (not just Serial Port)

**Fix:**
- Tools → Serial Monitor
- Set baud rate to 115200
- Select correct port

### Issue 2: Wrong Port Selected

**Check available ports:**
- Windows: Device Manager → Ports (COM & LPT)
- Linux: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`

**Fix:**
- Select the correct port in Arduino IDE
- Tools → Port → Select your ESP32 port

### Issue 3: ESP32 Not Resetting

**Try:**
1. Press RESET button on ESP32
2. Or unplug/replug USB cable
3. Or click Upload button again (will reset)

### Issue 4: Code Not Uploaded

**Check:**
- Upload should show "Done uploading"
- No errors during upload

**Fix:**
- Re-upload the code
- Check for upload errors

### Issue 5: Serial.begin Delay Issue

The code now has a 500ms delay after `Serial.begin(115200)` to ensure Serial is ready. If you still don't see output:

**Try:**
1. Open Serial Monitor BEFORE uploading
2. Or wait a few seconds after upload
3. Press RESET button on ESP32

## Expected Logging Frequency

- **Startup**: Immediate (on reset/upload)
- **WiFi Connection**: During setup
- **MQTT Connection**: During setup
- **Status Updates**: Every 10 seconds
- **Motion Events**: When motion detected/stops
- **Commands**: When web interface sends commands
- **Errors**: Immediately when they occur

## What Changed

I've added:
1. ✅ More detailed startup messages
2. ✅ Periodic status logging (every 10 seconds)
3. ✅ Better formatted messages with prefixes ([WiFi], [MQTT], etc.)
4. ✅ Increased delay after Serial.begin (500ms)
5. ✅ More verbose connection status
6. ✅ Command processing logs

## Quick Test

1. **Upload code** to ESP32
2. **Open Serial Monitor** (115200 baud)
3. **Press RESET** button on ESP32
4. **You should immediately see** startup messages

If you see nothing:
- Check baud rate (must be 115200)
- Check port selection
- Try pressing RESET button
- Try re-uploading code
