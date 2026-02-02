"""
MQTT Client for IoT Device Control
Handles communication with ESP32 devices via MQTT broker
"""
import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("paho-mqtt not installed. IoT features will be disabled.")

logger = logging.getLogger(__name__)


class MQTTClient:
    """Async MQTT client wrapper for IoT device communication."""
    
    def __init__(
        self,
        broker_host: str = "10.0.0.1",
        broker_port: int = 1883,
        client_id: str = "loki_ids_controller"
    ):
        if not MQTT_AVAILABLE:
            raise RuntimeError("paho-mqtt library is not installed")
        
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_callbacks: Dict[str, Callable] = {}
        self.loop = None
        self.loop_thread = None
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to sensor topics
            client.subscribe("esp32/sensor1")  # Motion sensor
            client.subscribe("esp32/status")   # Device status
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Try to parse as JSON
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {"raw": payload}
            
            # Store in database asynchronously (non-blocking)
            self._store_message_async(topic, data)
            
            # Call registered callbacks
            if topic in self.message_callbacks:
                self.message_callbacks[topic](topic, data)
            else:
                logger.debug(f"Received message on {topic}: {data}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _store_message_async(self, topic: str, data: dict):
        """Store MQTT message in database asynchronously (non-blocking)."""
        # This is called from MQTT callback thread, so we'll just log
        # Database storage will be handled by API endpoints or background tasks
        # to avoid threading issues with async database operations
        logger.debug(f"Received MQTT message on {topic}: {data}")
    
    def register_callback(self, topic: str, callback: Callable):
        """Register a callback for a specific MQTT topic."""
        self.message_callbacks[topic] = callback
        logger.info(f"Registered callback for topic: {topic}")
    
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        if not MQTT_AVAILABLE:
            logger.error("MQTT library not available")
            return False
        
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start network loop in a separate thread
            self.client.loop_start()
            
            # Wait a bit for connection
            import time
            time.sleep(1)
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0) -> bool:
        """Publish a message to an MQTT topic."""
        if not self.connected or not self.client:
            logger.warning("MQTT client not connected. Cannot publish message.")
            return False
        
        try:
            # Convert payload to JSON if it's a dict
            if isinstance(payload, dict):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)
            
            result = self.client.publish(topic, payload_str, qos=qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload_str}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}. Error code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing MQTT message: {e}")
            return False
    
    def send_rgb_command(self, device_id: str, color: str, brightness: int = 255, effect: str = "solid") -> bool:
        """Send RGB LED control command to ESP32-2."""
        topic = "rpi/broadcast"
        payload = {
            "device": device_id,
            "command": "rgb_control",
            "color": color,  # Hex color like "#FF0000"
            "brightness": brightness,
            "effect": effect,  # "solid", "fade", "rainbow", etc.
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.publish(topic, payload)
    
    def send_alarm_command(self, device_id: str, action: str) -> bool:
        """Send alarm control command to ESP32-1."""
        topic = "rpi/broadcast"
        payload = {
            "device": device_id,
            "command": "alarm_control",
            "action": action,  # "enable", "disable", "test"
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.publish(topic, payload)
    
    def send_buzzer_command(self, device_id: str, action: str, duration: int = 1000) -> bool:
        """Send buzzer control command to ESP32-1."""
        topic = "rpi/broadcast"
        payload = {
            "device": device_id,
            "command": "buzzer_control",
            "action": action,  # "on", "off", "beep"
            "duration": duration,  # Duration in milliseconds for beep
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.publish(topic, payload)
    
    def is_connected(self) -> bool:
        """Check if client is connected to broker."""
        return self.connected


# Global MQTT client instance
_mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client(broker_host: str = "127.0.0.1", broker_port: int = 1883) -> Optional[MQTTClient]:
    """Get or create the global MQTT client instance."""
    global _mqtt_client
    
    if not MQTT_AVAILABLE:
        return None
    
    if _mqtt_client is None:
        _mqtt_client = MQTTClient(broker_host=broker_host, broker_port=broker_port)
    
    return _mqtt_client


def initialize_mqtt(broker_host: str = "127.0.0.1", broker_port: int = 1883) -> bool:
    """Initialize and connect the MQTT client."""
    client = get_mqtt_client(broker_host, broker_port)
    if client:
        return client.connect()
    return False


def shutdown_mqtt():
    """Shutdown the MQTT client."""
    global _mqtt_client
    if _mqtt_client:
        _mqtt_client.disconnect()
        _mqtt_client = None
