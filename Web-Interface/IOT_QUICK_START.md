# IoT Control - Quick Start Guide

## What Was Built

A complete IoT device control system integrated into the Loki IDS web interface that allows you to:

1. **Control RGB LED Strips** (ESP32-2)
   - Color picker
   - Brightness control (0-255)
   - Effects: Solid, Fade, Rainbow, Blink

2. **Monitor & Control Motion Sensors** (ESP32-1)
   - View motion detection status
   - Enable/Disable alarm
   - Test alarm functionality

3. **MQTT Integration**
   - Automatic connection to broker at `10.0.0.1:1883`
   - Real-time device state monitoring
   - Command publishing

## Quick Setup (3 Steps)

### Step 1: Install Dependencies
```bash
cd Web-Interface
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Register Devices
```bash
venv/bin/python3 setup_iot_devices.py
```

### Step 3: Start Server
```bash
./start_web_server.sh
```

## Using the Interface

1. Open http://localhost:8080
2. Click **"IoT Control"** tab
3. Check MQTT status (should show "Connected" if broker is running)
4. Control your devices!

## MQTT Broker Setup

If you don't have MQTT broker running:

```bash
# Install Mosquitto
sudo apt-get install mosquitto mosquitto-clients

# Start service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Test connection
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

## File Structure

```
Web-Interface/
├── api/
│   ├── iot/
│   │   ├── __init__.py
│   │   └── mqtt_client.py          # MQTT client wrapper
│   ├── routes/
│   │   └── iot.py                  # IoT API endpoints
│   └── models/
│       └── database.py            # IoT device models added
├── static/
│   ├── index.html                 # IoT tab added
│   └── js/
│       └── app.js                 # IoT control functions
├── setup_iot_devices.py          # Device registration script
├── IOT_SETUP.md                  # Detailed documentation
└── requirements.txt              # paho-mqtt added
```

## API Endpoints

- `GET /api/iot/devices` - List all devices
- `GET /api/iot/devices/{id}/state` - Get device state
- `POST /api/iot/devices/{id}/rgb` - Control RGB LED
- `POST /api/iot/devices/{id}/alarm` - Control alarm
- `GET /api/iot/mqtt/status` - Check MQTT connection
- `POST /api/iot/mqtt/connect` - Connect to MQTT broker

## Troubleshooting

**MQTT Not Connecting?**
- Check broker is running: `sudo systemctl status mosquitto`
- Verify IP address (default: 10.0.0.1)
- Check firewall: `sudo ufw allow 1883/tcp`

**Devices Not Showing?**
- Run: `python3 setup_iot_devices.py`
- Check database: `sqlite3 loki_ids.db "SELECT * FROM iot_devices;"`

**Commands Not Working?**
- Verify MQTT status shows "Connected"
- Check ESP32 devices are connected to WiFi
- Verify ESP32s are subscribed to `rpi/broadcast`

## Next Steps

- Customize device IDs and types
- Add more ESP32 devices
- Integrate with IDS alerts (e.g., flash RGB on attack detection)
- Create automation rules

For detailed documentation, see [IOT_SETUP.md](IOT_SETUP.md)
