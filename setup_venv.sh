#!/bin/bash
# =================================================================
#  LOKI IDS - Setup Shared Virtual Environment
# =================================================================
# This script creates a unified virtual environment for both
# the Core IDS and Web Interface components
# =================================================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/loki_env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "======================================================"
echo "    LOKI IDS - Virtual Environment Setup"
echo "======================================================"
echo -e "${NC}"

# Detect Python version
PYTHON_CMD="python3"
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    echo -e "${GREEN}[+] Found Python 3.13${NC}"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}[+] Found Python 3.12${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}[+] Found Python 3.11${NC}"
else
    echo -e "${YELLOW}[*] Using system python3${NC}"
fi

# Check if venv already exists
if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}[!] Virtual environment already exists at: $VENV_PATH${NC}"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}[*] Removing existing venv...${NC}"
        rm -rf "$VENV_PATH"
    else
        echo -e "${GREEN}[+] Keeping existing venv. Installing/updating dependencies...${NC}"
        "$VENV_PATH/bin/pip" install --upgrade pip
        "$VENV_PATH/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"
        echo -e "${GREEN}[+] Done!${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${CYAN}[*] Creating virtual environment at: $VENV_PATH${NC}"
$PYTHON_CMD -m venv "$VENV_PATH"

if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}[!] Failed to create virtual environment${NC}"
    exit 1
fi

# Upgrade pip
echo -e "${CYAN}[*] Upgrading pip...${NC}"
"$VENV_PATH/bin/pip" install --upgrade pip

# Install dependencies
echo -e "${CYAN}[*] Installing dependencies from requirements.txt...${NC}"
"$VENV_PATH/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"

# Verify critical packages
echo -e "${CYAN}[*] Verifying installation...${NC}"
MISSING=0

check_package() {
    if ! "$VENV_PATH/bin/python" -c "import $1" 2>/dev/null; then
        echo -e "${RED}[!] Missing: $1${NC}"
        MISSING=$((MISSING + 1))
    else
        echo -e "${GREEN}[✓] Installed: $1${NC}"
    fi
}

# Check Core IDS packages
check_package "netfilterqueue"
check_package "scapy"

# Check Web Interface packages
check_package "fastapi"
check_package "uvicorn"
check_package "sqlalchemy"
check_package "aiosqlite"

if [ $MISSING -gt 0 ]; then
    echo -e "${YELLOW}[!] Warning: $MISSING package(s) missing${NC}"
    echo -e "${YELLOW}[!] You may need to install system dependencies first${NC}"
    echo -e "${YELLOW}[!] For netfilterqueue: sudo apt-get install build-essential python3-dev libnetfilter-queue-dev${NC}"
else
    echo -e "${GREEN}"
    echo "======================================================"
    echo "  Virtual Environment Setup Complete!"
    echo "======================================================"
    echo -e "${NC}"
    echo "Virtual environment location: $VENV_PATH"
    echo ""
    echo "To activate manually:"
    echo "  source $VENV_PATH/bin/activate"
    echo ""
    echo "The run_loki.sh and start_web_server.sh scripts will"
    echo "automatically use this shared virtual environment."
fi