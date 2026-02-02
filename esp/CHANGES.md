# ESP32 Firmware Changes Summary

This document details all changes made to the ESP32 firmware to make it compatible with the Loki IDS web interface.

## Overview

Both ESP32 firmware files were updated to:
1. Parse JSON commands from the web interface
2. Handle specific command types (buzzer, alarm, RGB)
3. Publish motion events in JSON format
4. Filter commands by device ID

---

## ESP32-1 (Motion Sensor & Buzzer) Changes

### File: `full-code.ino` → `ESP32-1-Motion-Buzzer.ino`

### 1. **Added ArduinoJson Library**
```cpp
// NEW
#include <ArduinoJson.h>
```
**Why**: Needed to parse JSON commands from web interface

### 2. **Added Device ID Constant**
```cpp
// NEW
const char* DEVICE_ID = "esp32-1";
```
**Why**: Filter commands meant for this specific device

### 3. **Added State Variables**
```cpp
// NEW
bool alarmEnabled = false;
bool buzzerState = false;
unsigned long buzzerBeepEndTime = 0;
bool motionDetected = false;
```
**Why**: Track buzzer and alarm states for command handling

### 4. **Added Buzzer Control Functions**
```cpp
// NEW
void beepBuzzer(unsigned long duration) {
  buzzerState = true;
  buzzerBeepEndTime = millis() + duration;
  // ...
}
```
**Why**: Handle beep commands with specific durations

### 5. **Completely Rewrote MQTT Callback**
**OLD:**
```cpp
void callback(char* topic, byte* message, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)message[i];
  
  if (String(topic) == "rpi/broadcast") {
    if (msg == "10") {
      Serial.println("Action received → Blink LED or something");
    }
  }
}
```

**NEW:**
```cpp
void callback(char* topic, byte* message, unsigned int length) {
  // Parse JSON
  StaticJsonDocument<512> doc;
  deserializeJson(doc, msg);
  
  // Check device ID
  if (strcmp(device, DEVICE_ID) != 0) return;
  
  // Handle buzzer_control command
  if (strcmp(command, "buzzer_control") == 0) {
    // Handle "on", "off", "beep" actions
  }
  
  // Handle alarm_control command
  if (strcmp(command, "alarm_control") == 0) {
    // Handle "enable", "disable", "test" actions
  }
}
```
**Why**: Parse JSON commands and handle buzzer/alarm control

### 6. **Added Motion Event Publishing**
```cpp
// NEW
void publishMotionEvent(bool detected) {
  StaticJsonDocument<200> doc;
  doc["motion_detected"] = detected;
  doc["timestamp"] = millis();
  
  char buffer[256];
  serializeJson(doc, buffer);
  client.publish("esp32/sensor1", buffer);
}
```
**Why**: Publish motion events in JSON format for web interface

### 7. **Updated Main Loop**
**OLD:**
```cpp
void loop() {
  // Simple PIR reading and alarm activation
  pirState = digitalRead(pirPin);
  if (pirState == HIGH) {
    soundAlarm();
  }
}
```

**NEW:**
```cpp
void loop() {
  // Handle buzzer beep timing
  if (buzzerState && buzzerBeepEndTime > 0) {
    // Manage beep duration
  }
  
  // Detect motion state changes
  if (pirState == HIGH && lastPirState == LOW) {
    publishMotionEvent(true);  // NEW: Publish to MQTT
    if (alarmEnabled) {  // NEW: Check if alarm is enabled
      soundAlarm();
    }
  }
  
  // Publish motion status periodically
  if (motionDetected && client.connected()) {
    if (millis() - lastMotionPublish > 4000) {
      publishMotionEvent(true);
    }
  }
}
```
**Why**: 
- Handle buzzer beep timing
- Publish motion events to MQTT
- Respect alarm enable/disable state

### 8. **Added MQTT Callback Registration**
```cpp
// NEW
client.setCallback(callback);
```
**Why**: Process incoming MQTT commands

---

## ESP32-2 (RGB Controller) Changes

### File: `Final-RGB.ino` → `ESP32-2-RGB.ino`

### 1. **Added ArduinoJson Library**
```cpp
// NEW
#include <ArduinoJson.h>
```
**Why**: Parse JSON RGB commands from web interface

### 2. **Added Device ID Constant**
```cpp
// NEW
const char* DEVICE_ID = "esp32-2";
```
**Why**: Filter commands meant for this device

### 3. **Added RGB State Variables**
```cpp
// NEW
uint8_t currentR = 0;
uint8_t currentG = 0;
uint8_t currentB = 0;
uint8_t currentBrightness = 255;
String currentEffect = "solid";
```
**Why**: Store current RGB state and effect

### 4. **Added Effect Animation Variables**
```cpp
// NEW
unsigned long lastEffectUpdate = 0;
unsigned long effectStartTime = 0;
int rainbowHue = 0;
bool blinkState = false;
unsigned long lastBlinkTime = 0;
```
**Why**: Control effect animations (fade, rainbow, blink)

### 5. **Added Hex Color Conversion**
```cpp
// NEW
bool hexToRgb(String hex, uint8_t& r, uint8_t& g, uint8_t& b) {
  // Convert "#FF0000" to RGB values
  r = strtol(hex.substring(0, 2).c_str(), NULL, 16);
  g = strtol(hex.substring(2, 4).c_str(), NULL, 16);
  b = strtol(hex.substring(4, 6).c_str(), NULL, 16);
  return true;
}
```
**Why**: Convert web interface hex colors (like "#FF0000") to RGB values

