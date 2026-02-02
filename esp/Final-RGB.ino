/*
 * COMBINED FIRMWARE FOR: ESP32-1 (Entryway Hub)
 * Features:
 *  - WiFi connection (your original logic)
 *  - MQTT connection + reconnect logic
 *  - Subscribes to: rpi/broadcast
 *  - Publishes to: esp32/sensor1
 *  - NeoPixel animation on GPIO 15
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>

// --- START: CONFIGURE YOUR SETTINGS ---
const char* WIFI_SSID = "Mikro";
const char* WIFI_PASS = "123456789";
const char* MQTT_BROKER_IP = "172.16.10.252";
const int   MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-entryway";
// --- END: CONFIGURE YOUR SETTINGS ---

// --- Global Variables ---
WiFiClient espClient;
PubSubClient client(espClient);

long lastReconnectAttempt = 0;
long lastMsg = 0;

// ===============================
//   MODIFICATION #1  
//   Merged your LED strip setup
// ===============================
#define PIN 15
#define NUM_LEDS 4
Adafruit_NeoPixel strip(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);
int brightness = 100;

uint32_t colors[] = {
  strip.Color(brightness, 0, 0),
  strip.Color(0, brightness, 0),
  strip.Color(0, 0, brightness),
  strip.Color(brightness, brightness, brightness),
  strip.Color(0, 0, 0)
};


// ===============================
//   Wi-Fi setup (UNCHANGED)
// ===============================
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
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}


// ===============================
//   MODIFICATION #2
//   Single unified MQTT reconnect function
// ===============================
boolean reconnect_mqtt() {
  Serial.print("Attempting MQTT connection...");

  // Ensure WiFi connected
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (client.connect(MQTT_CLIENT_ID)) {
    Serial.println("MQTT Connected");

    // SUBSCRIBE HERE
    client.subscribe("rpi/broadcast");
  }
  else {
    Serial.print("failed, rc=");
    Serial.print(client.state());
    Serial.println(" trying again in 2 seconds");
  }

  return client.connected();
}


// ===============================
//   MQTT CALLBACK
// ===============================
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(" | Data: ");

  String msg;
  for (int i = 0; i < length; i++) msg += (char)message[i];

  Serial.println(msg);

  // Example reaction:
  if (String(topic) == "rpi/broadcast") {
    if (msg == "10") {
      Serial.println("Action received → Blink LED or something");
    }
  }
}


// ===============================
//   SETUP
// ===============================
void setup() {
  Serial.begin(115200);

  // LED strip
  strip.begin();
  strip.show();

  setup_wifi();

  client.setServer(MQTT_BROKER_IP, MQTT_PORT);
  client.setCallback(callback);
}


// ===============================
//   MAIN LOOP
// ===============================
void loop() {
  
  // MQTT reconnect logic
  if (!client.connected()) {
    long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      if (reconnect_mqtt()) lastReconnectAttempt = 0;
    }
  } else {
    client.loop();
  }

  // Animation (NON-BLOCKING)
  static unsigned long lastColorChange = 0;
  static int colorIndex = 0;

  if (millis() - lastColorChange > 500) {
    for (int j = 0; j < NUM_LEDS; j++) {
      strip.setPixelColor(j, colors[colorIndex]);
    }
    strip.show();
    colorIndex = (colorIndex + 1) % 5;
    lastColorChange = millis();
  }

  // Publish every 4 seconds
  if (millis() - lastMsg > 4000) {
    lastMsg = millis();
    client.publish("esp32/sensor1", "88");
  }
}
