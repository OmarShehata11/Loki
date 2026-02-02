# ESP32 Debugging Guide

## Enhanced Logging

Both ESP32 firmware files now have enhanced logging to help debug MQTT command issues.

## What to Check in Serial Monitor

### When a Command is Sent from Web Interface:

**ESP32-1 (Motion/Buzzer) should show:**
```
[MQTT] >>> Message received!
[MQTT] Topic: rpi/broadcast
[MQTT] Data: {"device":"esp32-1","command":"buzzer_control","action":"on",...}
[MQTT] Device ID in message: esp32-1
[MQTT] Expected device ID: esp32-1
[MQTT] ✓ Device ID matches!
[MQTT] Processing command: buzzer_control
[Buzzer] Processing buzzer_control command
[Buzzer] Action received: on
[Buzzer] ✓ Turned ON (continuous)
```

**ESP32-2 (RGB) should show:**
```
[MQTT] >>> Message received!
[MQTT] Topic: rpi/broadcast
[MQTT] Data: {"device":"esp32-2","command":"rgb_control","color":"#FF0000",...}
[MQTT] Device ID in message: esp32-2
[MQTT] Expected device ID: esp32-2
[MQTT] ✓ Device ID matches!
[MQTT] Processing command: rgb_control
[RGB] Processing rgb_control command
[RGB] Color received: #FF0000
[RGB] ✓ Command received: Color=#FF0000 Brightness=255 Effect=solid
```

## Common Issues

### 1. "Message not for this device, ignoring"
**Problem:** Device ID mismatch
- Check that `DEVICE_ID` in ESP32 code matches the device ID in the web interface
- ESP32-1 should have `DEVICE_ID = "esp32-1"`
- ESP32-2 should have `DEVICE_ID = "esp32-2"`

### 2. "JSON parse error"
**Problem:** Malformed JSON or wrong ArduinoJson version
- Ensure you're using ArduinoJson v6.x (not v7.x)
- Check that the MQTT message format is correct

### 3. "No command field found"
**Problem:** MQTT message missing command field
- Check server-side MQTT client is sending correct format
- Verify message structure matches expected format

### 4. "Unknown command type"
**Problem:** Command name doesn't match
- ESP32-1 expects: `buzzer_control`, `alarm_control`
- ESP32-2 expects: `rgb_control`
- Check spelling and case sensitivity

### 5. No messages received at all
**Problem:** MQTT not connected or wrong topic
- Check MQTT connection status in Serial Monitor
- Verify ESP32 is subscribed to `rpi/broadcast`
- Check MQTT broker is running and accessible
- Verify IP address in ESP32 code matches broker IP

## Testing Steps

1. **Open Serial Monitor** (115200 baud)
2. **Click a button** in the web interface
3. **Check Serial Monitor** for the log messages above
4. **If no messages appear:**
   - Check MQTT connection status
   - Verify broker IP address
   - Check WiFi connection
5. **If messages appear but command fails:**
   - Check the specific error message
   - Verify device ID matches
   - Check command format

## Expected Behavior

### Buzzer Control (ESP32-1)
- **ON**: Buzzer turns on continuously
- **OFF**: Buzzer turns off
- **BEEP**: Buzzer beeps for specified duration

### Alarm Control (ESP32-1)
- **ENABLE**: Alarm will trigger on motion detection
- **DISABLE**: Alarm will not trigger
- **TEST**: Immediately plays alarm sound and flashes LED

### RGB Control (ESP32-2)
- **Solid**: Sets LED to specified color immediately
- **Fade**: Fades color in and out
- **Rainbow**: Cycles through rainbow colors
- **Blink**: Blinks the color on/off

## Serial Monitor Settings

- **Baud Rate**: 115200
- **Line Ending**: Both NL & CR (or just Newline)
- **Auto-scroll**: Enabled
