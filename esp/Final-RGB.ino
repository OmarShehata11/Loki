/*
 * ESP32-2: RGB LED Controller (Bulb Controller)
 * Controls RGB LED strip based on commands from Loki IDS Dashboard
 *
 * Features:
 *  - WiFi connection
 *  - MQTT connection + auto-reconnect
 *  - Subscribes to: rpi/broadcast
 *  - Publishes to: esp32/sensor2/status
 *  - RGB LED strip control (GPIO 15)
 *  - Responds to dashboard commands (bulb_control)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>

// --- WiFi and MQTT Configuration ---
const char* WIFI_SSID = "Mikro";
const char* WIFI_PASS = "123456789";
const char* MQTT_BROKER_IP = "172.16.10.252";
const int   MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-2";           // Device ID
const char* DEVICE_ID = "esp32-2";                // Must match dashboard

// --- LED Strip Configuration ---
#define LED_PIN 15
#define NUM_LEDS 4
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// --- Global Variables ---
WiFiClient espClient;
PubSubClient client(espClient);

long lastReconnectAttempt = 0;
long lastHeartbeat = 0;

// LED State
bool bulbOn = false;
int currentBrightness = 100;

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

  // Ensure WiFi connected
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (client.connect(MQTT_CLIENT_ID)) {
    Serial.println("[✓] MQTT Connected");

    // Subscribe to broadcast channel
    client.subscribe("rpi/broadcast");
    Serial.println("[✓] Subscribed to: rpi/broadcast");

    // Publish online status
    publishStatus("online");
  }
  else {
    Serial.print("[✗] Failed, rc=");
    Serial.print(client.state());
    Serial.println(" trying again in 5 seconds");
  }

  return client.connected();
}

// --- Publish Status to Dashboard ---
void publishStatus(const char* status) {
  StaticJsonDocument<200> doc;
  doc["device"] = DEVICE_ID;
  doc["status"] = status;
  doc["bulb_state"] = bulbOn ? "on" : "off";
  doc["brightness"] = currentBrightness;

  char buffer[200];
  serializeJson(doc, buffer);

  client.publish("esp32/sensor2/status", buffer);
  Serial.print("[→] Status published: ");
  Serial.println(buffer);
}

// --- Set LED Color ---
void setLEDColor(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

// --- Control Bulb ---
void controlBulb(bool state, int brightness) {
  bulbOn = state;
  currentBrightness = constrain(brightness, 0, 255);

  Serial.print("[Bulb] State: ");
  Serial.print(bulbOn ? "ON" : "OFF");
  Serial.print(", Brightness: ");
  Serial.println(currentBrightness);

  if (bulbOn) {
    // Calculate RGB based on brightness (white light)
    setLEDColor(currentBrightness, currentBrightness, currentBrightness);
  } else {
    // Turn off
    setLEDColor(0, 0, 0);
  }

  // Publish confirmation
  publishStatus("command_executed");
}

// --- MQTT Callback (Handle Dashboard Commands) ---
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("[←] Message on topic: ");
  Serial.print(topic);
  Serial.print(" | Length: ");
  Serial.println(length);

  // Parse JSON message
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message, length);

  if (error) {
    Serial.print("[✗] JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Check if message is for this device
  const char* targetDevice = doc["device"];
  if (!targetDevice || strcmp(targetDevice, DEVICE_ID) != 0) {
    Serial.println("[i] Message not for this device, ignoring");
    return;
  }

  // Get command
  const char* command = doc["command"];
  if (!command) {
    Serial.println("[✗] No command field in message");
    return;
  }

  Serial.print("[!] Command received: ");
  Serial.println(command);

  // Handle bulb_control command
  if (strcmp(command, "bulb_control") == 0) {
    const char* state = doc["state"];           // "on" or "off"
    int brightness = doc["brightness"] | 255;   // Default 255

    if (state) {
      bool turnOn = (strcmp(state, "on") == 0);
      controlBulb(turnOn, brightness);
    } else {
      Serial.println("[✗] No state field in bulb_control command");
    }
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
  Serial.println("  ESP32-2: RGB LED Controller");
  Serial.println("======================================");

  // Initialize LED strip
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
  Serial.println("[✓] LED Strip initialized");

  // Connect to WiFi
  setup_wifi();

  // Setup MQTT
  client.setServer(MQTT_BROKER_IP, MQTT_PORT);
  client.setCallback(callback);

  Serial.println("[✓] System ready");
}

// --- Main Loop ---
void loop() {

  // MQTT reconnect logic
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

  // Publish heartbeat every 30 seconds
  if (millis() - lastHeartbeat > 30000) {
    lastHeartbeat = millis();
    publishStatus("heartbeat");
  }

  delay(10); // Small delay for stability
}
