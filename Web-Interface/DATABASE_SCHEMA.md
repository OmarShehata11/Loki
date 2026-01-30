# Database Schema Documentation

## Overview

The Loki IDS Web Interface uses SQLite for lightweight, file-based storage. Since SQLite doesn't support native enums, enum values are stored as `VARCHAR` (strings) and validated at the application level using Python enums.

## Database File

- **Location**: `Web-Interface/loki_ids.db`
- **Type**: SQLite 3

## Tables

### 1. `alerts` - Security Alerts/Events

Stores all security alerts detected by the IDS with lifecycle tracking.

#### Schema

```sql
CREATE TABLE alerts (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    timestamp VARCHAR NOT NULL,                    -- ISO format timestamp
    status VARCHAR,                                 -- AlertStatus enum (as string)
    type VARCHAR NOT NULL,                          -- AlertType enum (as string)
    subtype VARCHAR,                                -- AlertSubtype enum (as string)
    src_ip VARCHAR NOT NULL,                        -- Source IP address
    dst_ip VARCHAR,                                 -- Destination IP address
    src_port INTEGER,                               -- Source port
    dst_port INTEGER,                               -- Destination port
    message TEXT NOT NULL,                          -- Human-readable alert message
    details TEXT,                                   -- JSON string with additional data
    severity VARCHAR DEFAULT 'MEDIUM',              -- LOW, MEDIUM, HIGH, CRITICAL
    duration_seconds VARCHAR,                       -- For ONGOING alerts
    packet_count INTEGER,                           -- For ONGOING alerts
    attack_rate_pps VARCHAR,                        -- For ONGOING alerts (packets per second)
    total_duration_seconds VARCHAR,                 -- For ENDED alerts
    total_packets INTEGER,                          -- For ENDED alerts
    average_rate_pps VARCHAR,                       -- For ENDED alerts (packets per second)
    first_seen VARCHAR,                             -- For ENDED alerts (ISO timestamp)
    last_seen VARCHAR                               -- For ENDED alerts (ISO timestamp)
);
```

#### Indexes

```sql
CREATE INDEX idx_timestamp ON alerts(timestamp);
CREATE INDEX idx_src_ip ON alerts(src_ip);
CREATE INDEX idx_type ON alerts(type);
CREATE INDEX idx_status ON alerts(status);
CREATE INDEX idx_subtype ON alerts(subtype);
```

#### Enum Values (Stored as Strings)

**`type` (AlertType):**
- `"SIGNATURE"` - Signature-based detection
- `"BEHAVIOR"` - Behavioral detection
- `"SYSTEM"` - System events

**`subtype` (AlertSubtype) - Optional, only for BEHAVIOR type:**
- `"PORT_SCAN"` - TCP port scanning
- `"TCP_FLOOD"` - TCP flood (DoS/DDoS)
- `"UDP_FLOOD"` - UDP flood (DoS/DDoS)
- `"ICMP_FLOOD"` - ICMP flood (DoS/DDoS)
- `NULL` - For SIGNATURE and SYSTEM types

**`status` (AlertStatus) - Optional:**
- `"STARTED"` - Alert just started
- `"ONGOING"` - Alert is ongoing (with updates)
- `"ENDED"` - Alert has ended
- `NULL` - Legacy alerts without status

**`severity`:**
- `"LOW"`
- `"MEDIUM"` (default)
- `"HIGH"`
- `"CRITICAL"`

#### Example Records

```json
{
  "id": 1,
  "timestamp": "2026-01-30T22:15:00.123456",
  "status": "STARTED",
  "type": "BEHAVIOR",
  "subtype": "PORT_SCAN",
  "src_ip": "192.168.1.100",
  "dst_ip": "192.168.1.1",
  "src_port": 54321,
  "dst_port": 80,
  "message": "Port Scan Detected on INPUT chain",
  "details": "{\"dst_ip\": \"192.168.1.1\", \"dst_port\": 80, \"chain\": \"INPUT\"}",
  "severity": "MEDIUM",
  "duration_seconds": null,
  "packet_count": null,
  "attack_rate_pps": null,
  "total_duration_seconds": null,
  "total_packets": null,
  "average_rate_pps": null,
  "first_seen": null,
  "last_seen": null
}
```

