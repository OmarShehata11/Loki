#!/bin/bash
# Start the Loki IDS API Server

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/loki_env"

cd "$(dirname "$0")"

echo "[*] Starting Loki IDS API Server..."
echo "[*] Using virtual environment: $VENV_PATH"

if [ ! -d "$VENV_PATH" ]; then
    echo "[!] Virtual environment not found: $VENV_PATH"
    echo "[!] Please run: bash $PROJECT_ROOT/setup_venv.sh"
    exit 1
fi

"$VENV_PATH/bin/python3" api_server.py
