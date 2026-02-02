/*
 * ESP32-2: RGB LED Controller
 * Compatible with Loki IDS Web Interface
 * 
 * Features:
 *  - WiFi connection to Raspberry Pi AP
 *  - MQTT connection + reconnect logic
 *  - Subscribes to: rpi/broadcast (for RGB commands)
 *  - NeoPixel RGB LED strip on GPIO15
 * 
 * Required Libraries:
 *  - WiFi (built-in)
 *  - PubSubClient (install via Library Manager)
 *  - ArduinoJson (install version 6.x via Library Manager)
 *  - Adafruit NeoPixel (install via Library Manager)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

// --- START: CONFIGURE YOUR SETTINGS ---
const char* WIFI_SSID = "Access Point";  // Change to your WiFi SSID
const char* WIFI_PASS = "1234Az@1";  // Change to your WiFi password
const char* MQTT_BROKER_IP = "172.16.10.50";  // Raspberry Pi IP (or 127.0.0.1 if same device)
const int   MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-2";
const char* DEVICE_ID = "esp32-2";  // Must match web interface device ID
// --- END: CONFIGURE YOUR SETTINGS ---

// NeoPixel setup
#define PIN 15
#define NUM_LEDS 4
Adafruit_NeoPixel strip(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

// Global Variables
WiFiClient espClient;
PubSubClient client(espClient);
long lastReconnectAttempt = 0;

// RGB state variables
uint8_t currentR = 0;
uint8_t currentG = 0;
uint8_t currentB = 0;
uint8_t currentBrightness = 255;
String currentEffect = "solid";

// Effect animation variables
unsigned long lastEffectUpdate = 0;
unsigned long effectStartTime = 0;
int rainbowHue = 0;
bool blinkState = false;
unsigned long lastBlinkTime = 0;

// Function to convert hex color string to RGB
bool hexToRgb(String hex, uint8_t& r, uint8_t& g, uint8_t& b) {
  // Remove # if present
  if (hex.startsWith("#")) {
    hex = hex.substring(1);
  }
  
  if (hex.length() != 6) {
    return false;
  }

  // Convert hex to integers
  r = strtol(hex.substring(0, 2).c_str(), NULL, 16);
  g = strtol(hex.substring(2, 4).c_str(), NULL, 16);
  b = strtol(hex.substring(4, 6).c_str(), NULL, 16);
  
  return true;
}

// Function to set RGB color
void setRGBColor(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness) {
  currentR = r;
  currentG = g;
  currentB = b;
  currentBrightness = brightness;
  
  // Apply brightness
  r = (r * brightness) / 255;
  g = (g * brightness) / 255;
  b = (b * brightness) / 255;
  
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
  
  Serial.print("RGB set to: R=");
  Serial.print(r);
  Serial.print(" G=");
  Serial.print(g);
  Serial.print(" B=");
  Serial.print(b);
  Serial.print(" Brightness=");
  Serial.println(brightness);
}

// Function to update effect animation
void updateEffect() {
  unsigned long now = millis();
  
  if (currentEffect == "solid") {
    // Solid color - no animation needed
    setRGBColor(currentR, currentG, currentB, currentBrightness);
  }
  else if (currentEffect == "fade") {
    // Fade between colors
    if (now - lastEffectUpdate > 50) {  // Update every 50ms
      float factor = (sin((now - effectStartTime) / 1000.0) + 1.0) / 2.0;  // 0 to 1
      uint8_t r = (uint8_t)(currentR * factor);
      uint8_t g = (uint8_t)(currentG * factor);
      uint8_t b = (uint8_t)(currentB * factor);
      setRGBColor(r, g, b, currentBrightness);
      lastEffectUpdate = now;
    }
  }
  else if (currentEffect == "rainbow") {
    // Rainbow effect - cycle through hues
    if (now - lastEffectUpdate > 20) {  // Update every 20ms
      rainbowHue = (rainbowHue + 2) % 360;
      
      // Convert HSV to RGB
      float h = rainbowHue / 60.0;
      int i = (int)h;
      float f = h - i;
      float p = 0;
      float q = 1 - f;
      float t = f;
      
      uint8_t r, g, b;
      switch (i % 6) {
        case 0: r = 255; g = t * 255; b = 0; break;
        case 1: r = q * 255; g = 255; b = 0; break;
        case 2: r = 0; g = 255; b = t * 255; break;
        case 3: r = 0; g = q * 255; b = 255; break;
        case 4: r = t * 255; g = 0; b = 255; break;
        case 5: r = 255; g = 0; b = q * 255; break;
      }
      
      // Apply brightness
      r = (r * currentBrightness) / 255;
      g = (g * currentBrightness) / 255;
      b = (b * currentBrightness) / 255;
      
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(r, g, b));
      }
      strip.show();
      lastEffectUpdate = now;
    }
  }
  else if (currentEffect == "blink") {
    // Blink effect
    if (now - lastBlinkTime > 500) {  // Toggle every 500ms
      blinkState = !blinkState;
      if (blinkState) {
        setRGBColor(currentR, currentG, currentB, currentBrightness);
      } else {
        for (int i = 0; i < NUM_LEDS; i++) {
          strip.setPixelColor(i, strip.Color(0, 0, 0));
        }
        strip.show();
      }
      lastBlinkTime = now;
    }
  }
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

// --- MQTT Callback - Handle RGB commands from web interface ---
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

  // Handle rgb_control command
  if (strcmp(command, "rgb_control") == 0) {
    // Get color (hex string like "#FF0000")
    const char* colorStr = doc["color"];
    if (colorStr == NULL) {
      Serial.println("No color field in rgb_control");
      return;
    }

    // Get brightness (0-255)
    uint8_t brightness = doc["brightness"] | 255;
    
    // Get effect
    const char* effectStr = doc["effect"];
    if (effectStr != NULL) {
      currentEffect = String(effectStr);
      effectStartTime = millis();  // Reset effect timer
      Serial.print("Effect set to: ");
      Serial.println(currentEffect);
    }

    // Convert hex color to RGB
    uint8_t r, g, b;
    if (hexToRgb(String(colorStr), r, g, b)) {
      currentR = r;
      currentG = g;
      currentB = b;
      currentBrightness = brightness;
      
      // Apply immediately for solid effect, or start animation
      if (currentEffect == "solid") {
        setRGBColor(r, g, b, brightness);
      } else {
        effectStartTime = millis();
        lastEffectUpdate = 0;
        lastBlinkTime = 0;
        blinkState = false;
        rainbowHue = 0;
      }
      
      Serial.print("RGB command received: Color=");
      Serial.print(colorStr);
      Serial.print(" Brightness=");
      Serial.print(brightness);
      Serial.print(" Effect=");
      Serial.println(currentEffect);
    } else {
      Serial.print("Invalid color format: ");
      Serial.println(colorStr);
    }
  }
}

// --- SETUP ---
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("========================================");
  Serial.println("ESP32-2: RGB LED Controller");
  Serial.println("========================================");

  // Initialize NeoPixel strip
  strip.begin();
  strip.setBrightness(255);
  strip.show();  // Initialize all pixels to 'off'
  
  Serial.println("NeoPixel strip initialized");

  // Setup WiFi and MQTT
  setup_wifi();
  client.setServer(MQTT_BROKER_IP, MQTT_PORT);
  client.setCallback(callback);
  lastReconnectAttempt = 0;
  
  // Set initial color (off)
  setRGBColor(0, 0, 0, 0);
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

  // Update effect animation
  updateEffect();
  
  delay(10);  // Small delay for stability
}
