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
        
        # MQTT return codes
        rc_messages = {
            0: "Normal disconnection",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised",
            7: "Network error - connection lost or timeout",
        }
        
        message = rc_messages.get(rc, f"Unknown error code: {rc}")
        
        if rc == 0:
            logger.info(f"Disconnected from MQTT broker: {message}")
        elif rc == 7:
            logger.warning(f"Disconnected from MQTT broker. {message} (code: {rc})")
            logger.warning("This usually indicates network connectivity issues. Will attempt to reconnect...")
        else:
            logger.error(f"Disconnected from MQTT broker. {message} (code: {rc})")
    
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
            
            # Set keepalive and connection timeout
            # Keepalive: 60 seconds (send ping every 60s)
            # Connection timeout: 30 seconds
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Start network loop in a separate thread
            self.client.loop_start()
            
            # Wait a bit longer for connection to establish
            import time
            time.sleep(2)  # Increased from 1 to 2 seconds
            
            # Check connection state
            if not self.connected:
                # Check if there's a connection error
                state = self.client._state
                if state == mqtt.mqtt_cs_connect_async:
                    logger.warning("Connection in progress, waiting longer...")
                    time.sleep(2)
                elif state == mqtt.mqtt_cs_disconnecting:
                    logger.warning("Connection is disconnecting")
                elif state == mqtt.mqtt_cs_new:
                    logger.warning("Connection not started")
            
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
        return self.connected


# Global MQTT client instance
_mqtt_client: Optional[MQTTClient] = None
_reconnect_thread = None
_reconnect_running = False


def _start_auto_reconnect():
    """Start background thread for automatic reconnection."""
    global _reconnect_thread, _reconnect_running
    
    if _reconnect_running:
        return
    
    _reconnect_running = True
    
    import threading
    import time
    
    def reconnect_loop():
        global _mqtt_client, _reconnect_running
        
        while _reconnect_running:
            time.sleep(10)  # Check every 10 seconds
            
            if _mqtt_client and not _mqtt_client.is_connected():
                logger.info("MQTT disconnected, attempting to reconnect...")
                try:
                    if _mqtt_client.connect():
                        logger.info("Successfully reconnected to MQTT broker")
                    else:
                        logger.warning("Reconnection attempt failed, will retry in 10 seconds")
                except Exception as e:
                    logger.error(f"Error during reconnection: {e}")
    
    _reconnect_thread = threading.Thread(target=reconnect_loop, daemon=True)
    _reconnect_thread.start()
    logger.info("Started MQTT auto-reconnect thread")


def get_mqtt_client(broker_host: str = "127.0.0.1", broker_port: int = 1883) -> Optional[MQTTClient]:
    """Get or create the global MQTT client instance."""
    global _mqtt_client
    
    if not MQTT_AVAILABLE:
        return None
    
    # If client exists but broker changed, recreate it
    if _mqtt_client is not None:
        if _mqtt_client.broker_host != broker_host or _mqtt_client.broker_port != broker_port:
            logger.info(f"Broker changed, recreating MQTT client: {broker_host}:{broker_port}")
            _mqtt_client.disconnect()
            _mqtt_client = None
    
    if _mqtt_client is None:
        _mqtt_client = MQTTClient(broker_host=broker_host, broker_port=broker_port)
        # Start auto-reconnect thread
        _start_auto_reconnect()
    
    return _mqtt_client


def initialize_mqtt(broker_host: str = "127.0.0.1", broker_port: int = 1883) -> bool:
    """Initialize and connect the MQTT client."""
    client = get_mqtt_client(broker_host, broker_port)
    if client:
        return client.connect()
    return False


def shutdown_mqtt():
    """Shutdown the MQTT client."""
    global _mqtt_client, _reconnect_running
    _reconnect_running = False
    if _mqtt_client:
        _mqtt_client.disconnect()
        _mqtt_client = None
