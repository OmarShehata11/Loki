#!/bin/bash
# Start the Loki IDS Web Interface server

cd "$(dirname "$0")"

echo "======================================================"
echo "    Starting Loki IDS Web Interface"
echo "======================================================"

# Function to check if a package is installed in venv
check_package_installed() {
    # Map package names to their import names
    case "$1" in
        "fastapi") venv/bin/python3 -c "import fastapi" 2>/dev/null ;;
        "uvicorn") venv/bin/python3 -c "import uvicorn" 2>/dev/null ;;
        "sqlalchemy") venv/bin/python3 -c "import sqlalchemy" 2>/dev/null ;;
        "aiosqlite") venv/bin/python3 -c "import aiosqlite" 2>/dev/null ;;
        "pydantic") venv/bin/python3 -c "import pydantic" 2>/dev/null ;;
        "python-multipart") venv/bin/python3 -c "import multipart" 2>/dev/null ;;
        "pyyaml") venv/bin/python3 -c "import yaml" 2>/dev/null ;;
        "psutil") venv/bin/python3 -c "import psutil" 2>/dev/null ;;
        *) venv/bin/python3 -c "import $1" 2>/dev/null ;;
    esac
}

# Function to check internet connectivity
check_internet() {
    # Try to ping a reliable server (with timeout)
    ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1 || ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1
}

# Function to check if critical packages are installed
check_critical_packages() {
    local missing=0
    local critical_packages=("fastapi" "uvicorn" "sqlalchemy" "aiosqlite" "pydantic")
    
    for pkg in "${critical_packages[@]}"; do
        if ! check_package_installed "$pkg"; then
            echo "[!] Missing critical package: $pkg"
            missing=$((missing + 1))
        fi
    done
    
    return $missing
}

# Detect Python 3.13 if available, otherwise fall back to python3
PYTHON_CMD="python3"
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    echo "[*] Using Python 3.13"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "[*] Using Python 3.12"
else
    echo "[*] Using system Python 3"
fi

# Check if virtual environment exists, create if needed
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment with $PYTHON_CMD..."
    env -i PATH=/usr/bin:/bin "$PYTHON_CMD" -m venv venv
    
    # Check for internet before trying to install
    if check_internet; then
        echo "[*] Internet connection detected. Installing dependencies..."
        venv/bin/pip install --upgrade pip 2>/dev/null || true
        venv/bin/pip install -q -r requirements.txt 2>/dev/null || {
            echo "[!] Warning: Failed to install some dependencies"
            echo "[*] Continuing anyway..."
        }
    else
        echo "[!] No internet connection detected"
        echo "[!] Virtual environment created but dependencies not installed"
        echo "[!] Please install dependencies manually when online:"
        echo "    source venv/bin/activate"
        echo "    pip install -r requirements.txt"
        echo ""
        echo "[!] Attempting to start server anyway (may fail if packages missing)..."
    fi
fi

# Check if critical packages are installed
if ! check_critical_packages; then
    echo "[*] Some critical packages may be missing"
    
    # Try to install/update dependencies only if internet is available
    if check_internet; then
        echo "[*] Internet connection detected. Attempting to install/update dependencies..."
        venv/bin/pip install --upgrade pip 2>/dev/null || true
        venv/bin/pip install -q -r requirements.txt 2>/dev/null || {
            echo "[!] Warning: Some dependencies failed to install"
            echo "[*] Continuing anyway (web interface may still work)"
        }
    else
        echo "[!] No internet connection and some packages may be missing"
        echo "[!] Server will attempt to start, but may fail if critical packages are missing"
        echo "[!] Install dependencies when online: pip install -r requirements.txt"
    fi
else
    echo "[✓] All critical packages are installed"
    
    # Optional: Try to update packages if internet is available (non-blocking)
    if check_internet; then
        echo "[*] Internet connection detected. Checking for package updates (optional)..."
        venv/bin/pip install --upgrade pip >/dev/null 2>&1 || true
        venv/bin/pip install -q -r requirements.txt >/dev/null 2>&1 || true
    fi
fi

# Final check before starting
if ! check_critical_packages; then
    echo ""
    echo "[!] WARNING: Critical packages are missing!"
    echo "[!] The server may not start properly."
    echo "[!] Please install dependencies: pip install -r requirements.txt"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[*] Exiting. Please install dependencies first."
        exit 1
    fi
fi

# Start the server
echo "[*] Starting FastAPI server..."
echo "[*] Dashboard will be available at: http://localhost:8080"
echo "[*] API documentation at: http://localhost:8080/docs"
echo ""

venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload

