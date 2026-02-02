# ESP32 Firmware Requirements for Web Interface

## Overview

Your ESP32 firmware needs to be compatible with the MQTT command format sent by the web interface. This document outlines what your ESP32 code must handle.

## MQTT Topics

### Subscribe To:
- **`rpi/broadcast`** - Commands from web interface (both ESP32s)

### Publish To:
- **`esp32/sensor1`** - Motion detection events (ESP32-1 only)

## Command Format

All commands are sent as JSON to the `rpi/broadcast` topic. Your ESP32 must:

1. **Subscribe** to `rpi/broadcast`
2. **Parse JSON** messages
3. **Check** if `device` field matches your device ID
4. **Execute** the command

## ESP32-1 (Motion Sensor & Buzzer)

### Commands to Handle

#### 1. Buzzer Control
```json
{
  "device": "esp32-1",
  "command": "buzzer_control",
  "action": "on",        // or "off", "beep"
  "duration": 1000,      // milliseconds (only for "beep")
  "timestamp": "2024-01-01T12:00:00"
}
```

**Actions:**
- `"on"` - Turn buzzer ON continuously
- `"off"` - Turn buzzer OFF
- `"beep"` - Beep for `duration` milliseconds

#### 2. Alarm Control
```json
{
  "device": "esp32-1",
  "command": "alarm_control",
  "action": "enable",    // or "disable", "test"
  "timestamp": "2024-01-01T12:00:00"
}
```

**Actions:**
- `"enable"` - Enable alarm system
- `"disable"` - Disable alarm system
- `"test"` - Trigger test alarm

### Publish Motion Events

When motion is detected, publish to `esp32/sensor1`:
```json
{
  "motion_detected": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

## ESP32-2 (RGB LED Controller)

### Commands to Handle

#### RGB Control
```json
{
  "device": "esp32-2",
  "command": "rgb_control",
  "color": "#FF0000",     // Hex color code
  "brightness": 255,      // 0-255
  "effect": "solid",      // "solid", "fade", "rainbow", "blink"
  "timestamp": "2024-01-01T12:00:00"
}
```

**Effects:**
- `"solid"` - Static color
- `"fade"` - Smooth color transitions
- `"rainbow"` - Color cycling
- `"blink"` - Flashing effect

## Example ESP-IDF Code Structure

### ESP32-1 Example (Pseudocode)

```c
#include "mqtt_client.h"
#include "cJSON.h"

// MQTT callback
void mqtt_callback(char* topic, char* payload, int len) {
    // Parse JSON
    cJSON *json = cJSON_Parse(payload);
    
    // Check device ID
    cJSON *device = cJSON_GetObjectItem(json, "device");
    if (strcmp(device->valuestring, "esp32-1") != 0) {
        return; // Not for this device
    }
    
    // Get command
    cJSON *command = cJSON_GetObjectItem(json, "command");
    
    if (strcmp(command->valuestring, "buzzer_control") == 0) {
        cJSON *action = cJSON_GetObjectItem(json, "action");
        
        if (strcmp(action->valuestring, "on") == 0) {
            buzzer_on();
        } else if (strcmp(action->valuestring, "off") == 0) {
            buzzer_off();
        } else if (strcmp(action->valuestring, "beep") == 0) {
            cJSON *duration = cJSON_GetObjectItem(json, "duration");
            buzzer_beep(duration->valueint);
        }
    }
    else if (strcmp(command->valuestring, "alarm_control") == 0) {
        cJSON *action = cJSON_GetObjectItem(json, "action");
        
        if (strcmp(action->valuestring, "enable") == 0) {
            alarm_enable();
        } else if (strcmp(action->valuestring, "disable") == 0) {
            alarm_disable();
        } else if (strcmp(action->valuestring, "test") == 0) {
            alarm_test();
        }
    }
    
    cJSON_Delete(json);
}

// Publish motion event
void publish_motion(bool detected) {
    char payload[200];
    snprintf(payload, sizeof(payload),
        "{\"motion_detected\":%s,\"timestamp\":\"%s\"}",
        detected ? "true" : "false",
        get_timestamp()
    );
    mqtt_publish("esp32/sensor1", payload);
}
```

### ESP32-2 Example (Pseudocode)

```c
// MQTT callback
void mqtt_callback(char* topic, char* payload, int len) {
    cJSON *json = cJSON_Parse(payload);
    
    // Check device ID
    cJSON *device = cJSON_GetObjectItem(json, "device");
    if (strcmp(device->valuestring, "esp32-2") != 0) {
        return;
    }
    
    // Get command
    cJSON *command = cJSON_GetObjectItem(json, "command");
    
    if (strcmp(command->valuestring, "rgb_control") == 0) {
        // Parse color (hex string like "#FF0000")
        cJSON *color = cJSON_GetObjectItem(json, "color");
        cJSON *brightness = cJSON_GetObjectItem(json, "brightness");
        cJSON *effect = cJSON_GetObjectItem(json, "effect");
        
        // Convert hex color to RGB
        uint8_t r, g, b;
        hex_to_rgb(color->valuestring, &r, &g, &b);
        
        // Apply to LED strip
        rgb_set_color(r, g, b);
        rgb_set_brightness(brightness->valueint);
        rgb_set_effect(effect->valuestring);
    }
    
    cJSON_Delete(json);
}
```

## Required Changes to Your ESP32 Code

### If Your Code Already Uses MQTT:

1. **Subscribe to `rpi/broadcast`** (if not already)
2. **Parse JSON** commands (use cJSON library)
3. **Check `device` field** matches your device ID
4. **Handle new commands:**
   - ESP32-1: `buzzer_control`, `alarm_control`
   - ESP32-2: `rgb_control`
5. **Publish motion events** to `esp32/sensor1` (ESP32-1 only)

### If Your Code Uses Different Format:

You have two options:

#### Option 1: Update ESP32 Code (Recommended)
- Modify your ESP32 firmware to match the web interface format
- This ensures full compatibility

#### Option 2: Add Translation Layer
- Keep your ESP32 code as-is
- Add a translation layer in the web interface to convert commands
- More complex, not recommended

## Testing

### Test Buzzer Control:
1. Open web interface
2. Click "Buzzer ON" - ESP32-1 buzzer should turn on
3. Click "Buzzer OFF" - Buzzer should turn off
4. Click "Beep (1s)" - Should hear 1 second beep

### Test RGB Control:
1. Select color in color picker
2. Adjust brightness
3. Select effect
4. Click "Apply" - ESP32-2 LED should update

### Test Motion Sensor:
1. Trigger motion sensor
2. ESP32-1 should publish to `esp32/sensor1`
3. Web interface should show "Motion Detected: YES"

## MQTT Broker Connection

Your ESP32s should connect to:
- **Host**: Raspberry Pi IP (usually `10.0.0.1` or the AP's IP)
- **Port**: `1883`
- **Client ID**: Unique for each device (e.g., "esp32-1", "esp32-2")

## Summary

**Yes, you likely need to update your ESP32 code** to:
1. Subscribe to `rpi/broadcast` topic
2. Parse JSON commands with the exact format shown above
3. Handle the specific command types (`buzzer_control`, `alarm_control`, `rgb_control`)
4. Check the `device` field to filter commands

The web interface sends commands in a specific JSON format, so your ESP32 firmware must be able to parse and respond to that format.