```json
{
  "id": 2,
  "timestamp": "2026-01-30T22:15:05.456789",
  "status": "ONGOING",
  "type": "BEHAVIOR",
  "subtype": "TCP_FLOOD",
  "src_ip": "10.0.0.50",
  "dst_ip": "10.0.0.1",
  "src_port": 12345,
  "dst_port": 443,
  "message": "TCP Flood (DoS/DDoS) Detected on FORWARD chain",
  "details": "{\"dst_ip\": \"10.0.0.1\", \"dst_port\": 443, \"chain\": \"FORWARD\"}",
  "severity": "HIGH",
  "duration_seconds": "5.2",
  "packet_count": 1250,
  "attack_rate_pps": "240.4",
  "total_duration_seconds": null,
  "total_packets": null,
  "average_rate_pps": null,
  "first_seen": null,
  "last_seen": null
}
```

```json
{
  "id": 3,
  "timestamp": "2026-01-30T22:15:20.789012",
  "status": "ENDED",
  "type": "BEHAVIOR",
  "subtype": "UDP_FLOOD",
  "src_ip": "172.16.0.10",
  "dst_ip": "172.16.0.1",
  "src_port": 54321,
  "dst_port": 53,
  "message": "UDP Flood (DoS/DDoS) Detected on INPUT chain",
  "details": "{\"dst_ip\": \"172.16.0.1\", \"dst_port\": 53, \"chain\": \"INPUT\"}",
  "severity": "HIGH",
  "duration_seconds": null,
  "packet_count": null,
  "attack_rate_pps": null,
  "total_duration_seconds": "15.5",
  "total_packets": 3500,
  "average_rate_pps": "225.8",
  "first_seen": "2026-01-30T22:15:05.123456",
  "last_seen": "2026-01-30T22:15:20.623456"
}
```

### 2. `signatures` - Detection Signatures

Stores signature rules for pattern-based detection.

#### Schema

```sql
CREATE TABLE signatures (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,                   -- Unique signature name
    pattern TEXT NOT NULL,                          -- Detection pattern
    action VARCHAR NOT NULL DEFAULT 'alert',        -- Always 'alert' (drop removed)
    description TEXT,                               -- Optional description
    enabled INTEGER DEFAULT 1,                      -- 1 = enabled, 0 = disabled
    created_at VARCHAR,                             -- ISO timestamp
    updated_at VARCHAR                              -- ISO timestamp
);
```

#### Indexes

```sql
CREATE INDEX ix_signatures_id ON signatures(id);
```

#### Example Record

```json
{
  "id": 1,
  "name": "SQL Injection - Union Select",
  "pattern": "UNION SELECT",
  "action": "alert",
  "description": "Detects SQL injection attempts using UNION SELECT statements",
  "enabled": 1,
  "created_at": "2026-01-30T20:00:00.000000",
  "updated_at": "2026-01-30T20:00:00.000000"
}
```

### 3. `stats_cache` - Cached Statistics

Stores pre-computed statistics for performance optimization.

#### Schema

```sql
CREATE TABLE stats_cache (
    key VARCHAR NOT NULL PRIMARY KEY,               -- Cache key
    value TEXT,                                     -- JSON string with cached data
    updated_at VARCHAR                              -- ISO timestamp of last update
);
```

## Data Types

### String Storage
- **VARCHAR**: Used for all string fields including enum values
- **TEXT**: Used for longer text fields (message, details, pattern, description)

### Integer Storage
- **INTEGER**: Used for numeric fields (id, ports, packet counts)

### Enum Storage Strategy
Since SQLite doesn't support native enums:
1. **Storage**: Enum values are stored as `VARCHAR` (strings)
2. **Validation**: Python enums validate values at application level
3. **Conversion**: API converts database strings to enum objects for validation
4. **Backward Compatibility**: Invalid enum values are passed through as-is

## Relationships

- **No foreign keys**: SQLite is used in a simple, denormalized way
- **Alerts are independent**: Each alert is a standalone record
- **Signatures are independent**: Each signature is a standalone rule

## Indexes for Performance

All frequently queried fields have indexes:
- `timestamp` - For time-based queries
- `type` - For filtering by alert type
- `status` - For filtering by alert status
- `subtype` - For filtering by behavior subtype
- `src_ip` - For filtering by source IP

## Notes

1. **Enum Values**: Stored as strings but validated using Python enums
2. **JSON Fields**: `details` field stores JSON as text (SQLite doesn't have native JSON)
3. **Timestamps**: All timestamps stored as ISO format strings
4. **Nullable Fields**: Most lifecycle fields are nullable (only populated for specific statuses)
5. **Default Values**: `severity` defaults to `'MEDIUM'`, `action` defaults to `'alert'`
