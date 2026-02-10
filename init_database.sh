#!/bin/bash
# Initialize Loki IDS Database
# This script initializes the database for the new architecture

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/loki_env"

echo "======================================================="
echo "  Loki IDS - Database Initialization"
echo "======================================================="
echo ""

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "[!] Virtual environment not found at: $VENV_PATH"
    echo "[!] Please run setup_venv.sh first:"
    echo "    bash setup_venv.sh"
    exit 1
fi

# Run initialization script
cd "$PROJECT_ROOT/Core/loki"
"$VENV_PATH/bin/python3" init_database.py

echo ""
echo "You can now start the system with:"
echo "  sudo bash start_loki_system.sh"
