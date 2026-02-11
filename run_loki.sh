#!/bin/bash
# =================================================================
#  LOKI IDS - Run Everything
# =================================================================
# This script:
#   1. Calls Scripts/iptables_up.sh to set up NFQUEUE rules
#   2. Activates the Python virtual environment
#   3. Starts the IDS (Core/loki/nfqueue_app.py)
#   4. On exit (Ctrl+C), calls Scripts/iptables_down.sh to clean up
#
# Project structure expected:
#   Loki-IDS/
#   ├── Core/loki/         <- IDS Python files
#   ├── Scripts/           <- iptables_up.sh, iptables_down.sh
#   ├── loki_env/          <- virtual environment
#   └── run_loki.sh        <- this script (lives in project root)
#
# Usage:
#   cd /path/to/Loki-IDS
#   sudo bash run_loki.sh
# =================================================================

# --- Resolve project root (where this script lives) ---
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# --- Paths ---
SCRIPTS_DIR="$PROJECT_ROOT/Scripts"
IDS_DIR="$PROJECT_ROOT/Core/loki"
VENV_PATH="$PROJECT_ROOT/loki_env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "======================================================"
echo "            LOKI IDS - Starting Up"
echo "======================================================"
echo -e "${NC}"
echo "[*] Project root: $PROJECT_ROOT"

# --- Check: Must be root ---
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] This script must be run as root (sudo).${NC}"
    echo "    Usage: sudo bash run_loki.sh"
    exit 1
fi

# --- Check: Scripts exist ---
if [ ! -f "$SCRIPTS_DIR/iptables_up.sh" ]; then
    echo -e "${RED}[!] Cannot find Scripts/iptables_up.sh${NC}"
    echo "    Make sure you run this from the Loki-IDS root directory."
    exit 1
fi

if [ ! -f "$IDS_DIR/nfqueue_app.py" ]; then
    echo -e "${RED}[!] Cannot find Core/loki/nfqueue_app.py${NC}"
    exit 1
fi

# --- Check: Virtual environment ---
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}[!] Virtual environment not found at: $VENV_PATH${NC}"
    echo "[*] Looking for alternative venv locations..."

    # Try Web-Interface venv as fallback
    if [ -d "$PROJECT_ROOT/Web-Interface/venv" ]; then
        VENV_PATH="$PROJECT_ROOT/Web-Interface/venv"
        echo -e "${GREEN}[+] Found venv at: $VENV_PATH${NC}"
    else
        echo -e "${RED}[!] No virtual environment found.${NC}"
        echo "    Please run: bash Scripts/install_deps.sh"
        exit 1
    fi
fi

# --- Cleanup function (runs on Ctrl+C or exit) ---
cleanup() {
    echo ""
    echo -e "${YELLOW}[*] Shutting down LOKI IDS...${NC}"

    # Call the existing iptables_down.sh script
    echo "[*] Running Scripts/iptables_down.sh..."
    bash "$SCRIPTS_DIR/iptables_down.sh"

    echo -e "${GREEN}[+] LOKI IDS stopped cleanly.${NC}"
    exit 0
}

# Register cleanup on Ctrl+C and termination
trap cleanup SIGINT SIGTERM

# --- Step 1: Setup iptables ---
echo -e "${CYAN}[1/3] Setting up iptables...${NC}"
bash "$SCRIPTS_DIR/iptables_up.sh"
echo ""


# --- Step 3: Run IDS ---
echo -e "${CYAN}[3/3] Launching IDS engine...${NC}"
echo ""
echo -e "${GREEN}======================================================"
echo "  LOKI IDS is running!"
echo "  Detection: Sliding Window + EWMA"
echo "  Press Ctrl+C to stop"
echo "======================================================${NC}"
echo ""

cd "$IDS_DIR"
"$VENV_PATH/bin/python3" nfqueue_app.py

# If nfqueue_app.py exits on its own (not via Ctrl+C), still clean up
cleanup