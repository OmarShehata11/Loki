// ------------------------
// FIRST CODE (PIR + BUZZER)
// ------------------------

// Pin definitions
int pirPin = 15;      // PIR motion sensor on GPIO15
int buzzerPin = 3;    // Buzzer on GPIO3
int ledPin = 2;       // LED on GPIO2 (built-in LED on most ESP32)

// Variables
int pirState = 0;
unsigned long lastMotionTime = 0;  // Track last motion detection time
bool alarmActive = false;
bool lastAlarmState = false;  // Track previous alarm state to detect changes
const unsigned long alarmDuration = 5000;  // 20 seconds in milliseconds

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


// ------------------------
// SECOND CODE (WiFi + MQTT)
// ------------------------

#include <WiFi.h>
#include <PubSubClient.h>

// --- START: CONFIGURE YOUR SETTINGS ---
char WIFI_SSID[] = "MyWiFi";
char WIFI_PASS[] = "password";
const char* MQTT_BROKER_IP = "172.16.10.252"; // Your RPi 5's Static IP
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-entryway";
// --- END: CONFIGURE YOUR SETTINGS ---

// --- Global Variables ---
WiFiClient espClient;
PubSubClient client(espClient);
long lastReconnectAttempt = 0;


// ------------------------
// COMBINED SETUP()
// (Both codes merged with ZERO changes to logic)
// ------------------------
void setup() {
  // Setup from PIR/buzzer code
  Serial.begin(115200);
  pinMode(pirPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  
  digitalWrite(buzzerPin, LOW);
  digitalWrite(ledPin, LOW);
  
  Serial.println("PIR Motion Sensor System Ready");
  Serial.println("Waiting for motion...");

  // Setup from WiFi/MQTT code
  setup_wifi();
  client.setServer(MQTT_BROKER_IP, MQTT_PORT);
  lastReconnectAttempt = 0;
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
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}


// --- Reconnect to MQTT ---
boolean reconnect_mqtt() {
  if (client.connect(MQTT_CLIENT_ID)) {
    Serial.println("MQTT Connected");
    client.subscribe("rpi/broadcast");
  } else {
    Serial.print("failed, rc=");
    Serial.print(client.state());
  }
  return client.connected();
}


// ------------------------
// COMBINED LOOP()
// (Both codes merged without changes)
// ------------------------
void loop() {

  // --- MQTT handling (original code untouched) ---
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
    return;
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


  // --- PIR logic (original code untouched) ---
  pirState = digitalRead(pirPin);

  if (pirState == HIGH) {
    lastMotionTime = millis();

    if (!alarmActive) {
      Serial.println("MOTION DETECTED! Alarm activated!");
      alarmActive = true;
      lastAlarmState = true;
    }

    digitalWrite(ledPin, HIGH);
    soundAlarm();

  } else {

    if (alarmActive && (millis() - lastMotionTime >= alarmDuration)) {
      Serial.println("No motion for 5 seconds. System reset to normal.");
      alarmActive = false;
      digitalWrite(buzzerPin, LOW);
      digitalWrite(ledPin, LOW);
      lastAlarmState = false;
    }

    if (alarmActive) {
      digitalWrite(ledPin, HIGH);
    } else {
      digitalWrite(ledPin, LOW);
    }

    delay(100);
  }
}
