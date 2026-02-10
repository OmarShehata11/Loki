# Loki IDS - IoT Integration Guide

## System Overview

The complete Loki IDS system now consists of:
1. **IDS Core (Backend)** - Detects threats, owns database, exposes APIs
2. **Web Dashboard (Frontend)** - HTML/CSS/JS interface for monitoring and control
3. **ESP32-1** - Motion sensor with alarm/buzzer control
4. **ESP32-2** - RGB LED strip controller (bulb)

## Architecture

```
┌────────────────────────────────────────────────┐
│           Raspberry Pi (IDS Core)              │
│                                                │
│  ┌──────────────┐        ┌─────────────────┐  │
│  │   FastAPI    │◄───────┤  Packet         │  │
│  │   Server     │        │  Processing     │  │
│  │  (port 8080) │        │  (nfqueue)      │  │
│  └──────┬───────┘        └─────────────────┘  │
│         │                                      │
│  ┌──────▼────────┐       ┌─────────────────┐  │
│  │   Database    │       │  MQTT Broker    │  │
│  │ (loki_ids.db) │       │  (port 1883)    │  │
│  └───────────────┘       └────────┬────────┘  │
│                                   │            │
└───────────────────────────────────┼────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    │               │               │
            ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼─────┐
            │  Dashboard   │ │  ESP32-1   │ │  ESP32-2  │
            │ (Web Browser)│ │  Motion +  │ │ RGB LED   │
            │              │ │   Alarm    │ │Controller │
            └──────────────┘ └────────────┘ └───────────┘
```

## Communication Protocol

### MQTT Topics

**From Dashboard → ESP32 (Command Topic)**
- Topic: `rpi/broadcast`
- Format: JSON
```json
{
  "device": "esp32-1" or "esp32-2",
  "command": "alarm_control" / "buzzer_control" / "led_control" / "bulb_control",
  "action": "enable" / "disable" / "on" / "off" / "test",
  "brightness": 0-255,
  "duration": milliseconds,
  "timestamp": "ISO-8601"
}
```

**From ESP32 → Dashboard (Status Topic)**
- ESP32-1: `esp32/sensor1/status`
- ESP32-2: `esp32/sensor2/status`
- Format: JSON
```json
{
  "device": "esp32-1",
  "event": "online" / "motion_detected" / "heartbeat",
  "alarm_enabled": true/false,
  "alarm_active": true/false,
  "buzzer_on": true/false,
  "led_auto_mode": true/false
}
```

## ESP32 Device Specifications

### ESP32-1: Motion Sensor + Alarm
**Hardware:**
- PIR Motion Sensor (GPIO 15)
- Buzzer (GPIO 3)
- Status LED (GPIO 2)

**Capabilities:**
- Detects motion and triggers alarm
- Publishes motion events to dashboard
- Receives control commands from dashboard
- Auto-disables alarm after 5 seconds of no motion

**Dashboard Controls:**
- **Alarm Control**: Enable/Disable/Test alarm
- **Buzzer Control**: On/Off/Beep
- **LED Control**: On/Off/Auto (follows alarm state)

### ESP32-2: RGB LED Controller
**Hardware:**
- NeoPixel RGB LED Strip (4 LEDs on GPIO 15)

**Capabilities:**
- Controls RGB LED brightness (0-255)
- Turns bulb on/off from dashboard
- Publishes status updates

**Dashboard Controls:**
- **Bulb Control**: On/Off with brightness slider

## Setup Instructions

### Step 1: Flash ESP32 Firmware

**ESP32-1 (Motion Sensor):**
1. Open Arduino IDE
2. Load `esp/full-code.ino`
3. Update WiFi credentials (lines 21-22):
   ```cpp
   const char* WIFI_SSID = "YourWiFiName";
   const char* WIFI_PASS = "YourPassword";
   ```
4. Update MQTT broker IP (line 23) to your Raspberry Pi IP
5. Select board: ESP32 Dev Module
6. Upload firmware

**ESP32-2 (RGB Controller):**
1. Open Arduino IDE
2. Load `esp/Final-RGB.ino`
3. Update WiFi credentials (lines 20-21)
4. Update MQTT broker IP (line 22)
5. Select board: ESP32 Dev Module
6. Upload firmware

### Step 2: Install MQTT Broker on Raspberry Pi

