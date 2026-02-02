# MQTT Troubleshooting Guide

This guide helps you resolve MQTT connection issues.

## Common Issues

### Issue: MQTT Shows "Disconnected"

**Symptoms:**
- Web interface shows yellow/red MQTT status
- Cannot send commands to ESP32 devices
- Terminal shows "Disconnected from MQTT broker"

**Solutions:**

1. **Check MQTT Broker is Running**
   ```bash
   sudo systemctl status mosquitto
   ```
   If not running:
   ```bash
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```

2. **Find Raspberry Pi IP**
   ```bash
   hostname -I
   ```

3. **Connect Manually**
   - Click "Connect MQTT" button in web interface
   - Enter Raspberry Pi IP when prompted

4. **Check Broker Configuration**
   ```bash
   sudo cat /etc/mosquitto/mosquitto.conf
   ```
   Should have:
   ```
   listener 1883 0.0.0.0
   allow_anonymous true
   ```

### Issue: Return Code 7 (Network Error)

**Symptoms:**
- Terminal shows: "Disconnected from MQTT broker. Return code: 7"
- Connection established but immediately lost

**What it means:**
Return code 7 = Network error - connection lost or timeout

**Solutions:**

1. **Check Network Connectivity**
   ```bash
   ping YOUR_RPI_IP
   telnet YOUR_RPI_IP 1883
   ```

2. **Check Firewall**
   ```bash
   sudo ufw allow 1883/tcp
   sudo ufw reload
   ```

3. **Check Broker Logs**
   ```bash
   sudo journalctl -u mosquitto -f
   ```

4. **Verify Broker is Listening**
   ```bash
   sudo netstat -tlnp | grep 1883
   ```
   Should show: `0.0.0.0:1883` (not just `127.0.0.1:1883`)

**Note:** The web interface now has automatic reconnection. It will retry every 10 seconds if disconnected.

### Issue: Connection Refused

**Symptoms:**
- Cannot connect to broker
- Connection refused errors

**Solutions:**

1. **Broker not running**
   ```bash
   sudo systemctl start mosquitto
   ```

2. **Broker only listening on localhost**
   - Edit `/etc/mosquitto/mosquitto.conf`
   - Add: `listener 1883 0.0.0.0`
   - Restart: `sudo systemctl restart mosquitto`

3. **Firewall blocking**
   ```bash
   sudo ufw allow 1883/tcp
   ```

### Issue: Connection Timeout

**Symptoms:**
- Connection attempts timeout
- No response from broker

**Solutions:**

1. **Wrong IP address**
   - Verify Raspberry Pi IP: `hostname -I`
   - Update connection with correct IP

2. **Network connectivity**
   ```bash
   ping YOUR_RPI_IP
   ```

3. **Port blocked**
   ```bash
   sudo ufw status
   sudo ufw allow 1883/tcp
   ```

## Testing MQTT Connection

### Test 1: Manual MQTT Test

**Terminal 1 - Subscribe:**
```bash
mosquitto_sub -h YOUR_RPI_IP -t "test" -v
```

**Terminal 2 - Publish:**
```bash
mosquitto_pub -h YOUR_RPI_IP -t "test" -m "hello"
```

If this works, MQTT broker is fine. If not, check broker configuration.

### Test 2: Check Web Interface Status

```bash
curl http://localhost:8080/api/iot/mqtt/status
```

Should return:
```json
{
  "available": true,
  "connected": true,
  "broker_host": "YOUR_RPI_IP",
  "broker_port": 1883
}
```

### Test 3: Monitor MQTT Traffic

```bash
# Monitor all commands
mosquitto_sub -h YOUR_RPI_IP -t "rpi/broadcast" -v

# Monitor motion events
mosquitto_sub -h YOUR_RPI_IP -t "esp32/sensor1" -v
```

## Broker Configuration

### Basic Configuration

Edit `/etc/mosquitto/mosquitto.conf`:

```
# Listen on all interfaces
listener 1883 0.0.0.0

# Allow anonymous connections (for testing)
allow_anonymous true

# Persistent client expiration
persistent_client_expiration 1h

# No connection limit
max_connections -1
```

Restart:
```bash
sudo systemctl restart mosquitto
```

### Security (Production)

For production, add authentication:
```
allow_anonymous false
password_file /etc/mosquitto/passwd
```

## Auto-Reconnection

The web interface now includes automatic reconnection:

- Checks connection every 10 seconds
- Automatically reconnects if disconnected
- Logs reconnection attempts

**Log messages:**
- `MQTT disconnected, attempting to reconnect...`
- `Successfully reconnected to MQTT broker`

## Quick Reference

```bash
# Check broker status
sudo systemctl status mosquitto

# Start broker
sudo systemctl start mosquitto

# Check IP address
hostname -I

# Test connection
mosquitto_pub -h YOUR_RPI_IP -t test -m "hello"
mosquitto_sub -h YOUR_RPI_IP -t test -v

# Check port
sudo netstat -tlnp | grep 1883

# View logs
sudo journalctl -u mosquitto -f

# Allow firewall
sudo ufw allow 1883/tcp
```

## Still Having Issues?

1. Check broker logs: `sudo journalctl -u mosquitto -n 50`
2. Check web server logs for MQTT errors
3. Test with mosquitto clients to isolate Python client issues
4. Verify network path between web server and Raspberry Pi
5. Check broker connection limits in configuration
