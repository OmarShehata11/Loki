# Loki IDS

A real-time network intrusion detection system that combines behavioral analysis and signature-based detection to identify threats on your network. Includes a web dashboard for monitoring alerts and controlling IoT devices via MQTT.

Built with Python, Netfilter, FastAPI, and Scapy.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

---

## How It Works

Loki IDS sits between your network and the Linux kernel using **Netfilter queues**. Every incoming and forwarded packet is intercepted, parsed, and analyzed in real time by two detection engines:

- **Behavioral Detection** — Uses sliding time windows combined with EWMA (Exponentially Weighted Moving Average) rate estimation to detect port scans, TCP/UDP/ICMP floods. Both the packet count *and* the EWMA rate must exceed their thresholds before an alert fires, reducing false positives.

- **Signature Detection** — Matches packet payloads against a database of patterns (SQL injection, XSS, path traversal, command injection, etc.). Signatures are managed through the web dashboard and loaded at runtime.

Alerts follow a lifecycle: **STARTED** (new attack detected) → **ONGOING** (periodic updates during sustained attacks) → **ENDED** (attack stopped, summary logged). This prevents log flooding while preserving forensic data like total duration, packet count, and average packets-per-second.

```
┌──────────────┐     ┌──────────────┐     ┌───────────────┐
│   Network    │────>│  Netfilter   │────>│   Loki IDS    │
│   Traffic    │     │   Queue      │     │  Detection    │
└──────────────┘     └──────────────┘     │  Engine       │
                                          └──────┬────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                              ┌─────▼──────┐          ┌──────▼───────┐
                              │ Behavioral │          │  Signature   │
                              │  Analysis  │          │  Matching    │
                              │ (EWMA +    │          │ (Payload     │
                              │  Sliding   │          │  Patterns)   │
                              │  Window)   │          │              │
                              └─────┬──────┘          └──────┬───────┘
                                    │                         │
                                    └────────────┬────────────┘
                                                 │
                                          ┌──────▼────────┐
                                          │  Alert Logger │
                                          │  (Lifecycle   │
                                          │   Tracking)   │
                                          └──────┬────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                              ┌─────▼──────┐          ┌──────▼───────┐
                              │  FastAPI   │          │  JSONL Log   │
                              │  + SQLite  │          │  File        │
                              └─────┬──────┘          └──────────────┘
                                    │
                              ┌─────▼──────┐
                              │    Web     │
                              │ Dashboard  │
                              └────────────┘
```

---

## Features

### Detection
- **Port Scan Detection** — Detects scanning of 20+ unique ports within a 5-second window
- **TCP SYN Flood Detection** — Dual-threshold: 200+ SYN packets/2s *and* EWMA rate > 100 pps
- **UDP Flood Detection** — Dual-threshold: 300+ packets/2s *and* EWMA rate > 150 pps
- **ICMP Flood Detection** — Dual-threshold: 100+ echo requests/2s *and* EWMA rate > 50 pps
- **Signature Matching** — 20+ built-in rules covering SQL injection, XSS, path traversal, command injection, and more
- **Custom Signatures** — Add your own detection rules via the dashboard or YAML import

### Alert Management
- **Alert Lifecycle Tracking** — STARTED → ONGOING → ENDED with packet counts and duration
- **Smart Deduplication** — Suppresses duplicate alerts during sustained attacks (max 3 updates per attack)
- **Attack Summary** — When an attack ends, logs total duration, packet count, and average rate

### Web Dashboard
- **Real-time Monitoring** — Live alert feed with WebSocket updates
- **Filtering** — Filter alerts by type, subtype, pattern, status, source/destination IP
- **Signature Management** — Create, edit, enable/disable, and delete detection rules
- **Statistics** — Alerts by type, top attacking IPs, 24-hour activity overview
- **YAML Import** — Bulk import signatures from YAML files

### IoT Integration
- **MQTT Device Control** — Control ESP32 devices (bulbs, alarms, buzzers, LEDs) through the dashboard
- **Device Status Tracking** — Real-time online/offline detection via MQTT heartbeats
- **Multi-Broker Support** — Connect to local or remote MQTT brokers

---

## Project Structure

```
Loki-IDS/
├── Core/loki/                      # IDS Engine
│   ├── nfqueue_app.py              # Main packet processor (Netfilter queue binding)
│   ├── detectore_engine.py         # Behavioral detection (EWMA + sliding windows)
│   ├── signature_engine.py         # Signature-based payload matching
│   ├── logger.py                   # Alert lifecycle management and logging
│   ├── packet_parser.py            # Packet parsing (TCP/UDP/ICMP extraction)
│   ├── db_integration.py           # HTTP client for API communication
│   ├── api/                        # FastAPI Web Interface
│   │   ├── main.py                 # App initialization, CORS, routing
│   │   ├── models/
│   │   │   ├── database.py         # SQLAlchemy models (Alert, Signature, IoT)
│   │   │   ├── schemas.py          # Pydantic validation schemas
│   │   │   └── crud.py             # Database operations
│   │   ├── routes/
│   │   │   ├── alerts.py           # Alert CRUD + filtering endpoints
│   │   │   ├── signatures.py       # Signature management + YAML import
│   │   │   ├── system.py           # Health checks, IDS status
│   │   │   ├── stats.py            # Statistics aggregation
│   │   │   ├── websocket.py        # Real-time WebSocket alerts
│   │   │   └── iot.py              # IoT device control (MQTT commands)
│   │   └── iot/
│   │       └── mqtt_client.py      # MQTT client (paho-mqtt 2.x compatible)
│   ├── example_signatures.yaml     # Built-in detection rules
│   └── database/                   # SQLite database directory
├── Web-Interface/static/           # Frontend (HTML/CSS/JS)
│   ├── index.html                  # Dashboard UI
│   ├── css/style.css               # Styling
│   └── js/app.js                   # Dashboard logic
├── Scripts/
│   ├── iptables_up.sh              # Netfilter queue setup (INPUT + FORWARD)
│   ├── iptables_down.sh            # Firewall rule cleanup
│   └── setup_iot_devices.py        # IoT device registration utility
├── attack-scripts/                 # Attack simulation for testing
│   ├── dos-tcp.sh                  # TCP SYN flood
│   ├── dos-udp.sh                  # UDP flood
│   ├── icmp-attack.sh              # ICMP flood
│   └── nmap-portscan.sh            # Port scan
├── start_loki_system.sh            # Full system startup (API + IDS + iptables)
├── run_loki.sh                     # IDS-only startup
├── setup_venv.sh                   # Virtual environment setup
└── requirements.txt                # Python dependencies
```

