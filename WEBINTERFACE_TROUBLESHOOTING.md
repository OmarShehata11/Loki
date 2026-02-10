# Web Interface Troubleshooting Guide

## Quick Diagnostic Steps

### 1. Run the Diagnostic Script

```bash
cd /home/zaher/Loki-IDS
bash debug_webinterface.sh
```

This will check:
- If the server is running
- If port 8080 is listening
- Firewall status
- Network connectivity
- Your Pi's IP address

### 2. Common Issues & Solutions

#### Issue: "Cannot access from another computer"

**Problem**: You're trying to access from a laptop/desktop but using `http://localhost:8080`

**Solution**: Use your Raspberry Pi's IP address instead:

```bash
# On the Raspberry Pi, find your IP:
hostname -I

# Then access from your other computer:
# http://192.168.X.X:8080  (use the actual IP from above)
```

#### Issue: "Connection refused or timeout"

**Problem**: Firewall is blocking port 8080

**Solution**: Allow port 8080 through the firewall:

```bash
# If using UFW:
sudo ufw allow 8080/tcp
sudo ufw reload

# If using iptables directly:
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

#### Issue: "Server starts but immediately crashes"

**Problem**: Database or dependency issue

**Solution**: Check the logs and reinitialize database:

```bash
cd /home/zaher/Loki-IDS/Web-Interface

# Check if database exists
ls -lh loki_ids.db

# If missing or corrupt, reinitialize:
../loki_env/bin/python3 init_database.py

# Try starting again
bash start_web_server.sh
```

#### Issue: "Import errors when starting"

**Problem**: Virtual environment missing packages

**Solution**: Reinstall dependencies:

```bash
cd /home/zaher/Loki-IDS
bash setup_venv.sh
```

### 3. Manual Testing

Test if the server is accessible locally on the Pi:

```bash
# Test from the Raspberry Pi itself:
curl http://localhost:8080

# Should return HTML or "404" (both are OK - means server is working)

# Test API endpoint:
curl http://localhost:8080/api/health

# Test from another computer (replace with your Pi's IP):
curl http://192.168.X.X:8080
```

### 4. Check Server Logs

When you start the web interface, look for these messages:

**Good signs:**
```
[✓] All critical packages are installed
[*] Starting FastAPI server...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Bad signs:**
```
[!] Missing critical package: fastapi
ModuleNotFoundError: No module named 'fastapi'
ERROR:    Error loading ASGI app
```

### 5. Port Conflict Check

See if another process is using port 8080:

```bash
sudo lsof -i :8080
# or
sudo netstat -tulpn | grep 8080
```

If something else is using it, either:
- Stop that process
- Change the web interface port in [start_web_server.sh](start_web_server.sh) (line 89):
  ```bash
  "$VENV_PATH/bin/uvicorn" api.main:app --host 0.0.0.0 --port 8081 --reload
  ```

### 6. Full Restart Procedure

If all else fails, try a complete restart:

```bash
# 1. Stop any running web interface
pkill -f "uvicorn.*api.main"

# 2. Go to project root
cd /home/zaher/Loki-IDS

# 3. Recreate virtual environment
bash setup_venv.sh

# 4. Reinitialize database
cd Web-Interface
../loki_env/bin/python3 init_database.py

# 5. Start server
bash start_web_server.sh
```

## Access URLs

Once working, access these URLs:

| Purpose | URL (on Pi) | URL (from other computer) |
|---------|-------------|---------------------------|
| Dashboard | http://localhost:8080 | http://PI_IP:8080 |
| API Docs | http://localhost:8080/docs | http://PI_IP:8080/docs |
| Health Check | http://localhost:8080/api/health | http://PI_IP:8080/api/health |

Replace `PI_IP` with your actual Raspberry Pi IP address (find it with `hostname -I`).

## Browser-Specific Issues

### Chrome/Edge
- Try incognito mode
- Clear cache: Ctrl+Shift+Delete

### Firefox
- Try private window
- Clear cache for the site

### All Browsers
- Try: http://PI_IP:8080 (not https://)
- Disable any ad-blockers for this site

## Network Issues

### Both IDS and Web Interface on same Pi
✓ Should work fine - they're independent processes

### Accessing from same network
✓ Make sure your computer and Pi are on the same network

### Accessing from different network
✗ You'll need port forwarding or VPN (security risk!)

## Still Not Working?

Run the diagnostic script and share the output:

```bash
bash debug_webinterface.sh > webinterface_debug.txt
cat webinterface_debug.txt
```

Check for:
1. ✓ marks (good) vs ✗ marks (problems)
2. Error messages in red
3. The Pi's IP address shown
4. Whether port 8080 is listening