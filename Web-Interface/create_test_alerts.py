#!/usr/bin/env python3
"""
Script to create test alerts in the database for dashboard testing.
"""
import asyncio
import json
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.models.database import get_db, init_db
from api.models import crud


async def create_test_alerts():
    """Create various test alerts for dashboard testing."""
    # Initialize database
    await init_db()
    
    # Get database session
    async for db in get_db():
        print("[*] Creating test alerts...")
        
        # Current time
        now = datetime.utcnow()
        
        # Test alerts data
        test_alerts = [
            # BEHAVIOR - PORT_SCAN - STARTED
            {
                "timestamp": (now - timedelta(minutes=5)).isoformat(),
                "status": "STARTED",
                "type": "BEHAVIOR",
                "subtype": "PORT_SCAN",
                "src_ip": "192.168.1.100",
                "dst_ip": "192.168.1.1",
                "src_port": 54321,
                "dst_port": 80,
                "message": "Port Scan Detected on INPUT chain",
                "details": json.dumps({
                    "dst_ip": "192.168.1.1",
                    "dst_port": 80,
                    "chain": "INPUT"
                }),
                "severity": "MEDIUM"
            },
            
            # BEHAVIOR - TCP_FLOOD - ONGOING
            {
                "timestamp": (now - timedelta(minutes=3)).isoformat(),
                "status": "ONGOING",
                "type": "BEHAVIOR",
                "subtype": "TCP_FLOOD",
                "src_ip": "10.0.0.50",
                "dst_ip": "10.0.0.1",
                "src_port": 12345,
                "dst_port": 443,
                "message": "TCP Flood (DoS/DDoS) Detected on FORWARD chain",
                "details": json.dumps({
                    "dst_ip": "10.0.0.1",
                    "dst_port": 443,
                    "chain": "FORWARD"
                }),
                "severity": "HIGH",
                "duration_seconds": "180.5",
                "packet_count": 12500,
                "attack_rate_pps": "69.2"
            },
            
            # BEHAVIOR - UDP_FLOOD - ENDED
            {
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "status": "ENDED",
                "type": "BEHAVIOR",
                "subtype": "UDP_FLOOD",
                "src_ip": "172.16.0.10",
                "dst_ip": "172.16.0.1",
                "src_port": 54321,
                "dst_port": 53,
                "message": "UDP Flood (DoS/DDoS) Detected on INPUT chain",
                "details": json.dumps({
                    "dst_ip": "172.16.0.1",
                    "dst_port": 53,
                    "chain": "INPUT"
                }),
                "severity": "HIGH",
                "total_duration_seconds": "300.0",
                "total_packets": 25000,
                "average_rate_pps": "83.3",
                "first_seen": (now - timedelta(minutes=15)).isoformat(),
                "last_seen": (now - timedelta(minutes=10)).isoformat()
            },
            
            # BEHAVIOR - ICMP_FLOOD - STARTED
            {
                "timestamp": (now - timedelta(minutes=1)).isoformat(),
                "status": "STARTED",
                "type": "BEHAVIOR",
                "subtype": "ICMP_FLOOD",
                "src_ip": "203.0.113.5",
                "dst_ip": "203.0.113.1",
                "src_port": 0,
                "dst_port": 0,
                "message": "ICMP Flood (DoS/DDoS) Detected on INPUT chain",
                "details": json.dumps({
                    "dst_ip": "203.0.113.1",
                    "chain": "INPUT"
                }),
                "severity": "MEDIUM"
            },
            
            # BEHAVIOR - PORT_SCAN - ONGOING
            {
                "timestamp": (now - timedelta(minutes=8)).isoformat(),
                "status": "ONGOING",
                "type": "BEHAVIOR",
                "subtype": "PORT_SCAN",
                "src_ip": "198.51.100.20",
                "dst_ip": "198.51.100.1",
                "src_port": 45678,
                "dst_port": 22,
                "message": "Port Scan Detected on FORWARD chain",
                "details": json.dumps({
                    "dst_ip": "198.51.100.1",
                    "dst_port": 22,
                    "chain": "FORWARD"
                }),
                "severity": "MEDIUM",
                "duration_seconds": "480.0",
                "packet_count": 500,
                "attack_rate_pps": "1.0"
            },
            
            # SIGNATURE - With pattern
            {
                "timestamp": (now - timedelta(minutes=2)).isoformat(),
                "status": "STARTED",
                "type": "SIGNATURE",
                "subtype": None,
                "pattern": "UNION SELECT",
                "src_ip": "192.168.1.200",
                "dst_ip": "192.168.1.1",
                "src_port": 49152,
                "dst_port": 80,
                "message": "Signature Match: SQL Injection - Union Select",
                "details": json.dumps({
                    "pattern": "UNION SELECT",
                    "action": "ALERT",
                    "chain": "INPUT"
                }),
                "severity": "HIGH"
            },
            
            # SIGNATURE - With pattern
            {
                "timestamp": (now - timedelta(minutes=12)).isoformat(),
                "status": "ENDED",
                "type": "SIGNATURE",
                "subtype": None,
                "pattern": "<script>",
                "src_ip": "10.0.0.100",
                "dst_ip": "10.0.0.1",
                "src_port": 49153,
                "dst_port": 443,
                "message": "Signature Match: XSS - Script Tag",
                "details": json.dumps({
                    "pattern": "<script>",
                    "action": "ALERT",
                    "chain": "FORWARD"
                }),
                "severity": "MEDIUM"
            },
            
            # BEHAVIOR - TCP_FLOOD - ENDED
            {
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "status": "ENDED",
                "type": "BEHAVIOR",
                "subtype": "TCP_FLOOD",
                "src_ip": "172.16.0.50",
                "dst_ip": "172.16.0.1",
                "src_port": 12346,
                "dst_port": 8080,
                "message": "TCP Flood (DoS/DDoS) Detected on FORWARD chain",
                "details": json.dumps({
                    "dst_ip": "172.16.0.1",
                    "dst_port": 8080,
                    "chain": "FORWARD"
                }),
                "severity": "CRITICAL",
                "total_duration_seconds": "600.0",
                "total_packets": 50000,
                "average_rate_pps": "83.3",
                "first_seen": (now - timedelta(minutes=30)).isoformat(),
                "last_seen": (now - timedelta(minutes=20)).isoformat()
            },
            
            # BEHAVIOR - UDP_FLOOD - ONGOING
            {
                "timestamp": (now - timedelta(minutes=4)).isoformat(),
                "status": "ONGOING",
                "type": "BEHAVIOR",
                "subtype": "UDP_FLOOD",
                "src_ip": "203.0.113.10",
                "dst_ip": "203.0.113.1",
                "src_port": 54322,
                "dst_port": 53,
                "message": "UDP Flood (DoS/DDoS) Detected on INPUT chain",
                "details": json.dumps({
                    "dst_ip": "203.0.113.1",
                    "dst_port": 53,
                    "chain": "INPUT"
                }),
                "severity": "HIGH",
                "duration_seconds": "240.0",
                "packet_count": 20000,
                "attack_rate_pps": "83.3"
            },
            
            # BEHAVIOR - ICMP_FLOOD - ENDED
            {
                "timestamp": (now - timedelta(minutes=15)).isoformat(),
                "status": "ENDED",
                "type": "BEHAVIOR",
                "subtype": "ICMP_FLOOD",
                "src_ip": "198.51.100.30",
                "dst_ip": "198.51.100.1",
                "src_port": 0,
                "dst_port": 0,
                "message": "ICMP Flood (DoS/DDoS) Detected on FORWARD chain",
                "details": json.dumps({
                    "dst_ip": "198.51.100.1",
                    "chain": "FORWARD"
                }),
                "severity": "MEDIUM",
                "total_duration_seconds": "120.0",
                "total_packets": 5000,
                "average_rate_pps": "41.7",
                "first_seen": (now - timedelta(minutes=17)).isoformat(),
                "last_seen": (now - timedelta(minutes=15)).isoformat()
            },
            
            # SIGNATURE - Multiple
            {
                "timestamp": (now - timedelta(minutes=6)).isoformat(),
                "status": "STARTED",
                "type": "SIGNATURE",
                "subtype": None,
                "pattern": "/etc/passwd",
                "src_ip": "192.168.1.150",
                "dst_ip": "192.168.1.1",
                "src_port": 49154,
                "dst_port": 80,
                "message": "Signature Match: Path Traversal - Etc Passwd",
                "details": json.dumps({
                    "pattern": "/etc/passwd",
                    "action": "ALERT",
                    "chain": "INPUT"
                }),
                "severity": "HIGH"
            },
            
            # More SIGNATURE alerts with different patterns
            {
                "timestamp": (now - timedelta(minutes=9)).isoformat(),
                "status": "STARTED",
                "type": "SIGNATURE",
                "subtype": None,
                "pattern": "OR 1=1",
                "src_ip": "192.168.1.175",
                "dst_ip": "192.168.1.1",
                "src_port": 49155,
                "dst_port": 80,
                "message": "Signature Match: SQL Injection - OR 1=1",
                "details": json.dumps({
                    "pattern": "OR 1=1",
                    "action": "ALERT",
                    "chain": "INPUT"
                }),
                "severity": "HIGH"
            },
            
            {
                "timestamp": (now - timedelta(minutes=11)).isoformat(),
                "status": "ENDED",
                "type": "SIGNATURE",
                "subtype": None,
                "pattern": "javascript:alert",
                "src_ip": "10.0.0.125",
                "dst_ip": "10.0.0.1",
                "src_port": 49156,
                "dst_port": 443,
                "message": "Signature Match: XSS - JavaScript Alert",
                "details": json.dumps({
                    "pattern": "javascript:alert",
                    "action": "ALERT",
                    "chain": "FORWARD"
                }),
                "severity": "MEDIUM"
            },
            
            # SYSTEM event
            {
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "status": None,
                "type": "SYSTEM",
                "subtype": None,
                "src_ip": "127.0.0.1",
                "dst_ip": None,
                "src_port": None,
                "dst_port": None,
                "message": "IDS started successfully",
                "details": json.dumps({
                    "level": "INFO"
                }),
                "severity": "LOW"
            },
            
            # More BEHAVIOR alerts for variety
            {
                "timestamp": (now - timedelta(minutes=7)).isoformat(),
                "status": "ONGOING",
                "type": "BEHAVIOR",
                "subtype": "PORT_SCAN",
                "src_ip": "10.0.0.75",
                "dst_ip": "10.0.0.1",
                "src_port": 45679,
                "dst_port": 3389,
                "message": "Port Scan Detected on INPUT chain",
                "details": json.dumps({
                    "dst_ip": "10.0.0.1",
                    "dst_port": 3389,
                    "chain": "INPUT"
                }),
                "severity": "MEDIUM",
                "duration_seconds": "420.0",
                "packet_count": 300,
                "attack_rate_pps": "0.7"
            },
            
            {
                "timestamp": (now - timedelta(minutes=25)).isoformat(),
                "status": "ENDED",
                "type": "BEHAVIOR",
                "subtype": "TCP_FLOOD",
                "src_ip": "172.16.0.75",
                "dst_ip": "172.16.0.1",
                "src_port": 12347,
                "dst_port": 22,
                "message": "TCP Flood (DoS/DDoS) Detected on INPUT chain",
                "details": json.dumps({
                    "dst_ip": "172.16.0.1",
                    "dst_port": 22,
                    "chain": "INPUT"
                }),
                "severity": "HIGH",
                "total_duration_seconds": "180.0",
                "total_packets": 15000,
                "average_rate_pps": "83.3",
                "first_seen": (now - timedelta(minutes=28)).isoformat(),
                "last_seen": (now - timedelta(minutes=25)).isoformat()
            }
        ]
        
        # Insert alerts
        created_count = 0
        for alert_data in test_alerts:
            try:
                await crud.create_alert(db, alert_data)
                created_count += 1
            except Exception as e:
                print(f"[!] Error creating alert: {e}")
        
        print(f"[+] Successfully created {created_count} test alerts")
        print(f"[*] Alert types: BEHAVIOR (with subtypes), SIGNATURE, SYSTEM")
        print(f"[*] Alert statuses: STARTED, ONGOING, ENDED")
        print(f"[*] You can now test the dashboard UI!")
        break


if __name__ == "__main__":
    asyncio.run(create_test_alerts())
