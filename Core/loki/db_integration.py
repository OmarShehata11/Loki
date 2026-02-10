"""
API integration for Loki Logger.
Sends alerts to the Web Interface API instead of directly accessing the database.
This prevents database locking issues.
"""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


class DatabaseIntegration:
    """
    Handles API communication for the logger.
    Sends alerts to the Web Interface API via HTTP POST.
    """
    def __init__(self, api_base_url: str = "http://localhost:8080/api"):
        self.enabled = False
        self.api_base_url = api_base_url.rstrip('/')
        self.alerts_endpoint = f"{self.api_base_url}/alerts"
        self.signatures_endpoint = f"{self.api_base_url}/signatures"

    def enable(self):
        """Enable API integration."""
        try:
            # Test if API is reachable
            req = urllib.request.Request(
                f"{self.api_base_url}/system/health",
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    self.enabled = True
                    print(f"[*] API integration enabled (API: {self.api_base_url})")
                    return True
        except Exception as e:
            print(f"[!] Failed to enable API integration: {e}")
            print(f"[!] Make sure Web Interface is running at {self.api_base_url}")
            return False

    def disable(self):
        """Disable API integration."""
        self.enabled = False
        print("[*] API integration disabled")

    def insert_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send alert to Web Interface API via HTTP POST.
        Non-blocking - returns immediately without waiting for response.
        """
        if not self.enabled:
            return False

        try:
            # Convert details dict to JSON string if needed
            if 'details' in alert_data and isinstance(alert_data['details'], dict):
                # Keep as dict, API will handle conversion
                pass

            # Prepare JSON payload
            payload = json.dumps(alert_data).encode('utf-8')

            # Create HTTP POST request
            req = urllib.request.Request(
                self.alerts_endpoint,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                method='POST'
            )

            # Send request (non-blocking with short timeout)
            try:
                with urllib.request.urlopen(req, timeout=1) as response:
                    if response.status in (200, 201):
                        return True
                    else:
                        print(f"[!] API returned status {response.status}")
                        return False
            except urllib.error.URLError as e:
                # Timeout or connection error - don't block IDS
                print(f"[!] Failed to send alert to API (non-blocking): {e}")
                return False

        except Exception as e:
            print(f"[!] Error sending alert to API: {e}")
            return False

    def get_signatures(self, enabled_only: bool = True) -> list:
        """
        Get signatures from Web Interface API via HTTP GET.
        Returns list of signature dicts with keys: name, pattern, action, description, enabled
        """
        if not self.enabled:
            return []

        try:
            # Build URL with query parameters
            url = f"{self.signatures_endpoint}?page=1&page_size=10000"
            if enabled_only:
                url += "&enabled=true"

            # Create HTTP GET request
            req = urllib.request.Request(url, method='GET')

            # Send request
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    signatures = data.get('signatures', [])

                    # Convert to expected format
                    return [
                        {
                            'name': sig.get('name', ''),
                            'pattern': sig.get('pattern', ''),
                            'action': sig.get('action', 'alert'),
                            'description': sig.get('description', ''),
                            'enabled': sig.get('enabled', False)
                        }
                        for sig in signatures
                    ]
                else:
                    print(f"[!] Failed to get signatures from API: HTTP {response.status}")
                    return []

        except Exception as e:
            print(f"[!] Error getting signatures from API: {e}")
            return []


# Global instance
db_integration = DatabaseIntegration()