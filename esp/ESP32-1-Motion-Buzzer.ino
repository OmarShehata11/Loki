/*
 * ESP32-1: Motion Sensor & Buzzer Controller
 * Compatible with Loki IDS Web Interface
 * 
 * Features:
 *  - WiFi connection to Raspberry Pi AP
 *  - MQTT connection + reconnect logic
 *  - Subscribes to: rpi/broadcast (for commands)
 *  - Publishes to: esp32/sensor1 (motion events)
 *  - PIR motion sensor on GPIO15
 *  - Buzzer on GPIO3
 *  - LED indicator on GPIO2
 * 
 * Required Libraries:
 *  - WiFi (built-in)
 *  - PubSubClient (install via Library Manager)
 *  - ArduinoJson (install version 6.x via Library Manager)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- START: CONFIGURE YOUR SETTINGS ---
const char* WIFI_SSID = "Access Point";  // Change to your WiFi SSID
const char* WIFI_PASS = "1234Az@1";  // Change to your WiFi password
const char* MQTT_BROKER_IP = "172.16.10.50";  // Raspberry Pi IP (or 127.0.0.1 if same device)
const int   MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-1";
const char* DEVICE_ID = "esp32-1";  // Must match web interface device ID
// --- END: CONFIGURE YOUR SETTINGS ---

// Pin definitions
const int pirPin = 15;      // PIR motion sensor on GPIO15
const int buzzerPin = 3;    // Buzzer on GPIO3
const int ledPin = 2;       // LED on GPIO2 (built-in LED)

// Global Variables
WiFiClient espClient;
PubSubClient client(espClient);
long lastReconnectAttempt = 0;
long lastMotionPublish = 0;

// State variables
int pirState = 0;
int lastPirState = LOW;
unsigned long lastMotionTime = 0;
bool alarmEnabled = false;
bool buzzerState = false;
unsigned long buzzerBeepEndTime = 0;
bool motionDetected = false;

// Function to create alarm sound pattern
void soundAlarm() {
  // First tone (higher frequency)
  for(int i = 0; i < 80; i++) {
    digitalWrite(buzzerPin, HIGH);
    delay(1);
    digitalWrite(buzzerPin, LOW);
    delay(1);
  }
  
  // Second tone (lower frequency)
  for(int i = 0; i < 100; i++) {
    digitalWrite(buzzerPin, HIGH);
    delayMicroseconds(500);
    digitalWrite(buzzerPin, LOW);
    delay(2);
  }
}

// Function to beep buzzer for specified duration
void beepBuzzer(unsigned long duration) {
  buzzerState = true;
  buzzerBeepEndTime = millis() + duration;
  Serial.print("Beeping for ");
  Serial.print(duration);
  Serial.println(" ms");
}

// --- Connect to WiFi ---
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// --- Reconnect to MQTT ---
boolean reconnect_mqtt() {
  Serial.print("Attempting MQTT connection...");
  
  // Ensure WiFi connected
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (client.connect(MQTT_CLIENT_ID)) {
    Serial.println("MQTT Connected");
    // Subscribe to commands from web interface
    client.subscribe("rpi/broadcast");
    Serial.println("Subscribed to: rpi/broadcast");
  } else {
    Serial.print("failed, rc=");
    Serial.print(client.state());
    Serial.println(" trying again in 5 seconds");
  }

  return client.connected();
}

// --- MQTT Callback - Handle commands from web interface ---
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(" | Data: ");
  
  String msg;
  for (int i = 0; i < length; i++) {
    msg += (char)message[i];
  }
  Serial.println(msg);

  // Parse JSON message
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, msg);

  if (error) {
    Serial.print("JSON parse error: ");
    Serial.println(error.c_str());
    return;
  }

  // Check if message is for this device
  const char* device = doc["device"];
  if (device == NULL || strcmp(device, DEVICE_ID) != 0) {
    Serial.println("Message not for this device, ignoring");
    return;
  }

  // Get command type
  const char* command = doc["command"];
  if (command == NULL) {
    Serial.println("No command field found");
    return;
  }

  Serial.print("Processing command: ");
  Serial.println(command);

  // Handle buzzer_control command
  if (strcmp(command, "buzzer_control") == 0) {
    const char* action = doc["action"];
    if (action == NULL) {
      Serial.println("No action field in buzzer_control");
      return;
    }

    if (strcmp(action, "on") == 0) {
      buzzerState = true;
      buzzerBeepEndTime = 0;  // Continuous
      digitalWrite(buzzerPin, HIGH);
      Serial.println("Buzzer ON");
    } 
    else if (strcmp(action, "off") == 0) {
      buzzerState = false;
      buzzerBeepEndTime = 0;
      digitalWrite(buzzerPin, LOW);
      Serial.println("Buzzer OFF");
    } 
    else if (strcmp(action, "beep") == 0) {
      int duration = doc["duration"] | 1000;  // Default 1000ms
      beepBuzzer(duration);
    }
  }
  // Handle alarm_control command
  else if (strcmp(command, "alarm_control") == 0) {
    const char* action = doc["action"];
    if (action == NULL) {
      Serial.println("No action field in alarm_control");
      return;
    }

    if (strcmp(action, "enable") == 0) {
      alarmEnabled = true;
      Serial.println("Alarm ENABLED");
    } 
    else if (strcmp(action, "disable") == 0) {
      alarmEnabled = false;
      Serial.println("Alarm DISABLED");
    } 
    else if (strcmp(action, "test") == 0) {
      Serial.println("Testing alarm...");
      soundAlarm();
      digitalWrite(ledPin, HIGH);
      delay(500);
      digitalWrite(ledPin, LOW);
    }
  }
}

// --- Publish motion event to MQTT ---
void publishMotionEvent(bool detected) {
  StaticJsonDocument<200> doc;
  doc["motion_detected"] = detected;
  doc["timestamp"] = millis();  // You can add proper timestamp if needed

  char buffer[256];
  serializeJson(doc, buffer);
  
  if (client.publish("esp32/sensor1", buffer)) {
    Serial.print("Published motion event: ");
    Serial.println(buffer);
  } else {
    Serial.println("Failed to publish motion event");
  }
}

// --- SETUP ---
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("========================================");
  Serial.println("ESP32-1: Motion Sensor & Buzzer");
  Serial.println("========================================");

  // Setup pins
  pinMode(pirPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  
  digitalWrite(buzzerPin, LOW);
  digitalWrite(ledPin, LOW);
  
  Serial.println("PIR Motion Sensor System Ready");
  Serial.println("Waiting for motion...");

  // Setup WiFi and MQTT
  setup_wifi();
  client.setServer(MQTT_BROKER_IP, MQTT_PORT);
  client.setCallback(callback);
  lastReconnectAttempt = 0;
}

// --- MAIN LOOP ---
void loop() {
  // MQTT reconnect logic
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (!client.connected()) {
    long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      if (reconnect_mqtt()) {
        lastReconnectAttempt = 0;
      }
    }
  } else {
    client.loop();
  }

  // Handle buzzer beep timing
  if (buzzerState && buzzerBeepEndTime > 0) {
    if (millis() >= buzzerBeepEndTime) {
      buzzerState = false;
      digitalWrite(buzzerPin, LOW);
      Serial.println("Beep finished");
    } else {
      digitalWrite(buzzerPin, HIGH);
    }
  } else if (buzzerState && buzzerBeepEndTime == 0) {
    // Continuous ON
    digitalWrite(buzzerPin, HIGH);
  } else {
    digitalWrite(buzzerPin, LOW);
  }

  // Read PIR sensor
  pirState = digitalRead(pirPin);

  // Detect motion state change
  if (pirState == HIGH && lastPirState == LOW) {
    // Motion just detected
    motionDetected = true;
    lastMotionTime = millis();
    Serial.println("MOTION DETECTED!");
    
    // Publish motion event
    if (client.connected()) {
      publishMotionEvent(true);
      lastMotionPublish = millis();
    }

    // Activate alarm if enabled
    if (alarmEnabled) {
      digitalWrite(ledPin, HIGH);
      soundAlarm();
    }
  } 
  else if (pirState == LOW && lastPirState == HIGH) {
    // Motion just stopped
    motionDetected = false;
    Serial.println("Motion stopped");
    
    // Publish motion event
    if (client.connected()) {
      publishMotionEvent(false);
      lastMotionPublish = millis();
    }

    if (!alarmEnabled) {
      digitalWrite(ledPin, LOW);
    }
  }

  // Update LED based on alarm state
  if (alarmEnabled && motionDetected) {
    digitalWrite(ledPin, HIGH);
  } else if (!alarmEnabled) {
    digitalWrite(ledPin, LOW);
  }

  // Publish motion status periodically (every 4 seconds) if motion is still detected
  if (motionDetected && client.connected()) {
    if (millis() - lastMotionPublish > 4000) {
      publishMotionEvent(true);
      lastMotionPublish = millis();
    }
  }

  lastPirState = pirState;
  delay(50);  // Small delay to avoid bouncing
}
