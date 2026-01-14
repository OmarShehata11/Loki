# Python 3.13.5 Setup Guide for Raspberry Pi 5

This guide helps you set up Python 3.13.5 on Raspberry Pi 5 and configure the Loki IDS Web Interface to use it.

## Prerequisites

- Raspberry Pi 5 running Raspberry Pi OS (Debian-based)
- Root/sudo access
- Internet connection

## Step 1: Install Python 3.13.5

### Option A: Build from Source (Recommended for Raspberry Pi 5)

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install build dependencies
sudo apt-get install -y \
    build-essential \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libsqlite3-dev \
    libreadline-dev \
    libffi-dev \
    curl \
    libbz2-dev \
    liblzma-dev \
    libgdbm-compat-dev \
    libmpdec-dev \
    tk-dev

# Download Python 3.13.5 source
cd /tmp
wget https://www.python.org/ftp/python/3.13.5/Python-3.13.5.tgz
tar -xf Python-3.13.5.tgz
cd Python-3.13.5

# Configure build (optimized for Raspberry Pi 5)
./configure --enable-optimizations --with-system-ffi

# Build (use all CPU cores for faster compilation)
make -j$(nproc)

# Install (use altinstall to keep system Python 3)
sudo make altinstall

# Verify installation
python3.13 --version
# Should output: Python 3.13.5
```

### Option B: Use pyenv (Alternative Method)

```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to shell profile
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
source ~/.bashrc

# Install Python 3.13.5
pyenv install 3.13.5
pyenv global 3.13.5
```

## Step 2: Install System Dependencies for IDS

```bash
# Required for netfilterqueue and scapy
sudo apt-get install -y \
    python3.13-dev \
    libnetfilter-queue-dev \
    libnfnetlink-dev \
    libpcap-dev
```

## Step 3: Setup Web Interface with Python 3.13.5

```bash
cd /home/zaher/Loki-IDS/Web-Interface

# Remove old venv if exists
rm -rf venv

# Create virtual environment with Python 3.13.5
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install web interface dependencies
pip install -r requirements.txt

# Install IDS dependencies (if running IDS)
pip install -r requirements-ids.txt
```

**Note:** If `netfilterqueue` installation fails, try building from source:
```bash
pip install --no-binary netfilterqueue netfilterqueue
```

## Step 4: Verify Setup

```bash
# Check Python version in venv
venv/bin/python3 --version
# Should show: Python 3.13.5

# Test imports
venv/bin/python3 -c "import fastapi, uvicorn, sqlalchemy; print('All imports successful')"

# If running IDS, test IDS dependencies
venv/bin/python3 -c "import netfilterqueue, scapy; print('IDS dependencies OK')"
```

## Step 5: Start the Web Interface

The startup script will automatically detect Python 3.13:

```bash
cd /home/zaher/Loki-IDS/Web-Interface
./start_web_server.sh
```

Or manually:
```bash
venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8080
```

## Step 6: Run IDS with Integration

```bash
cd /home/zaher/Loki-IDS

# The script will automatically use Python 3.13 from venv
sudo Web-Interface/venv/bin/python3.13 Web-Interface/run_ids_with_integration.py
```

## Troubleshooting

### Issue: `netfilterqueue` fails to install

**Solution:**
```bash
# Install build dependencies
sudo apt-get install -y python3.13-dev libnetfilter-queue-dev

# Build from source
pip install --no-binary netfilterqueue netfilterqueue
```

### Issue: `scapy` installation fails

**Solution:**
```bash
# Update to latest version
pip install --upgrade scapy
```

### Issue: Virtual environment uses wrong Python version

**Solution:**
```bash
# Remove and recreate venv
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: Import errors after deployment

**Solution:**
1. Verify Python version: `venv/bin/python3 --version`
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check for architecture mismatch (ARM64 vs ARM32)

## Architecture Notes for Raspberry Pi 5

Raspberry Pi 5 uses **ARM64 (aarch64)** architecture. Ensure:
- Python 3.13.5 is built for ARM64
- All packages have ARM64 wheels or can be built from source
- System libraries match the architecture

## Verification Checklist

- [ ] Python 3.13.5 installed and accessible
- [ ] Virtual environment created with Python 3.13.5
- [ ] All web interface dependencies installed
- [ ] IDS dependencies installed (if needed)
- [ ] Web interface starts successfully
- [ ] IDS runs with integration (if needed)
- [ ] No import errors in logs

## Additional Resources

- [Python 3.13.5 Release Notes](https://www.python.org/downloads/release/python-3135/)
- [Raspberry Pi 5 Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi-5.html)
