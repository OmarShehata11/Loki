# ESP32 Firmware for Loki IDS IoT Control

This directory contains the updated ESP32 firmware files compatible with the Loki IDS web interface.

## Files

- **ESP32-1-Motion-Buzzer.ino** - Motion sensor with buzzer and alarm control
- **ESP32-2-RGB.ino** - RGB LED strip controller

## Required Libraries

Install these libraries via Arduino IDE Library Manager:

1. **PubSubClient** by Nick O'Leary
   - Tools → Manage Libraries → Search "PubSubClient"

2. **ArduinoJson** by Benoit Blanchon (version 6.x)
   - Tools → Manage Libraries → Search "ArduinoJson"
   - **Important**: Use version 6.x, not version 7.x

3. **Adafruit NeoPixel** by Adafruit (for ESP32-2 only)
   - Tools → Manage Libraries → Search "Adafruit NeoPixel"

## Configuration

Before uploading, update these settings in both files:

```cpp
const char* WIFI_SSID = "Mikro";  // Your WiFi SSID
const char* WIFI_PASS = "123456789";  // Your WiFi password
const char* MQTT_BROKER_IP = "172.16.10.252";  // Raspberry Pi IP address
```

**Important**: 
- If Raspberry Pi is the access point, use its IP address (usually `10.0.0.1` or check with `hostname -I`)
- If MQTT broker is on the same device, you can use `127.0.0.1` or `localhost` (but ESP32 needs the actual IP)

## Hardware Connections

### ESP32-1 (Motion Sensor & Buzzer)
- **PIR Sensor**: GPIO 15
- **Buzzer**: GPIO 3
- **LED Indicator**: GPIO 2 (built-in LED)

### ESP32-2 (RGB Controller)
- **NeoPixel Strip**: GPIO 15
- **Number of LEDs**: 4 (change `NUM_LEDS` if different)

## Features

### ESP32-1 Features
- ✅ Motion detection via PIR sensor
- ✅ Buzzer control (ON/OFF/Beep)
- ✅ Alarm system control (Enable/Disable/Test)
- ✅ Publishes motion events to `esp32/sensor1`
- ✅ Subscribes to `rpi/broadcast` for commands

### ESP32-2 Features
- ✅ RGB color control (hex color codes)
- ✅ Brightness control (0-255)
- ✅ Multiple effects:
  - **Solid**: Static color
  - **Fade**: Smooth color transitions
  - **Rainbow**: Color cycling
  - **Blink**: Flashing effect
- ✅ Subscribes to `rpi/broadcast` for commands

## MQTT Topics

### Subscribed (Both ESP32s)
- `rpi/broadcast` - Commands from web interface

### Published (ESP32-1 only)
- `esp32/sensor1` - Motion detection events

## Command Format

The web interface sends JSON commands like:

**Buzzer Control:**
```json
{
  "device": "esp32-1",
  "command": "buzzer_control",
  "action": "on",  // or "off", "beep"
  "duration": 1000  // for beep (milliseconds)
}
```

**Alarm Control:**
```json
{
  "device": "esp32-1",
  "command": "alarm_control",
  "action": "enable"  // or "disable", "test"
}
```

**RGB Control:**
```json
{
  "device": "esp32-2",
  "command": "rgb_control",
  "color": "#FF0000",
  "brightness": 255,
  "effect": "solid"  // or "fade", "rainbow", "blink"
}
```

## Upload Instructions

1. Open Arduino IDE
2. Select board: **Tools → Board → ESP32 Dev Module**
3. Select port: **Tools → Port → /dev/ttyUSB0** (or your port)
4. Install required libraries (see above)
5. Open the appropriate `.ino` file
6. Update WiFi and MQTT settings
7. Click **Upload**

## Testing

After uploading:

1. Open Serial Monitor (115200 baud)
2. You should see:
   - WiFi connection status
   - MQTT connection status
   - "Subscribed to: rpi/broadcast"
3. Test via web interface:
   - Open http://localhost:8080
   - Go to "IoT Control" tab
   - Send commands and verify ESP32 responds

## Troubleshooting

### ESP32 won't connect to WiFi
- Check SSID and password are correct
- Verify WiFi is in range
- Check Serial Monitor for error messages

### ESP32 won't connect to MQTT
- Verify MQTT broker IP is correct
- Check MQTT broker is running: `sudo systemctl status mosquitto`
- Test MQTT manually: `mosquitto_pub -h <IP> -t test -m "hello"`

### Commands not working
- Check Serial Monitor for JSON parse errors
- Verify device ID matches (`esp32-1` or `esp32-2`)
- Check MQTT subscription: `mosquitto_sub -h <IP> -t "rpi/broadcast" -v`

### RGB not responding
- Verify NeoPixel library is installed
- Check GPIO pin connection
- Verify number of LEDs matches `NUM_LEDS`

### Buzzer not working
- Check GPIO pin connection
- Test buzzer directly (bypass code)
- Verify buzzer is active (not passive)

## Serial Monitor Output

### ESP32-1 Expected Output:
```
========================================
ESP32-1: Motion Sensor & Buzzer
========================================
PIR Motion Sensor System Ready
Waiting for motion...
Connecting to Mikro
WiFi connected
IP address: 10.0.0.5
Attempting MQTT connection...
MQTT Connected
Subscribed to: rpi/broadcast
MOTION DETECTED!
Published motion event: {"motion_detected":true,"timestamp":12345}
```

### ESP32-2 Expected Output:
```
========================================
ESP32-2: RGB LED Controller
========================================
NeoPixel strip initialized
Connecting to Mikro
WiFi connected
IP address: 10.0.0.6
Attempting MQTT connection...
MQTT Connected
Subscribed to: rpi/broadcast
Message arrived on topic: rpi/broadcast | Data: {"device":"esp32-2",...}
Processing command: rgb_control
RGB set to: R=255 G=0 B=0 Brightness=255
```

## Notes

- Both ESP32s must be on the same WiFi network as the Raspberry Pi
- Device IDs (`esp32-1` and `esp32-2`) must match the web interface
- JSON parsing uses ArduinoJson v6.x (not v7.x)
- Motion events are published every 4 seconds while motion is detected
- Effects run continuously until a new command is received