---

## Requirements

- **OS:** Linux (kernel with Netfilter support)
- **Python:** 3.11 or higher
- **Privileges:** Root access (required for Netfilter queues and iptables)
- **System packages:**
  ```
  libnetfilter-queue-dev
  python3-dev
  iptables
  ```
- **Optional:** MQTT broker (e.g., Mosquitto) for IoT features

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/LoKi-IDS/Loki-IDS.git
cd Loki-IDS
```

### 2. Install system dependencies

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install libnetfilter-queue-dev python3-dev iptables

# Or run the provided script
sudo bash Scripts/install_deps.sh
```

### 3. Set up the Python environment

```bash
bash setup_venv.sh
```

This creates a virtual environment, installs all Python dependencies, and verifies critical packages.

### 4. (Optional) Install MQTT broker for IoT features

```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

---

## Usage

### Start the full system

```bash
sudo bash start_loki_system.sh
```

This will:
1. Start the FastAPI web server on `http://localhost:8080`
2. Set up iptables Netfilter queue rules
3. Launch the IDS detection engine

Open **http://localhost:8080** in your browser to access the dashboard.

### Stop the system

Press `Ctrl+C` in the terminal. The cleanup handler will:
- Flush iptables rules
- Stop the API server
- Log session statistics

### Import signatures

You can import detection rules from a YAML file through the dashboard, or use the included example:

```yaml
# example_signatures.yaml
signatures:
  - name: "SQL Injection - Union Select"
    pattern: "UNION SELECT"
    action: "alert"
    description: "Detects SQL injection attempts using UNION SELECT"
```

### Test detection

Use the included attack simulation scripts from a separate machine (or another terminal targeting the IDS host):

```bash
# Port scan
bash attack-scripts/nmap-portscan.sh <target-ip>

# TCP SYN flood
bash attack-scripts/dos-tcp.sh <target-ip> <port>

# UDP flood
bash attack-scripts/dos-udp.sh <target-ip> <port>

# ICMP flood
bash attack-scripts/icmp-attack.sh <target-ip>
```

---

## API Endpoints

The REST API is available at `http://localhost:8080/api`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/alerts` | List alerts (with filtering and pagination) |
| `GET` | `/api/alerts/{id}` | Get a single alert |
| `POST` | `/api/alerts` | Create an alert (used by IDS core) |
| `DELETE` | `/api/alerts/{id}` | Delete an alert |
| `GET` | `/api/signatures` | List signatures |
| `GET` | `/api/signatures/{id}` | Get a single signature |
| `POST` | `/api/signatures` | Create a signature |
| `PUT` | `/api/signatures/{id}` | Update a signature |
| `DELETE` | `/api/signatures/{id}` | Delete a signature |
| `POST` | `/api/signatures/reload` | Import signatures from YAML |
| `GET` | `/api/stats` | Get alert statistics |
| `GET` | `/api/system/health` | Health check |
| `GET` | `/api/system/status` | IDS running status |
| `GET` | `/api/iot/devices` | List IoT devices |
| `POST` | `/api/iot/devices/{id}/bulb` | Control bulb |
| `POST` | `/api/iot/devices/{id}/alarm` | Control alarm |
| `POST` | `/api/iot/devices/{id}/buzzer` | Control buzzer |
| `POST` | `/api/iot/devices/{id}/led` | Control LED |
| `GET` | `/api/iot/mqtt/status` | MQTT connection status |
| `POST` | `/api/iot/mqtt/connect` | Connect to MQTT broker |

Full interactive API docs available at `http://localhost:8080/docs` (Swagger UI).

---

## Detection Thresholds

| Attack Type | Window | Count Threshold | EWMA Rate Threshold |
|-------------|--------|----------------|---------------------|
| Port Scan | 5 seconds | 20 unique ports | N/A |
| TCP SYN Flood | 2 seconds | 200 packets | 100 pps |
| UDP Flood | 2 seconds | 300 packets | 150 pps |
| ICMP Flood | 2 seconds | 100 packets | 50 pps |

Alerts only fire when **both** the sliding window count and the EWMA rate exceed their thresholds simultaneously.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Packet Capture | Netfilter Queue (`netfilterqueue`) |
| Packet Parsing | Scapy |
| Detection Engine | Python (EWMA + sliding windows) |
| Web API | FastAPI + Uvicorn |
| Database | SQLite (async via `aiosqlite`) |
| ORM | SQLAlchemy 2.0 (async) |
| Frontend | Vanilla HTML/CSS/JavaScript + Chart.js |
| IoT Communication | MQTT (`paho-mqtt` 2.x) |
| Process Management | Bash scripts + iptables |

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2025 Omar Shehata
