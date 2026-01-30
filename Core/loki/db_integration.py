"""
Database integration for Loki Logger.
Allows the logger to write alerts directly to the database.
"""
import os
import sys
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

# Add Web-Interface to path to import database modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
web_interface_path = os.path.join(project_root, "Web-Interface")
if web_interface_path not in sys.path:
    sys.path.insert(0, web_interface_path)

from api.models.database import AsyncSessionLocal
from api.models.crud import create_alert, get_signatures


class DatabaseIntegration:
    """
    Handles database operations for the logger.
    Uses asyncio to run async database operations from sync context.
    """
    def __init__(self):
        self.enabled = False
        self.loop = None
        self._loop_thread = None
        
    def enable(self):
        """Enable database integration."""
        try:
            # Try to get or create an event loop
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in current thread, create a new one
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            
            self.enabled = True
            print("[*] Database integration enabled")
            return True
        except Exception as e:
            print(f"[!] Failed to enable database integration: {e}")
            return False
    
    def disable(self):
        """Disable database integration."""
        self.enabled = False
        if self.loop and not self.loop.is_closed():
            # Don't close the loop, just mark as disabled
            pass
    
    async def _insert_alert_async(self, alert_data: Dict[str, Any]) -> bool:
        """Async function to insert alert into database."""
        try:
            async with AsyncSessionLocal() as session:
                # Convert details dict to JSON string if it exists
                if 'details' in alert_data and isinstance(alert_data['details'], dict):
                    alert_data['details'] = json.dumps(alert_data['details'])
                
                # Convert numeric fields to strings for database (as per schema)
                if 'duration_seconds' in alert_data and alert_data['duration_seconds'] is not None:
                    alert_data['duration_seconds'] = str(alert_data['duration_seconds'])
                if 'attack_rate_pps' in alert_data and alert_data['attack_rate_pps'] is not None:
                    alert_data['attack_rate_pps'] = str(alert_data['attack_rate_pps'])
                if 'total_duration_seconds' in alert_data and alert_data['total_duration_seconds'] is not None:
                    alert_data['total_duration_seconds'] = str(alert_data['total_duration_seconds'])
                if 'average_rate_pps' in alert_data and alert_data['average_rate_pps'] is not None:
                    alert_data['average_rate_pps'] = str(alert_data['average_rate_pps'])
                
                await create_alert(session, alert_data)
                return True
        except Exception as e:
            print(f"[!] Failed to insert alert into database: {e}")
            return False
    
    async def _get_signatures_async(self, enabled_only: bool = True) -> list:
        """Async function to get signatures from database."""
        try:
            async with AsyncSessionLocal() as session:
                signatures, _ = await get_signatures(session, enabled_only=enabled_only, limit=10000)
                return [
                    {
                        'name': sig.name,
                        'pattern': sig.pattern,
                        'action': sig.action,
                        'description': sig.description or '',
                        'enabled': bool(sig.enabled)
                    }
                    for sig in signatures
                ]
        except Exception as e:
            print(f"[!] Failed to get signatures from database: {e}")
            return []
    
    def get_signatures(self, enabled_only: bool = True) -> list:
        """
        Get signatures from database (synchronous wrapper for async operation).
        Returns list of signature dicts with keys: name, pattern, action, description, enabled
        """
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in this thread, create a new one in a thread
                import threading
                result_container = []
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(self._get_signatures_async(enabled_only))
                    result_container.append(result)
                    new_loop.close()
                
                thread = threading.Thread(target=run_in_thread, daemon=False)
                thread.start()
                thread.join()
                return result_container[0] if result_container else []
            
            # If loop is running, we need to use a thread
            if loop.is_running():
                import threading
                result_container = []
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(self._get_signatures_async(enabled_only))
                    result_container.append(result)
                    new_loop.close()
                
                thread = threading.Thread(target=run_in_thread, daemon=False)
                thread.start()
                thread.join()
                return result_container[0] if result_container else []
            else:
                # If loop is not running, run it
                return loop.run_until_complete(self._get_signatures_async(enabled_only))
        except Exception as e:
            print(f"[!] Error getting signatures from database: {e}")
            return []
    
    def insert_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Insert alert into database (synchronous wrapper for async operation).
        This can be called from the synchronous logger.
        Uses a background thread with its own event loop to avoid blocking.
        """
        if not self.enabled:
            return False
        
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in this thread, create a new one in a thread
                import threading
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(self._insert_alert_async(alert_data))
                    new_loop.close()
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                return True
            
            # If loop is running, schedule in background thread
            if loop.is_running():
                import threading
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(self._insert_alert_async(alert_data))
                    new_loop.close()
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                return True
            else:
                # If loop is not running, run it
                loop.run_until_complete(self._insert_alert_async(alert_data))
                return True
        except Exception as e:
            print(f"[!] Error inserting alert into database: {e}")
            return False


# Global instance
db_integration = DatabaseIntegration()
