#!/bin/bash
# Debug script for Web Interface connectivity issues

echo "======================================================"
echo "    Loki IDS Web Interface - Diagnostics"
echo "======================================================"
echo ""

# Check if server is running
echo "[1] Checking if server is running..."
if pgrep -f "uvicorn.*api.main:app" > /dev/null; then
    echo "✓ Web server process is running"
    echo "  PID(s): $(pgrep -f 'uvicorn.*api.main:app' | tr '\n' ' ')"
else
    echo "✗ Web server is NOT running"
    echo "  Start it with: cd Web-Interface && bash start_web_server.sh"
fi
echo ""

# Check if port 8080 is listening
echo "[2] Checking if port 8080 is listening..."
if ss -tulpn 2>/dev/null | grep -q ":8080"; then
    echo "✓ Port 8080 is listening"
    ss -tulpn 2>/dev/null | grep ":8080"
elif netstat -tuln 2>/dev/null | grep -q ":8080"; then
    echo "✓ Port 8080 is listening"
    netstat -tuln 2>/dev/null | grep ":8080"
else
    echo "✗ Port 8080 is NOT listening"
    echo "  The server might not have started properly"
fi
echo ""

# Check local connectivity
echo "[3] Testing local connectivity (localhost:8080)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 > /tmp/curl_result.txt 2>&1; then
    HTTP_CODE=$(cat /tmp/curl_result.txt)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        echo "✓ Server is responding locally (HTTP $HTTP_CODE)"
    else
        echo "⚠ Server responded with HTTP $HTTP_CODE"
    fi
else
    echo "✗ Cannot connect to localhost:8080"
    echo "  Server might not be running or crashed"
fi
echo ""

# Get Pi's IP address
echo "[4] Network information..."
echo "Raspberry Pi IP addresses:"
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v "127.0.0.1"
echo ""
PI_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v "127.0.0.1" | head -n1)

if [ -n "$PI_IP" ]; then
    echo "Primary IP: $PI_IP"
    echo "Access the dashboard at: http://$PI_IP:8080"
else
    echo "⚠ Could not determine IP address"
fi
echo ""

# Check firewall
echo "[5] Checking firewall status..."
if command -v ufw &> /dev/null; then
    if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
        echo "✓ UFW firewall is active"
        echo "Checking port 8080 rules:"
        sudo ufw status | grep 8080 || echo "  ⚠ Port 8080 is NOT allowed in UFW"
        echo ""
        echo "To allow port 8080:"
        echo "  sudo ufw allow 8080/tcp"
    else
        echo "✓ UFW firewall is inactive"
    fi
else
    echo "✓ UFW not installed (firewall likely not blocking)"
fi
echo ""

# Check iptables
echo "[6] Checking iptables rules for port 8080..."
if sudo iptables -L INPUT -n 2>/dev/null | grep -q "8080"; then
    echo "Found iptables rules for port 8080:"
    sudo iptables -L INPUT -n | grep "8080"
else
    echo "✓ No specific iptables rules blocking port 8080"
fi
echo ""

# Check if accessing from remote
echo "[7] Access instructions..."
echo "─────────────────────────────────────────────────────"
echo "If accessing from the Raspberry Pi itself:"
echo "  http://localhost:8080"
echo ""
echo "If accessing from another computer on the same network:"
echo "  http://$PI_IP:8080"
echo ""
echo "If you still can't access it:"
echo "  1. Check if firewall is blocking: sudo ufw allow 8080/tcp"
echo "  2. Check server logs in the terminal where you started it"
echo "  3. Try: curl http://localhost:8080 (on the Pi)"
echo "─────────────────────────────────────────────────────"
echo ""

# Test API endpoint
echo "[8] Testing API endpoints..."
if curl -s http://localhost:8080/docs >/dev/null 2>&1; then
    echo "✓ API docs accessible at: http://localhost:8080/docs"
else
    echo "✗ API docs not accessible"
fi

if curl -s http://localhost:8080/api/health >/dev/null 2>&1; then
    echo "✓ Health check endpoint working"
else
    echo "⚠ Health check endpoint not responding"
fi
echo ""

echo "======================================================"
echo "Diagnostics complete!"
echo "======================================================"