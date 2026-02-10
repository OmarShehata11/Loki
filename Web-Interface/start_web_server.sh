#!/bin/bash
# Start the Loki IDS Web Interface server

# Get the project root (one directory up from Web-Interface)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/loki_env"

cd "$(dirname "$0")"

echo "======================================================"
echo "    Starting Loki IDS Web Interface"
echo "======================================================"

# Function to check if a package is installed in venv
check_package_installed() {
    # Map package names to their import names
    case "$1" in
        "fastapi") "$VENV_PATH/bin/python3" -c "import fastapi" 2>/dev/null ;;
        "uvicorn") "$VENV_PATH/bin/python3" -c "import uvicorn" 2>/dev/null ;;
        "sqlalchemy") "$VENV_PATH/bin/python3" -c "import sqlalchemy" 2>/dev/null ;;
        "aiosqlite") "$VENV_PATH/bin/python3" -c "import aiosqlite" 2>/dev/null ;;
        "pydantic") "$VENV_PATH/bin/python3" -c "import pydantic" 2>/dev/null ;;
        "python-multipart") "$VENV_PATH/bin/python3" -c "import multipart" 2>/dev/null ;;
        "pyyaml") "$VENV_PATH/bin/python3" -c "import yaml" 2>/dev/null ;;
        "psutil") "$VENV_PATH/bin/python3" -c "import psutil" 2>/dev/null ;;
        *) "$VENV_PATH/bin/python3" -c "import $1" 2>/dev/null ;;
    esac
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

# Check if shared virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "[!] Shared virtual environment not found at: $VENV_PATH"
    echo "[!] Please run the setup script first:"
    echo "    cd $PROJECT_ROOT"
    echo "    bash setup_venv.sh"
    echo ""

    # Fall back to local venv for backward compatibility
    if [ -d "venv" ]; then
        echo "[*] Using local venv as fallback..."
        VENV_PATH="$(pwd)/venv"
    else
        echo "[!] No virtual environment found. Exiting."
        exit 1
    fi
fi

echo "[*] Using virtual environment: $VENV_PATH"

# Check if critical packages are installed
if ! check_critical_packages; then
    echo ""
    echo "[!] WARNING: Critical packages are missing!"
    echo "[!] Please run the setup script to install dependencies:"
    echo "    cd $PROJECT_ROOT"
    echo "    bash setup_venv.sh"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[*] Exiting. Please install dependencies first."
        exit 1
    fi
else
    echo "[✓] All critical packages are installed"
fi

# Start the server
echo "[*] Starting FastAPI server..."
echo "[*] Dashboard will be available at: http://localhost:8080"
echo "[*] API documentation at: http://localhost:8080/docs"
echo ""

"$VENV_PATH/bin/uvicorn" api.main:app --host 0.0.0.0 --port 8080 --reload

