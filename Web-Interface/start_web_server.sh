#!/bin/bash
# Start the Loki IDS Web Interface server

cd "$(dirname "$0")"

echo "======================================================"
echo "    Starting Loki IDS Web Interface"
echo "======================================================"

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
    echo "[*] Installing dependencies..."
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -q -r requirements.txt
fi

# Install/update dependencies
echo "[*] Checking dependencies..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -q -r requirements.txt || {
    echo "[!] Warning: Some dependencies failed to install"
    echo "[*] Continuing anyway (web interface may still work)"
}

# Start the server
echo "[*] Starting FastAPI server..."
echo "[*] Dashboard will be available at: http://localhost:8080"
echo "[*] API documentation at: http://localhost:8080/docs"
echo ""

venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload

