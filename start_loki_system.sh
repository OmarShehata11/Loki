#!/bin/bash
# =================================================================
#  LOKI IDS - Complete System Startup
# =================================================================
# This script starts both the Web Interface and IDS Core in the
# correct order with proper API integration.
#
# Usage:
#   sudo bash start_loki_system.sh
# =================================================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB_DIR="$PROJECT_ROOT/Web-Interface"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "======================================================"
echo "         LOKI IDS - Complete System Startup"
echo "======================================================"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] This script must be run as root (sudo)${NC}"
    echo "    Usage: sudo bash start_loki_system.sh"
    exit 1
fi

# Step 1: Start Web Interface
echo -e "${CYAN}[1/3] Starting Web Interface...${NC}"
echo ""

if pgrep -f "uvicorn.*api.main:app" > /dev/null; then
    echo -e "${YELLOW}[*] Web Interface is already running${NC}"
    echo -e "${GREEN}[*] PID: $(pgrep -f 'uvicorn.*api.main:app')${NC}"
else
    # Start Web Interface in background
    cd "$WEB_DIR"
    bash start_web_server.sh > /tmp/loki_web.log 2>&1 &
    WEB_PID=$!

    echo -e "${YELLOW}[*] Waiting for Web Interface to start...${NC}"

    # Wait up to 10 seconds for the API to be ready
    for i in {1..10}; do
        if curl -s http://localhost:8080/api/system/health > /dev/null 2>&1; then
            echo -e "${GREEN}[✓] Web Interface started successfully (PID: $WEB_PID)${NC}"
            echo -e "${GREEN}[✓] Dashboard: http://localhost:8080${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    # Verify it actually started
    if ! curl -s http://localhost:8080/api/system/health > /dev/null 2>&1; then
        echo -e "${RED}[!] Web Interface failed to start${NC}"
        echo -e "${RED}[!] Check logs: tail /tmp/loki_web.log${NC}"
        exit 1
    fi
fi

echo ""

# Step 2: Brief pause
echo -e "${CYAN}[2/3] Preparing IDS Core...${NC}"
sleep 2
echo ""

# Step 3: Start IDS Core
echo -e "${CYAN}[3/3] Starting IDS Core...${NC}"
echo ""

cd "$PROJECT_ROOT"

# Check if IDS is already running
if pgrep -f "nfqueue_app" > /dev/null; then
    echo -e "${YELLOW}[*] IDS Core is already running${NC}"
    echo -e "${YELLOW}[*] PID: $(pgrep -f 'nfqueue_app')${NC}"
    echo ""
    echo -e "${GREEN}======================================================"
    echo "  System Status: Already Running"
    echo "======================================================${NC}"
    echo ""
    echo "Web Interface: http://localhost:8080"
    echo "IDS Core: Running (PID $(pgrep -f 'nfqueue_app'))"
    echo ""
    echo "To stop:"
    echo "  Web Interface: pkill -f 'uvicorn.*api.main'"
    echo "  IDS Core: sudo pkill -f 'nfqueue_app'"
    exit 0
fi

# Run IDS in foreground (blocks here)
echo -e "${GREEN}======================================================"
echo "  LOKI IDS System Started Successfully!"
echo "======================================================${NC}"
echo ""
echo -e "${GREEN}✓ Web Interface:${NC} http://localhost:8080"
echo -e "${GREEN}✓ IDS Core:${NC} Starting now..."
echo ""
echo -e "${YELLOW}[*] Press Ctrl+C to stop both services${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}[*] Shutting down LOKI IDS System...${NC}"

    # Stop IDS Core
    echo "[*] Stopping IDS Core..."
    bash "$PROJECT_ROOT/Scripts/iptables_down.sh" 2>/dev/null

    # Stop Web Interface
    echo "[*] Stopping Web Interface..."
    pkill -f "uvicorn.*api.main" 2>/dev/null

    echo -e "${GREEN}[+] LOKI IDS System stopped cleanly${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start IDS Core (will run in foreground)
bash "$PROJECT_ROOT/run_loki.sh"

# If IDS exits, cleanup
cleanup