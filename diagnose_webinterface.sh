#!/bin/bash
# Comprehensive Web Interface Diagnostic Script

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================================"
echo "  Loki IDS Web Interface - Full Diagnostics"
echo "======================================================${NC}"
echo ""

# 1. Check if server is running
echo -e "${YELLOW}[1] Checking server process...${NC}"
if pgrep -f "uvicorn.*api.main:app" > /dev/null; then
    echo -e "${GREEN}✓ Server is running${NC}"
    echo "  PID: $(pgrep -f 'uvicorn.*api.main:app')"
else
    echo -e "${RED}✗ Server is NOT running${NC}"
    echo "  Start with: cd Web-Interface && bash start_web_server.sh"
    exit 1
fi
echo ""

# 2. Test API endpoints
echo -e "${YELLOW}[2] Testing API endpoints...${NC}"

test_endpoint() {
    local endpoint=$1
    local timeout=3

    response=$(curl -s -w "\n%{http_code}" --max-time $timeout "http://localhost:8080$endpoint" 2>&1)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} $endpoint (200 OK)"
        return 0
    elif [ -z "$http_code" ] || [ "$http_code" = "000" ]; then
        echo -e "${RED}✗${NC} $endpoint (TIMEOUT/NO RESPONSE)"
        return 1
    else
        echo -e "${YELLOW}⚠${NC} $endpoint (HTTP $http_code)"
        echo "   Response: ${body:0:80}"
        return 1
    fi
}

# Critical endpoints
test_endpoint "/api/stats"
STATS_OK=$?
test_endpoint "/api/system/status"
STATUS_OK=$?
test_endpoint "/api/alerts?page=1&page_size=5"
ALERTS_OK=$?
test_endpoint "/api/signatures?page=1&page_size=5"
SIGS_OK=$?
test_endpoint "/api/system/health"
HEALTH_OK=$?
echo ""

# 3. Check database
echo -e "${YELLOW}[3] Checking database...${NC}"
if [ -f "Web-Interface/loki_ids.db" ]; then
    echo -e "${GREEN}✓${NC} Database file exists"
    echo "   Size: $(du -h Web-Interface/loki_ids.db | cut -f1)"

    # Check if database is accessible
    if sqlite3 Web-Interface/loki_ids.db "SELECT COUNT(*) FROM alerts;" 2>/dev/null | grep -q "[0-9]"; then
        ALERT_COUNT=$(sqlite3 Web-Interface/loki_ids.db "SELECT COUNT(*) FROM alerts;" 2>/dev/null)
        echo -e "${GREEN}✓${NC} Database accessible ($ALERT_COUNT alerts)"
    else
        echo -e "${RED}✗${NC} Database not accessible or corrupted"
    fi
else
    echo -e "${RED}✗${NC} Database file not found"
    echo "   Run: cd Web-Interface && ../loki_env/bin/python3 init_database.py"
fi
echo ""

# 4. Check WebSocket endpoint
echo -e "${YELLOW}[4] Checking WebSocket endpoint...${NC}"
if curl -s -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
   -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
   http://localhost:8080/ws/alerts 2>&1 | grep -q "101\|426"; then
    echo -e "${GREEN}✓${NC} WebSocket endpoint responding"
else
    echo -e "${YELLOW}⚠${NC} WebSocket endpoint may have issues"
fi
echo ""

# 5. Check for Python errors in logs
echo -e "${YELLOW}[5] Checking for Python errors...${NC}"
if journalctl -u loki-web --since "5 minutes ago" 2>/dev/null | grep -i "error\|exception\|traceback" | tail -5; then
    echo -e "${RED}Found errors in logs (see above)${NC}"
else
    echo -e "${GREEN}✓${NC} No recent errors in logs"
fi
echo ""

# 6. Network accessibility
echo -e "${YELLOW}[6] Network information...${NC}"
PI_IP=$(hostname -I | awk '{print $1}')
echo "   Raspberry Pi IP: $PI_IP"
echo "   Access URL: http://$PI_IP:8080"
echo ""

# Summary
echo -e "${GREEN}======================================================"
echo "  Diagnostic Summary"
echo "======================================================${NC}"

if [ $STATS_OK -eq 0 ] && [ $STATUS_OK -eq 0 ] && [ $ALERTS_OK -eq 0 ]; then
    echo -e "${GREEN}✓ All critical API endpoints working${NC}"
    echo ""
    echo "The server is working! If browser still doesn't load:"
    echo ""
    echo "1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
    echo "2. Try incognito/private mode"
    echo "3. Check browser console for JavaScript errors:"
    echo "   - Press F12"
    echo "   - Go to Console tab"
    echo "   - Look for red errors"
    echo ""
    echo "4. Check Network tab in browser devtools:"
    echo "   - Press F12"
    echo "   - Go to Network tab"
    echo "   - Refresh page"
    echo "   - Look for failed requests (red)"
else
    echo -e "${RED}✗ Some API endpoints failed${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo ""
    echo "1. Check if database is initialized:"
    echo "   cd Web-Interface"
    echo "   ../loki_env/bin/python3 init_database.py"
    echo ""
    echo "2. Restart the web server:"
    echo "   pkill -f 'uvicorn.*api.main'"
    echo "   cd Web-Interface"
    echo "   bash start_web_server.sh"
    echo ""
    echo "3. Check server logs for errors:"
    echo "   Look at the terminal where you started the server"
fi

echo ""
echo "For more help, see: WEBINTERFACE_TROUBLESHOOTING.md"