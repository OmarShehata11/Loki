"""
MQTT Client for IoT Device Control
Handles communication with ESP32 devices via MQTT broker
Compatible with paho-mqtt 2.x API
"""
import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
    MQTT_AVAILABLE = True
    MQTT_V2 = True
except ImportError:
    try:
        # Fallback for older paho-mqtt 1.x
        import paho.mqtt.client as mqtt
        MQTT_AVAILABLE = True
        MQTT_V2 = False
    except ImportError:
        MQTT_AVAILABLE = False
        MQTT_V2 = False
        logging.warning("paho-mqtt not installed. IoT features will be disabled.")

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client wrapper for IoT device communication. Compatible with paho-mqtt 2.x."""
    
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
        self._connection_lock = False
        
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback for when the client connects to the broker (paho-mqtt 2.x API)."""
        # Handle both paho-mqtt 1.x (rc as int) and 2.x (reason_code object)
        if MQTT_V2:
            success = reason_code == 0 or (hasattr(reason_code, 'is_failure') and not reason_code.is_failure)
            rc_value = int(reason_code) if hasattr(reason_code, '__int__') else reason_code
        else:
            success = reason_code == 0
            rc_value = reason_code
            
        if success:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to sensor topics for receiving device status
            client.subscribe("esp32/sensor1/status")  # Motion sensor status
            client.subscribe("esp32/sensor2/status")  # RGB controller status
            client.subscribe("esp32/+/status")        # All device status
            logger.info("Subscribed to ESP32 device status topics")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc_value}")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        """Callback for when the client disconnects from the broker (paho-mqtt 2.x API)."""
        self.connected = False
        
        # Handle both paho-mqtt 1.x and 2.x
        if MQTT_V2:
            rc_value = int(reason_code) if hasattr(reason_code, '__int__') else reason_code
        else:
            # In paho-mqtt 1.x, the signature is (client, userdata, rc)
            # 'flags' is actually 'rc' in that case
            rc_value = flags if isinstance(flags, int) else 0
        
        if rc_value == 0:
            logger.info("Disconnected from MQTT broker: Normal disconnection")
        else:
            logger.warning(f"Disconnected from MQTT broker unexpectedly (code: {rc_value}). Will attempt to reconnect...")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received MQTT message on {topic}: {payload[:100]}...")
            
            # Try to parse as JSON
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {"raw": payload}
            
            # Call registered callbacks
            if topic in self.message_callbacks:
                self.message_callbacks[topic](topic, data)
            else:
                logger.debug(f"No callback registered for topic {topic}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def register_callback(self, topic: str, callback: Callable):
        """Register a callback for a specific MQTT topic."""
        self.message_callbacks[topic] = callback
        logger.info(f"Registered callback for topic: {topic}")
    
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        if not MQTT_AVAILABLE:
            logger.error("MQTT library not available")
            return False
        
        # Prevent concurrent connection attempts
        if self._connection_lock:
            logger.warning("Connection already in progress")
            return self.connected
        
        self._connection_lock = True
        
        try:
            # Disconnect existing client if any
            if self.client:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except:
                    pass
                self.client = None
                self.connected = False
            
            # Create client with paho-mqtt 2.x API
            if MQTT_V2:
                self.client = mqtt.Client(
                    callback_api_version=CallbackAPIVersion.VERSION2,
                    client_id=self.client_id,
                    clean_session=True
                )
            else:
                # Fallback for paho-mqtt 1.x
                self.client = mqtt.Client(client_id=self.client_id)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Enable automatic reconnection
            self.client.reconnect_delay_set(min_delay=1, max_delay=30)
            
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            
            # Connect with keepalive
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Start network loop in background thread
            self.client.loop_start()
            
            # Wait for connection to establish
            import time
            for i in range(30):  # Wait up to 3 seconds
                if self.connected:
                    logger.info("MQTT connection established successfully")
                    return True
                time.sleep(0.1)
            
            if not self.connected:
                logger.warning(f"Connection timeout - broker at {self.broker_host}:{self.broker_port} may be unreachable")
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            return False
        finally:
            self._connection_lock = False
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connected = False
                self.client = None
            logger.info("Disconnected from MQTT broker")
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        """Publish a message to an MQTT topic."""
        if not self.client:
            logger.warning("MQTT client not initialized. Cannot publish message.")
            return False
        
        if not self.connected:
            logger.warning("MQTT client not connected. Attempting to reconnect...")
            # Try to reconnect
            if not self.connect():
                logger.error("Failed to reconnect. Cannot publish message.")
                return False
        
        try:
            # Convert payload to JSON if it's a dict
            if isinstance(payload, dict):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)
            
            logger.info(f"Publishing to {topic}: {payload_str}")
            
            result = self.client.publish(topic, payload_str, qos=qos)
            
            # Wait for publish to complete (with timeout)
            result.wait_for_publish(timeout=5.0)
            
            if result.is_published():
                logger.info(f"✓ Successfully published to {topic}")
                return True
            else:
                logger.error(f"✗ Failed to publish to {topic} - message not confirmed")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing MQTT message: {e}")
            return False
    
    def send_bulb_command(self, device_id: str, state: str, brightness: int = 255) -> bool:
        """Send bulb control command to ESP32-2."""
        topic = "rpi/broadcast"
        payload = {
            "device": device_id,
            "command": "bulb_control",
            "state": state,  # "on" or "off"
            "brightness": brightness,  # 0-255
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Sending bulb command to {device_id}: state={state}, brightness={brightness}")
        result = self.publish(topic, payload)
        if result:
            logger.info(f"✓ Bulb command published successfully to {topic}")
        else:
            logger.error(f"✗ Failed to publish bulb command to {topic}")
        return result
    
    def send_alarm_command(self, device_id: str, action: str) -> bool:
        """Send alarm control command to ESP32-1."""
        topic = "rpi/broadcast"
        payload = {
            "device": device_id,
            "command": "alarm_control",
            "action": action,  # "enable", "disable", "test"
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Sending alarm command to {device_id}: action={action}")
        result = self.publish(topic, payload)
        if result:
            logger.info(f"✓ Alarm command published successfully to {topic}")
        else:
            logger.error(f"✗ Failed to publish alarm command to {topic}")
        return result
    
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
        logger.info(f"Sending buzzer command to {device_id}: action={action}, duration={duration}ms")
        result = self.publish(topic, payload)
        if result:
            logger.info(f"✓ Buzzer command published successfully to {topic}")
        else:
            logger.error(f"✗ Failed to publish buzzer command to {topic}")
        return result
    
    def send_led_command(self, device_id: str, action: str) -> bool:
        """Send LED control command to ESP32-1."""
        topic = "rpi/broadcast"
        payload = {
            "device": device_id,
            "command": "led_control",
            "action": action,  # "on", "off", "auto"
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Sending LED command to {device_id}: action={action}")
        result = self.publish(topic, payload)
        if result:
            logger.info(f"✓ LED command published successfully to {topic}")
        else:
            logger.error(f"✗ Failed to publish LED command to {topic}")
        return result
    
    def is_connected(self) -> bool:
        """Check if client is connected to broker."""
        if not self.client:
            return False
        # Use paho-mqtt's internal connection check if available
        try:
            return self.connected and self.client.is_connected()
        except AttributeError:
            # Fallback for older versions
            return self.connected


# Global MQTT client instance
_mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client(broker_host: str = "127.0.0.1", broker_port: int = 1883) -> Optional[MQTTClient]:
    """Get or create the global MQTT client instance."""
    global _mqtt_client
    
    if not MQTT_AVAILABLE:
        logger.warning("MQTT library not available")
        return None
    
    # If client exists but broker changed, recreate it
    if _mqtt_client is not None:
        if _mqtt_client.broker_host != broker_host or _mqtt_client.broker_port != broker_port:
            logger.info(f"Broker changed from {_mqtt_client.broker_host}:{_mqtt_client.broker_port} to {broker_host}:{broker_port}")
            _mqtt_client.disconnect()
            _mqtt_client = None
    
    if _mqtt_client is None:
        logger.info(f"Creating new MQTT client for {broker_host}:{broker_port}")
        _mqtt_client = MQTTClient(broker_host=broker_host, broker_port=broker_port)
    
    return _mqtt_client


def initialize_mqtt(broker_host: str = "127.0.0.1", broker_port: int = 1883) -> bool:
    """Initialize and connect the MQTT client."""
    logger.info(f"Initializing MQTT connection to {broker_host}:{broker_port}")
    client = get_mqtt_client(broker_host, broker_port)
    if client:
        success = client.connect()
        if success:
            logger.info(f"MQTT client successfully connected to {broker_host}:{broker_port}")
        else:
            logger.warning(f"MQTT client failed to connect to {broker_host}:{broker_port}")
        return success
    return False


def shutdown_mqtt():
    """Shutdown the MQTT client."""
    global _mqtt_client
    logger.info("Shutting down MQTT client")
    if _mqtt_client:
        _mqtt_client.disconnect()
        _mqtt_client = None