```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Verify MQTT is running:
```bash
sudo systemctl status mosquitto
```

### Step 3: Register Devices in Database

```bash
cd /home/zaher/Loki-IDS/Web-Interface
../loki_env/bin/python3 setup_iot_devices.py
```

This creates device entries:
- `esp32-1`: Motion Sensor & Buzzer
- `esp32-2`: Bulb Controller

### Step 4: Start Loki IDS System

```bash
cd /home/zaher/Loki-IDS
sudo bash start_loki_system.sh
```

This starts:
1. Core API Server (port 8080)
2. IDS packet processing
3. MQTT integration

### Step 5: Access Dashboard

Open browser to: http://RASPBERRY_PI_IP:8080

Go to the **IoT Control** tab to see and control your devices.

## Using the Dashboard

### IoT Control Tab Features

**Device List:**
- Shows all registered ESP32 devices
- Real-time status indicators
- Last seen timestamp

**ESP32-1 Controls (Motion Sensor):**
- **Alarm**: Enable/Disable/Test buttons
- **Buzzer**: On/Off/Beep buttons
- **LED**: On/Off/Auto buttons
- **Status Display**: Shows if alarm is active, motion detected

**ESP32-2 Controls (RGB LED):**
- **Power**: On/Off switch
- **Brightness Slider**: Adjust brightness 0-255
- **Status Display**: Shows current state and brightness

**Status Indicators:**
- 🟢 Green: Device online and responding
- 🔴 Red: Device offline or not responding
- 🟡 Yellow: Device in warning state

## Testing the System

### Test 1: ESP32 Connectivity
1. Power on both ESP32 devices
2. Check Serial Monitor (115200 baud)
3. Verify WiFi connection
4. Verify MQTT connection
5. Should see `[✓] MQTT Connected` message

### Test 2: Dashboard Control

**Test ESP32-2 (Bulb):**
1. Open dashboard IoT tab
2. Find ESP32-2 device card
3. Click "Turn On" button
4. Adjust brightness slider
5. LED strip should change brightness
6. Check ESP32 serial monitor for `[Bulb] State: ON, Brightness: XXX`

**Test ESP32-1 (Alarm):**
1. Open dashboard IoT tab
2. Find ESP32-1 device card
3. Click "Test Alarm" button
4. Should hear buzzer sound pattern
5. Click "Enable/Disable" to toggle alarm
6. Wave hand in front of PIR sensor
7. If alarm enabled, buzzer should sound

### Test 3: Motion Detection
1. Enable alarm on ESP32-1
2. Trigger PIR sensor (wave hand)
3. Buzzer should sound
4. Dashboard should show motion alert
5. LED should turn on
6. After 5 seconds, alarm should reset

### Test 4: Real-time Updates
1. Open dashboard
2. Trigger motion on ESP32-1
3. Dashboard should update in real-time via WebSocket
4. Status indicators should change

## Troubleshooting

### ESP32 Won't Connect to WiFi
**Problem**: Serial shows "Connecting to WiFi..." forever

**Solution:**
1. Check WiFi credentials in firmware
2. Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
3. Check WiFi signal strength
4. Reboot router if needed

### ESP32 Can't Connect to MQTT
**Problem**: `Failed, rc=-2` or similar error

**Solution:**
1. Verify MQTT broker is running: `sudo systemctl status mosquitto`
2. Check MQTT broker IP in firmware matches Raspberry Pi IP
3. Test MQTT manually:
   ```bash
   mosquitto_sub -h localhost -t "rpi/broadcast" -v
   ```
4. Check firewall: `sudo ufw allow 1883/tcp`

### Dashboard Can't Control Devices
**Problem**: Clicking buttons doesn't work

**Solution:**
1. Check MQTT client status in dashboard (should show "Connected")
2. Verify devices registered: Check database or API endpoint:
   ```bash
   curl http://localhost:8080/api/iot/devices
   ```
3. Check ESP32 serial monitor - should see `[←] Message on: rpi/broadcast`
4. Verify device_id matches in firmware and database

### Motion Not Detected
**Problem**: ESP32-1 doesn't respond to motion

**Solution:**
1. Check PIR sensor wiring (GPIO 15)
2. PIR sensor needs 30-60 seconds warm-up time after power-on
3. Check if alarm is enabled (not disabled from dashboard)
4. Verify PIR sensor is working: Check serial monitor for motion messages
5. Adjust PIR sensitivity potentiometer on sensor

### RGB LED Not Responding
**Problem**: LED strip doesn't change

**Solution:**
1. Check LED strip wiring (Data pin to GPIO 15)
2. Check power supply (5V for NeoPixels)
3. Verify NUM_LEDS matches actual LED count
4. Test with serial monitor commands
5. Check if bulb is turned "on" in dashboard

## Advanced Features

### Automatic Alarm on Threat Detection

You can configure the IDS to automatically trigger the ESP32-1 alarm when threats are detected.

Edit `Core/loki/logger.py` and add:

```python
def log_alert(self, alert_type, ...):
    # ... existing logging ...

    # Auto-trigger IoT response for high-severity alerts
    if severity == "HIGH" or severity == "CRITICAL":
        self.trigger_iot_alarm()

