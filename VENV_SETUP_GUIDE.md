# Unified Virtual Environment Setup Guide

This guide explains how to set up a single shared virtual environment for both the Loki IDS Core and Web Interface on your Raspberry Pi.

## Overview

Previously, the Web Interface had its own `venv` directory, and the Core IDS would use either `loki_env` or fall back to the Web Interface's venv. This setup consolidates everything into a single shared virtual environment at the project root.

## Benefits

- **Single dependency management**: Install packages once for both components
- **Easier maintenance**: Update dependencies in one place
- **Reduced disk space**: No duplicate packages
- **Consistent environment**: Both components use the same package versions

## Quick Setup

### 1. Run the Setup Script

From the Loki-IDS project root, run:

```bash
cd /home/zaher/Loki-IDS
bash setup_venv.sh
```

This will:
- Detect the best Python version (3.13, 3.12, 3.11, or system python3)
- Create a virtual environment at `loki_env/`
- Install all dependencies from `requirements.txt`
- Verify that critical packages are installed

### 2. Install System Dependencies (if needed)

If `netfilterqueue` fails to install, you need system development packages:

```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev libnetfilter-queue-dev
```

Then run the setup script again:

```bash
bash setup_venv.sh
```

### 3. Run the Components

Both scripts now automatically use the shared `loki_env`:

**Start the IDS Core:**
```bash
sudo bash run_loki.sh
```

**Start the Web Interface:**
```bash
cd Web-Interface
bash start_web_server.sh
```

## File Structure

```
Loki-IDS/
├── loki_env/              # Shared virtual environment (NEW)
├── requirements.txt        # Unified dependencies (NEW)
├── setup_venv.sh          # Setup script (NEW)
├── run_loki.sh            # Updated to use loki_env
├── Core/
│   └── loki/              # IDS Python files
└── Web-Interface/
    ├── start_web_server.sh # Updated to use loki_env
    └── requirements.txt    # Old file (kept for reference)
```

## Dependencies Installed

### Core IDS
- `netfilterqueue` - For packet capture and manipulation
- `scapy` - For packet parsing and analysis

### Web Interface
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - Database ORM
- `aiosqlite` - Async SQLite driver
- `pydantic` - Data validation
- `python-multipart` - Form data parsing
- `pyyaml` - YAML configuration support
- `psutil` - System monitoring
- `paho-mqtt` - IoT device communication

## Troubleshooting

### Virtual environment not found

If you see "Shared virtual environment not found", run:
```bash
bash setup_venv.sh
```

### Missing packages

To reinstall dependencies:
```bash
loki_env/bin/pip install -r requirements.txt
```

### Permission errors

The IDS Core requires root privileges:
```bash
sudo bash run_loki.sh
```

The Web Interface can run as a normal user:
```bash
cd Web-Interface && bash start_web_server.sh
```

### netfilterqueue installation fails

Install system dependencies first:
```bash
sudo apt-get install build-essential python3-dev libnetfilter-queue-dev
```

## Manual Virtual Environment Activation

If you need to manually work with the virtual environment:

```bash
# Activate
source loki_env/bin/activate

# Install a package
pip install some-package

# Deactivate
deactivate
```

## Migrating from Old Setup

If you previously used the Web-Interface's `venv`:

1. The old `Web-Interface/venv/` is no longer used
2. You can safely delete it to save space:
   ```bash
   rm -rf Web-Interface/venv
   ```
3. The scripts automatically use the new `loki_env`

## Updating Dependencies

To add new dependencies:

1. Edit `requirements.txt` at the project root
2. Install the new packages:
   ```bash
   loki_env/bin/pip install -r requirements.txt
   ```

## Notes for Raspberry Pi

- The setup script automatically detects Python 3.13, 3.12, or 3.11
- Some packages (like `netfilterqueue`) require compilation on ARM
- Ensure you have enough disk space (at least 500MB free)
- If running on a Pi Zero or older Pi, compilation may take several minutes