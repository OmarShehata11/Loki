# Testing IoT Devices - Step by Step Guide

## Problem: No Devices Showing in Web Interface

If you don't see any devices, follow these steps:

## Step 1: Register Devices in Database

**This is the most common issue!** Devices must be registered first.

```bash
cd /home/zaher/Loki-IDS/Web-Interface

# Activate virtual environment (if not already)
source venv/bin/activate

# Register devices
python3 setup_iot_devices.py
```

**Expected output:**
```
============================================================
    Setting up IoT Devices
============================================================
[✓] Registered ESP32-1 (Motion Sensor)
[✓] Registered ESP32-2 (RGB Controller)
[✓] IoT devices setup complete!
```

## Step 2: Verify Devices in Database

Check if devices are registered:

```bash
cd Web-Interface
sqlite3 loki_ids.db "SELECT device_id, name, device_type, enabled FROM iot_devices;"
```

**Expected output:**
```
esp32-1|ESP32 Motion Sensor & Buzzer|motion_sensor|1
esp32-2|ESP32 RGB Controller|rgb_controller|1
```

## Step 3: Start Web Server

```bash
cd Web-Interface
./start_web_server.sh
```

Or manually:
```bash
cd Web-Interface
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

## Step 4: Check MQTT Broker

The web interface needs MQTT broker to be running:

```bash
# Check if Mosquitto is running
sudo systemctl status mosquitto

# If not running, start it
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

## Step 5: Open Web Interface

1. Open browser: http://localhost:8080
2. Click **"IoT Control"** tab
3. Check MQTT status (should be green "Connected")

**If MQTT shows disconnected:**
- Click "Connect MQTT" button
- Or check broker IP in settings

## Step 6: Verify Devices Appear

You should now see:
- **ESP32 Motion Sensor & Buzzer** (ESP32-1)
- **ESP32 RGB Controller** (ESP32-2)

## Step 7: Test ESP32 Connections

### Test ESP32-1 (Motion Sensor)

1. **Upload firmware** to ESP32-1:
   - Open `esp/ESP32-1-Motion-Buzzer.ino` in Arduino IDE
   - Update WiFi SSID and password
   - Update MQTT broker IP
   - Upload to ESP32

2. **Check Serial Monitor** (115200 baud):
   ```
   WiFi connected
   IP address: 10.0.0.5
   MQTT Connected
   Subscribed to: rpi/broadcast
   ```

3. **Test in web interface:**
   - Click "Buzzer ON" → Should hear buzzer
   - Click "Buzzer OFF" → Buzzer stops
   - Click "Beep (1s)" → Short beep

### Test ESP32-2 (RGB Controller)

1. **Upload firmware** to ESP32-2:
   - Open `esp/ESP32-2-RGB.ino` in Arduino IDE
   - Update WiFi SSID and password
   - Update MQTT broker IP
   - Upload to ESP32

2. **Check Serial Monitor** (115200 baud):
   ```
   WiFi connected
   IP address: 10.0.0.6
   MQTT Connected
   Subscribed to: rpi/broadcast
   ```

3. **Test in web interface:**
   - Select color (e.g., red)
   - Adjust brightness
   - Select effect (e.g., "solid")
   - Click "Apply" → LED should change

## Troubleshooting

### Issue: Still No Devices Showing

**Solution 1: Re-register devices**
```bash
cd Web-Interface
python3 setup_iot_devices.py
```

**Solution 2: Check database directly**
```bash
sqlite3 Web-Interface/loki_ids.db "SELECT * FROM iot_devices;"
```

**Solution 3: Check API directly**
```bash
curl http://localhost:8080/api/iot/devices
```

Should return:
```json
{
  "devices": [
    {
      "id": 1,
      "device_id": "esp32-1",
      "name": "ESP32 Motion Sensor & Buzzer",
      ...
    },
    {
      "id": 2,
      "device_id": "esp32-2",
      "name": "ESP32 RGB Controller",
      ...
    }
  ]
}
```

### Issue: MQTT Not Connecting

**Check broker:**
```bash
sudo systemctl status mosquitto
sudo journalctl -u mosquitto -f
```

**Test MQTT manually:**
```bash
# Terminal 1: Subscribe
mosquitto_sub -h localhost -t "rpi/broadcast" -v

# Terminal 2: Publish
mosquitto_pub -h localhost -t "rpi/broadcast" -m '{"test": "message"}'
```

**Check broker IP:**
- If Raspberry Pi is access point, use its IP (check with `hostname -I`)
- Update in `api/iot/mqtt_client.py` if needed

### Issue: Commands Not Working

**Check MQTT messages:**
```bash
mosquitto_sub -h localhost -t "rpi/broadcast" -v
```

Then use web interface - you should see JSON commands appear.

**Check ESP32 Serial Monitor:**
- Should show "Message arrived on topic: rpi/broadcast"
- Should show "Processing command: ..."

**Verify device IDs match:**
- ESP32-1 code must have: `const char* DEVICE_ID = "esp32-1";`
- ESP32-2 code must have: `const char* DEVICE_ID = "esp32-2";`

### Issue: ESP32 Not Connecting to WiFi

**Check Serial Monitor:**
- Should show "Connecting to [SSID]"
- Should show "WiFi connected"
- Should show IP address

**Common fixes:**
- Verify SSID and password are correct
- Check WiFi is in range
- Verify Raspberry Pi access point is running

### Issue: ESP32 Not Connecting to MQTT

**Check Serial Monitor:**
- Should show "Attempting MQTT connection..."
- Should show "MQTT Connected"

**Common fixes:**
- Verify MQTT broker IP is correct
- Check broker is running: `sudo systemctl status mosquitto`
- Test broker: `mosquitto_pub -h <IP> -t test -m "hello"`

## Quick Test Checklist

- [ ] Devices registered in database (`setup_iot_devices.py`)
- [ ] Web server running
- [ ] MQTT broker running
- [ ] MQTT status shows "Connected" in web interface
- [ ] ESP32-1 connected to WiFi
- [ ] ESP32-1 connected to MQTT
- [ ] ESP32-2 connected to WiFi
- [ ] ESP32-2 connected to MQTT
- [ ] Devices appear in "IoT Control" tab
- [ ] Buzzer commands work
- [ ] RGB commands work

## Quick Commands Reference

```bash
# Register devices
cd Web-Interface && python3 setup_iot_devices.py

# Check devices in database
sqlite3 Web-Interface/loki_ids.db "SELECT * FROM iot_devices;"

# Start MQTT broker
sudo systemctl start mosquitto

# Test MQTT
mosquitto_sub -h localhost -t "rpi/broadcast" -v

# Check API
curl http://localhost:8080/api/iot/devices

# Start web server
cd Web-Interface && ./start_web_server.sh
```

## Still Having Issues?

1. **Check browser console** (F12) for JavaScript errors
2. **Check web server logs** for errors
3. **Check ESP32 Serial Monitor** for connection issues
4. **Verify all IP addresses** are correct
5. **Test MQTT manually** to isolate issues