### 6. **Added RGB Color Setting Function**
```cpp
// NEW
void setRGBColor(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness) {
  // Apply brightness and set all LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}
```
**Why**: Centralized function to set RGB color with brightness

### 7. **Added Effect Animation System**
```cpp
// NEW
void updateEffect() {
  if (currentEffect == "solid") {
    // Static color
  }
  else if (currentEffect == "fade") {
    // Smooth fade animation
  }
  else if (currentEffect == "rainbow") {
    // Rainbow color cycling
  }
  else if (currentEffect == "blink") {
    // Blinking effect
  }
}
```
**Why**: Implement all web interface effects (solid, fade, rainbow, blink)

### 8. **Completely Rewrote MQTT Callback**
**OLD:**
```cpp
void callback(char* topic, byte* message, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)message[i];
  
  if (String(topic) == "rpi/broadcast") {
    if (msg == "10") {
      Serial.println("Action received → Blink LED or something");
    }
  }
}
```

**NEW:**
```cpp
void callback(char* topic, byte* message, unsigned int length) {
  // Parse JSON
  StaticJsonDocument<512> doc;
  deserializeJson(doc, msg);
  
  // Check device ID
  if (strcmp(device, DEVICE_ID) != 0) return;
  
  // Handle rgb_control command
  if (strcmp(command, "rgb_control") == 0) {
    // Extract color, brightness, effect
    const char* colorStr = doc["color"];  // "#FF0000"
    uint8_t brightness = doc["brightness"];  // 0-255
    const char* effectStr = doc["effect"];  // "solid", "fade", etc.
    
    // Convert hex to RGB and apply
    hexToRgb(colorStr, r, g, b);
    setRGBColor(r, g, b, brightness);
  }
}
```
**Why**: Parse JSON RGB commands and apply them to LEDs

### 9. **Removed Old Animation Loop**
**OLD:**
```cpp
void loop() {
  // Fixed animation cycling through colors
  static int colorIndex = 0;
  if (millis() - lastColorChange > 500) {
    for (int j = 0; j < NUM_LEDS; j++) {
      strip.setPixelColor(j, colors[colorIndex]);
    }
    colorIndex = (colorIndex + 1) % 5;
  }
}
```

**NEW:**
```cpp
void loop() {
  // Update effect animation (if not solid)
  updateEffect();
}
```
**Why**: Replace fixed animation with command-driven effects

### 10. **Removed Old Publish Logic**
**OLD:**
```cpp
// Publish every 4 seconds
if (millis() - lastMsg > 4000) {
  client.publish("esp32/sensor1", "88");
}
```

**NEW:**
```cpp
// Removed - ESP32-2 doesn't publish sensor data
```
**Why**: ESP32-2 is a controller, not a sensor

### 11. **Added MQTT Callback Registration**
```cpp
// NEW
client.setCallback(callback);
```
**Why**: Process incoming RGB commands

---

## Key Differences Summary

### ESP32-1 Changes:
| Feature | Before | After |
|---------|--------|-------|
| Command Format | Simple string ("10") | JSON with device/command/action |
| Buzzer Control | None | ON/OFF/Beep with duration |
| Alarm Control | Auto on motion | Enable/Disable/Test via MQTT |
| Motion Publishing | None | JSON to `esp32/sensor1` |
| Device Filtering | None | Checks `device` field |

### ESP32-2 Changes:
| Feature | Before | After |
|---------|--------|-------|
| Command Format | Simple string ("10") | JSON with color/brightness/effect |
| Color Control | Fixed animation | Web interface controlled |
| Effects | None | Solid/Fade/Rainbow/Blink |
| Brightness | Fixed (100) | 0-255 controllable |
| Hex Colors | None | Converts "#FF0000" to RGB |

---

## New Dependencies

Both files now require:
1. **ArduinoJson v6.x** - For JSON parsing
2. **PubSubClient** - Already used, but now with JSON messages

---

## Command Format Compatibility

### Web Interface Sends:
```json
{
  "device": "esp32-1",
  "command": "buzzer_control",
  "action": "beep",
  "duration": 1000
}
```

### ESP32 Now Handles:
- ✅ Parses JSON
- ✅ Checks device ID
- ✅ Executes command
- ✅ Handles all action types

---

## Testing Checklist

After uploading new firmware:

- [ ] ESP32-1 connects to WiFi
- [ ] ESP32-1 connects to MQTT
- [ ] ESP32-1 responds to buzzer commands
- [ ] ESP32-1 responds to alarm commands
- [ ] ESP32-1 publishes motion events
- [ ] ESP32-2 connects to WiFi
- [ ] ESP32-2 connects to MQTT
- [ ] ESP32-2 responds to RGB color commands
- [ ] ESP32-2 responds to brightness changes
- [ ] ESP32-2 shows all effects (solid/fade/rainbow/blink)

---

## Migration Notes

**Breaking Changes:**
- Old simple string commands (`"10"`) no longer work
- Must use JSON format from web interface
- Device IDs must match (`esp32-1`, `esp32-2`)

**Backward Compatibility:**
- None - this is a complete rewrite for web interface compatibility

**Upgrade Path:**
1. Install ArduinoJson library
2. Update WiFi/MQTT settings
3. Upload new firmware
4. Test via web interface