def trigger_iot_alarm(self):
    try:
        import requests
        requests.post(
            "http://localhost:8080/api/iot/devices/esp32-1/alarm",
            json={"action": "enable"},
            timeout=1
        )
    except:
        pass  # Non-blocking
```

### Custom LED Colors

Modify `esp/Final-RGB.ino` to support color commands:

```cpp
void setLEDColorRGB(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

// In callback, add color_control command:
else if (strcmp(command, "color_control") == 0) {
  int r = doc["red"] | 255;
  int g = doc["green"] | 0;
  int b = doc["blue"] | 0;
  setLEDColorRGB(r, g, b);
}
```

## MQTT Command Reference

### Control ESP32-1 (Motion Sensor)

**Enable Alarm:**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-1","command":"alarm_control","action":"enable"}'
```

**Disable Alarm:**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-1","command":"alarm_control","action":"disable"}'
```

**Test Alarm:**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-1","command":"alarm_control","action":"test"}'
```

**Buzzer Beep (2 seconds):**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-1","command":"buzzer_control","action":"beep","duration":2000}'
```

**LED Control:**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-1","command":"led_control","action":"on"}'
```

### Control ESP32-2 (RGB LED)

**Turn On (Full Brightness):**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-2","command":"bulb_control","state":"on","brightness":255}'
```

**Turn Off:**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-2","command":"bulb_control","state":"off","brightness":0}'
```

**Dim (50% Brightness):**
```bash
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"device":"esp32-2","command":"bulb_control","state":"on","brightness":127}'
```

### Monitor Status

**Subscribe to ESP32-1 Status:**
```bash
mosquitto_sub -h localhost -t "esp32/sensor1/status" -v
```

**Subscribe to ESP32-2 Status:**
```bash
mosquitto_sub -h localhost -t "esp32/sensor2/status" -v
```

**Monitor All Topics:**
```bash
mosquitto_sub -h localhost -t "#" -v
```

## Required Libraries

### Arduino Libraries (Install via Library Manager)
1. **PubSubClient** by Nick O'Leary - MQTT client
2. **ArduinoJson** by Benoit Blanchon - JSON parsing
3. **Adafruit NeoPixel** - RGB LED control (ESP32-2 only)

### Python Libraries (Already in requirements.txt)
- `paho-mqtt>=2.0.0` - MQTT client for Raspberry Pi

## Security Considerations

1. **Change Default WiFi Credentials**: Update firmware before deployment
2. **MQTT Authentication**: Configure mosquitto with username/password
3. **Network Isolation**: Keep IoT devices on separate VLAN
4. **Firmware Updates**: Implement OTA (Over-The-Air) updates
5. **API Authentication**: Add authentication to dashboard (production)

## Performance

- **ESP32 Response Time**: < 100ms from dashboard command to device action
- **Motion Detection Latency**: < 500ms from motion to alarm trigger
- **MQTT Message Rate**: Max 10 messages/second per device (heartbeat + events)
- **Dashboard Updates**: Real-time via WebSocket (< 1 second latency)

## Support

For issues:
1. Check ESP32 serial monitor output (115200 baud)
2. Check Raspberry Pi API logs: `/tmp/loki_api.log`
3. Test MQTT manually with mosquitto_pub/sub
4. Verify network connectivity and firewall rules

---

**Your complete Loki IDS + IoT system is ready!** 🎉
