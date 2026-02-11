import json
import logging
import os
import time
from datetime import datetime
from collections import defaultdict
from enum import Enum

# Import database integration
from db_integration import db_integration


class AlertType(str, Enum):
    """High-level alert types."""
    SIGNATURE = "SIGNATURE"
    BEHAVIOR = "BEHAVIOR"
    SYSTEM = "SYSTEM"


class AlertSubtype(str, Enum):
    """Sub-categories for behavior alerts."""
    PORT_SCAN = "PORT_SCAN"
    TCP_FLOOD = "TCP_FLOOD"
    UDP_FLOOD = "UDP_FLOOD"
    ICMP_FLOOD = "ICMP_FLOOD"

class LokiLogger:
    """
    Handles logging of IDS alerts to both console and a structured JSONL file.
    NOW WITH: Alert aggregation to prevent log flooding during attacks.
    """
    def __init__(self, log_dir="logs", filename="loki_alerts.jsonl"):
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.log_dir = os.path.join(project_root, log_dir)
        
        self.filename = filename
        self.filepath = os.path.join(self.log_dir, self.filename)
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except Exception as e:
                print(f"[!] couldn't create the log directory: {e}")
                self.log_dir = current_dir # I will just work on the current directory.
        
        # Setup Python's built-in logging for console output
        self.console_logger = logging.getLogger("LokiIDS")
        self.console_logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers if re-initialized
        if not self.console_logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.console_logger.addHandler(ch)
        
        # ===== NEW: Alert Aggregation =====
        # Track active alerts to prevent flooding
        self.active_alerts = {}  # Key: (type, src, dst, port) -> Alert state
        
        # Configuration
        self.alert_cooldown = 10      # Seconds - attack considered "ended" after this
        self.update_interval = 5      # Seconds - log updates during ongoing attacks
        self.max_updates = 3          # Max number of "ONGOING" logs per attack
        
        # Statistics
        self.suppressed_count = 0     # How many duplicate alerts we prevented
    
    def log_alert(self, alert_type, src_ip, dst_ip, src_port, dst_port, message, details=None, subtype=None, pattern=None):
        """
        Logs an alert with smart deduplication.
        
        Args:
            alert_type (AlertType or str): "SIGNATURE", "BEHAVIOR", or "SYSTEM".
            src_ip (str): The attacker's IP address.
            dst_ip (str): The victim's IP address.
            src_port (int): Source port.
            dst_port (int): Destination port.
            message (str): A human-readable description (e.g., "Port Scan Detected").
            details (dict, optional): Extra data (e.g., ports scanned, payload snippet).
            subtype (AlertSubtype or str, optional): Sub-category of alert (e.g., "PORT_SCAN", "TCP_FLOOD", "UDP_FLOOD", "ICMP_FLOOD").
            pattern (str, optional): Pattern for SIGNATURE alerts (e.g., "UNION SELECT", "<script>").
        """
        # Convert enum to string if needed
        if isinstance(alert_type, AlertType):
            alert_type = alert_type.value
        if isinstance(subtype, AlertSubtype):
            subtype = subtype.value
        
        # Extract pattern from details if not provided and it's a SIGNATURE alert
        if pattern is None and alert_type == "SIGNATURE" and details and "pattern" in details:
            pattern = details.get("pattern")
        # Create unique key for this type of alert
        # For port scans: group by (type, src_ip, dst_ip)
        # For floods: group by (type, src_ip, dst_ip, dst_port)
        if "Port Scan" in message or "Scan" in message:
            alert_key = (alert_type, message, src_ip, dst_ip, "scan")
        else:
            alert_key = (alert_type, message, src_ip, dst_ip, dst_port)
        
        current_time = time.time()
        
        # Check if this is a new or ongoing alert
        if alert_key not in self.active_alerts:
            # NEW ALERT - Log it!
            self._log_new_alert(alert_key, alert_type, src_ip, dst_ip, src_port, 
                              dst_port, message, details, current_time, subtype, pattern)
        else:
            # ONGOING ALERT - Handle smartly
            self._handle_ongoing_alert(alert_key, alert_type, src_ip, dst_ip, 
                                       src_port, dst_port, message, details, current_time, subtype, pattern)
    
    def _log_new_alert(self, alert_key, alert_type, src_ip, dst_ip, src_port, 
                       dst_port, message, details, timestamp, subtype=None, pattern=None):
        """Log the FIRST occurrence of an alert"""
        
        # Console Output - Emphasized for new attack
        subtype_str = f" [{subtype}]" if subtype else ""
        pattern_str = f" [Pattern: {pattern}]" if pattern else ""
        self.console_logger.warning(
            f"[NEW] [{alert_type}]{subtype_str}{pattern_str} {src_ip}:{src_port} → {dst_ip}:{dst_port} - {message}"
        )
        
        # File Output
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "STARTED",  # NEW field to track lifecycle
            "type": alert_type,
            "subtype": subtype,  # Sub-category of alert (for BEHAVIOR)
            "pattern": pattern,  # Pattern for SIGNATURE alerts
            "src_ip": src_ip,
            "src_port": src_port,
            "dst_ip": dst_ip,
            "dst_port": dst_port,
            "message": message,
            "details": details or {}
        }
        
        self._write_to_file(record)
        
        # Send to Web Interface API if integration is enabled
        if db_integration.enabled:
            db_integration.insert_alert(record)
        
        # Track this alert
        self.active_alerts[alert_key] = {
            'first_seen': timestamp,
            'last_seen': timestamp,
            'last_logged': timestamp,
            'packet_count': 1,
            'update_count': 0,
            'src_port': src_port,
            'dst_port': dst_port,
            'subtype': subtype,
            'pattern': pattern,
            'details': details or {}
        }
    
    def _handle_ongoing_alert(self, alert_key, alert_type, src_ip, dst_ip, 
                             src_port, dst_port, message, details, timestamp, subtype=None, pattern=None):
        """Handle repeated alerts (ongoing attack)"""
        
        alert_state = self.active_alerts[alert_key]
        
        # Update state
        alert_state['last_seen'] = timestamp
        alert_state['packet_count'] += 1
        
        # Merge new details with existing
        if details:
            alert_state['details'].update(details)
        
        # Store subtype if not already set
        if subtype and 'subtype' not in alert_state:
            alert_state['subtype'] = subtype
        
        # Store pattern if not already set
        if pattern and 'pattern' not in alert_state:
            alert_state['pattern'] = pattern
        
        # Check if we should log an update
        time_since_last_log = timestamp - alert_state['last_logged']
        
        if (time_since_last_log >= self.update_interval and 
            alert_state['update_count'] < self.max_updates):
            # Log an ONGOING update
            self._log_ongoing_update(alert_key, alert_type, src_ip, dst_ip, 
                                    src_port, dst_port, message, timestamp, alert_state)
        else:
            # Suppress this duplicate alert
            self.suppressed_count += 1
            # Optionally log to console every N packets
            if alert_state['packet_count'] % 100 == 0:
                self.console_logger.debug(
                    f"[{alert_type}] {src_ip} → {dst_ip}:{dst_port} - "
                    f"{message} ({alert_state['packet_count']} packets)"
                )
    
    def _log_ongoing_update(self, alert_key, alert_type, src_ip, dst_ip, 
                           src_port, dst_port, message, timestamp, alert_state):
        """Log periodic updates during ongoing attack"""
        
        duration = timestamp - alert_state['first_seen']
        
        # Console Output
        self.console_logger.warning(
            f"[ONGOING] [{alert_type}] {src_ip}:{src_port} → {dst_ip}:{dst_port} - "
            f"{message} ({alert_state['packet_count']} packets, {duration:.1f}s)"
        )
        
        # File Output
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ONGOING",
            "type": alert_type,
            "subtype": alert_state.get('subtype'),
            "pattern": alert_state.get('pattern'),
            "src_ip": src_ip,
            "src_port": src_port,
            "dst_ip": dst_ip,
            "dst_port": dst_port,
            "message": message,
            "duration_seconds": round(duration, 2),
            "packet_count": alert_state['packet_count'],
            "attack_rate_pps": round(alert_state['packet_count'] / duration, 1) if duration > 0 else 0,
            "details": alert_state['details']
        }
        
        self._write_to_file(record)
        
        # Send to Web Interface API if integration is enabled
        if db_integration.enabled:
            db_integration.insert_alert(record)
        
        # Update tracking
        alert_state['last_logged'] = timestamp
        alert_state['update_count'] += 1
    
    def check_ended_alerts(self):
        """
        Check for attacks that have ended.
        Call this periodically (e.g., every 1-2 seconds) from your main IDS loop.
        """
        current_time = time.time()
        ended_alerts = []
        
        for alert_key, alert_state in self.active_alerts.items():
            # Check if attack has been inactive for cooldown period
            time_since_last = current_time - alert_state['last_seen']
            
            if time_since_last >= self.alert_cooldown:
                self._log_ended_alert(alert_key, alert_state, current_time)
                ended_alerts.append(alert_key)
        
        # Remove ended alerts
        for key in ended_alerts:
            del self.active_alerts[key]
        
        return len(ended_alerts)
    
    def _log_ended_alert(self, alert_key, alert_state, timestamp):
        """Log when an attack ends"""
        
        alert_type, message, src_ip, dst_ip, dst_port_or_scan = alert_key
        
        total_duration = alert_state['last_seen'] - alert_state['first_seen']
        
        # Console Output
        self.console_logger.info(
            f"ENDED] [{alert_type}] {src_ip} → {dst_ip} - {message} "
            f"(Total: {alert_state['packet_count']} packets, {total_duration:.1f}s)"
        )
        
        # File Output - Comprehensive summary
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ENDED",
            "type": alert_type,
            "subtype": alert_state.get('subtype'),
            "pattern": alert_state.get('pattern'),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": alert_state.get('src_port', 0),
            "dst_port": alert_state.get('dst_port', 0),
            "message": message,
            "total_duration_seconds": round(total_duration, 2),
            "total_packets": alert_state['packet_count'],
            "average_rate_pps": round(alert_state['packet_count'] / total_duration, 1) if total_duration > 0 else 0,
            "first_seen": datetime.fromtimestamp(alert_state['first_seen']).isoformat(),
            "last_seen": datetime.fromtimestamp(alert_state['last_seen']).isoformat(),
            "details": alert_state['details']
        }
        
        self._write_to_file(record)
        
        # Send to Web Interface API if integration is enabled
        if db_integration.enabled:
            db_integration.insert_alert(record)
    
    def _write_to_file(self, record):
        """Write JSON record to log file"""
        try:
            with open(self.filepath, 'a') as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            self.console_logger.error(f"Failed to write to log file: {e}")
    
    def get_stats(self):
        """Get logging statistics"""
        return {
            'active_alerts': len(self.active_alerts),
            'suppressed_alerts': self.suppressed_count,
            'suppression_rate': f"{(self.suppressed_count / max(1, self.suppressed_count + len(self.active_alerts))) * 100:.1f}%"
        }
    
    def log_system_event(self, message, level="INFO"):
        """
        Log non-alert system events (startup, shutdown, errors, etc.)
        """
        if level == "ERROR":
            self.console_logger.error(message)
        elif level == "WARNING":
            self.console_logger.warning(message)
        else:
            self.console_logger.info(message)
        
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": None,  # SYSTEM events don't have status
            "type": "SYSTEM",
            "subtype": None,
            "pattern": None,
            "src_ip": "system",
            "dst_ip": None,
            "src_port": None,
            "dst_port": None,
            "message": message,
            "details": {"level": level}
        }
        
        self._write_to_file(record)
        
        # Send to Web Interface API if integration is enabled
        if db_integration.enabled:
            db_integration.insert_alert(record)

# Create a singleton instance for easy import
logger = LokiLogger()