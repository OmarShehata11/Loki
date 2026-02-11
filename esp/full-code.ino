/*
 * ESP32-1: Motion Sensor + Alarm Controller (Entryway Hub)
 * PIR motion sensor with buzzer alarm controlled by Loki IDS Dashboard
 *
 * Features:
 *  - WiFi connection
 *  - MQTT connection + auto-reconnect
 *  - Subscribes to: rpi/broadcast
 *  - Publishes to: esp32/sensor1/status
 *  - PIR motion detection (GPIO 15)
 *  - Buzzer alarm (GPIO 3)
 *  - LED indicator (GPIO 2)
 *  - Dashboard control: alarm_control, buzzer_control, led_control
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- WiFi and MQTT Configuration ---
const char* WIFI_SSID = "MyWiFi";      // TODO: Update with your WiFi SSID
const char* WIFI_PASS = "password";    // TODO: Update with your WiFi password
const char* MQTT_BROKER_IP = "10.0.0.1"; // Raspberry Pi Access Point IP
const int   MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-1";
const char* DEVICE_ID = "esp32-1";  // Must match dashboard

// --- Pin Definitions ---
const int PIR_PIN = 15;         // PIR motion sensor
const int BUZZER_PIN = 3;       // Buzzer
const int LED_PIN = 2;          // Built-in LED

// --- Global Variables ---
WiFiClient espClient;
PubSubClient client(espClient);

long lastReconnectAttempt = 0;
long lastHeartbeat = 0;
unsigned long lastMotionTime = 0;

// System State
bool alarmEnabled = true;       // Alarm can be disabled from dashboard
bool alarmActive = false;       // Currently alarming due to motion
bool buzzerOn = false;
bool ledAutoMode = true;        // Auto mode follows alarm state
const unsigned long alarmDuration = 5000;  // 5 seconds

// --- WiFi Setup ---
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[✓] WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// --- MQTT Reconnect ---
boolean reconnect_mqtt() {
  Serial.print("Attempting MQTT connection...");

  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (client.connect(MQTT_CLIENT_ID)) {
    Serial.println("[✓] MQTT Connected");
    client.subscribe("rpi/broadcast");
    Serial.println("[✓] Subscribed to: rpi/broadcast");
    publishStatus("online");
  } else {
    Serial.print("[✗] Failed, rc=");
    Serial.print(client.state());
    Serial.println(" trying again in 5 seconds");
  }

  return client.connected();
}

// --- Publish Status to Dashboard ---
void publishStatus(const char* event) {
  StaticJsonDocument<256> doc;
  doc["device"] = DEVICE_ID;
  doc["event"] = event;
  doc["alarm_enabled"] = alarmEnabled;
  doc["alarm_active"] = alarmActive;
  doc["buzzer_on"] = buzzerOn;
  doc["led_auto_mode"] = ledAutoMode;

  char buffer[256];
  serializeJson(doc, buffer);

  client.publish("esp32/sensor1/status", buffer);
  Serial.print("[→] Status: ");
  Serial.println(buffer);
}

// --- Alarm Sound Pattern ---
void soundAlarm() {
  if (!alarmEnabled) return;

  // Two-tone alarm pattern
  for(int i = 0; i < 80; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(1);
    digitalWrite(BUZZER_PIN, LOW);
    delay(1);
  }

  for(int i = 0; i < 100; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(500);
    digitalWrite(BUZZER_PIN, LOW);
    delay(2);
  }
}

// --- Control Functions ---
void controlAlarm(const char* action) {
  Serial.print("[Alarm] Action: ");
  Serial.println(action);

  if (strcmp(action, "enable") == 0) {
    alarmEnabled = true;
    Serial.println("[✓] Alarm ENABLED");
  }
  else if (strcmp(action, "disable") == 0) {
    alarmEnabled = false;
    alarmActive = false;
    digitalWrite(BUZZER_PIN, LOW);
    Serial.println("[✓] Alarm DISABLED");
  }
  else if (strcmp(action, "test") == 0) {
    Serial.println("[!] Testing alarm...");
    soundAlarm();
    Serial.println("[✓] Alarm test complete");
  }

  publishStatus("alarm_command_executed");
}

void controlBuzzer(const char* action, int duration) {
  Serial.print("[Buzzer] Action: ");
  Serial.print(action);
  Serial.print(", Duration: ");
  Serial.println(duration);

  if (strcmp(action, "on") == 0) {
    buzzerOn = true;
    digitalWrite(BUZZER_PIN, HIGH);
  }
  else if (strcmp(action, "off") == 0) {
    buzzerOn = false;
    digitalWrite(BUZZER_PIN, LOW);
  }
  else if (strcmp(action, "beep") == 0) {
    // Beep for specified duration
    digitalWrite(BUZZER_PIN, HIGH);
    delay(duration);
    digitalWrite(BUZZER_PIN, LOW);
  }

  publishStatus("buzzer_command_executed");
}

void controlLED(const char* action) {
  Serial.print("[LED] Action: ");
  Serial.println(action);

  if (strcmp(action, "on") == 0) {
    ledAutoMode = false;
    digitalWrite(LED_PIN, HIGH);
  }
  else if (strcmp(action, "off") == 0) {
    ledAutoMode = false;
    digitalWrite(LED_PIN, LOW);
  }
  else if (strcmp(action, "auto") == 0) {
    ledAutoMode = true;
    // LED will follow alarm state
  }

  publishStatus("led_command_executed");
}

// --- MQTT Callback (Handle Dashboard Commands) ---
void callback(char* topic, byte* message, unsigned int length) {
  Serial.println("\n========== MQTT MESSAGE RECEIVED ==========");
  Serial.print("[←] Topic: ");
  Serial.println(topic);
  Serial.print("[←] Length: ");
  Serial.println(length);
  
  // Print raw message for debugging
  Serial.print("[←] Raw message: ");
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
  }
  Serial.println();
  Serial.println("============================================");

  // Parse JSON
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message, length);

  if (error) {
    Serial.print("[✗] JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Check if for this device
  const char* targetDevice = doc["device"];
  Serial.print("[i] Target device: ");
  Serial.println(targetDevice ? targetDevice : "NULL");
  Serial.print("[i] This device: ");
  Serial.println(DEVICE_ID);
  
  if (!targetDevice || strcmp(targetDevice, DEVICE_ID) != 0) {
    Serial.println("[i] Not for this device, ignoring");
    return;
  }

  // Get command
  const char* command = doc["command"];
  if (!command) {
    Serial.println("[✗] No command field");
    return;
  }

  Serial.print("[!] Executing command: ");
  Serial.println(command);

  // Handle commands
  if (strcmp(command, "alarm_control") == 0) {
    const char* action = doc["action"];
    if (action) controlAlarm(action);
  }
  else if (strcmp(command, "buzzer_control") == 0) {
    const char* action = doc["action"];
    int duration = doc["duration"] | 1000;  // Default 1 second
    if (action) controlBuzzer(action, duration);
  }
  else if (strcmp(command, "led_control") == 0) {
    const char* action = doc["action"];
    if (action) controlLED(action);
  }
  else {
    Serial.print("[?] Unknown command: ");
    Serial.println(command);
  }
}

// --- Setup ---
void setup() {
  Serial.begin(115200);
  Serial.println("\n======================================");
  Serial.println("  ESP32-1: Motion Sensor + Alarm");
  Serial.println("======================================");

  // Initialize pins
  pinMode(PIR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  Serial.println("[✓] Pins initialized");
  Serial.println("[✓] PIR Motion Sensor ready");

  // Connect WiFi and MQTT
  setup_wifi();
  client.setServer(MQTT_BROKER_IP, MQTT_PORT);
  client.setCallback(callback);

  Serial.println("[✓] System ready - Waiting for motion...");
}

// --- Main Loop ---
void loop() {

  // MQTT Connection Management
  if (!client.connected()) {
    long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      Serial.println("[!] MQTT disconnected, attempting reconnect...");
      if (reconnect_mqtt()) {
        lastReconnectAttempt = 0;
      }
    }
  } else {
    client.loop();  // Process incoming MQTT messages
  }

  // PIR Motion Detection
  int pirState = digitalRead(PIR_PIN);

  if (pirState == HIGH && alarmEnabled) {
    lastMotionTime = millis();

    if (!alarmActive) {
      Serial.println("\n[!] MOTION DETECTED! Alarm activated!");
      alarmActive = true;
      publishStatus("motion_detected");
    }

    // Sound alarm and LED
    digitalWrite(LED_PIN, HIGH);
    soundAlarm();

  } else {
    // Check if alarm should deactivate
    if (alarmActive && (millis() - lastMotionTime >= alarmDuration)) {
      Serial.println("[✓] No motion for 5s - Alarm reset");
      alarmActive = false;
      digitalWrite(BUZZER_PIN, LOW);
      publishStatus("motion_ended");
    }

    // LED control (auto mode follows alarm state)
    if (ledAutoMode) {
      digitalWrite(LED_PIN, alarmActive ? HIGH : LOW);
    }

    delay(100);
  }

  // Publish heartbeat every 30 seconds
  if (millis() - lastHeartbeat > 30000) {
    lastHeartbeat = millis();
    publishStatus("heartbeat");
  }

  delay(10);
}
