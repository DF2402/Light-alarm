#include <Arduino.h>      
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>
#include <TimeLib.h>  
#include <Wire.h>
#include "config.h"

using namespace websockets;

#define DHTPIN 14
#define DHTTYPE DHT11
#define LED_PIN 3
#define LED_CHANNEL 0
#define LED_FREQ 5000
#define LED_RES -1
#define OLED_SCL 8
#define OLED_SDA 9

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);
DHT dht(DHTPIN, DHTTYPE);
WebsocketsClient client;

float currentTemp = 0.0;
float currentHumi = 0.0;
int currentLED = 0;
bool  ledState = false; 
unsigned long lastWiFiRetry = 0;
unsigned long lastWsRetry = 0;

const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const char* websocket_server = WS_SERVER_URL;
const char* device_id = DEVICE_ID;

time_t t;  

String getTimestamp() {
  return String(millis());
}


void drawScreen(const char* statusMsg = nullptr) {
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_6x13_tr);

  char line[32];
  sprintf(line, "Temp: %.1f C", currentTemp);
  u8g2.drawStr(0, 12, line);

  sprintf(line, "Humi: %.1f %%", currentHumi);
  u8g2.drawStr(0, 26, line);

  sprintf(line, "LED : %s", ledState ? "ON" : "OFF");
  u8g2.drawStr(0, 40, line);

  int y,m,d,h,mi,s;
  timestamp2clocktime(now(), y, m, d, h, mi, s);
  sprintf(line, "%02d-%02d %02d:%02d:%02d", m, d, h, mi, s);
  u8g2.drawStr(0, 54, line);

  if (statusMsg) u8g2.drawStr(0, 64, statusMsg);

  u8g2.sendBuffer();
}

void sendSensor(const char* sensor_id, float value) {
  StaticJsonDocument<200> doc;
  doc["msg_type"] = "sensor_data";
  doc["device_id"] = device_id;
  doc["timestamp"] = getTimestamp();
  doc["sensor_id"] = sensor_id;
  doc["value"] = value;

  String payload;
  serializeJson(doc, payload);
  client.send(payload);
  Serial.println("Sent: " + payload);
}

void sendRegistration() {
  StaticJsonDocument<128> doc;
  doc["msg_type"] = "register";
  doc["device_id"] = device_id;
  String payload;
  serializeJson(doc, payload);
  client.send(payload);
  Serial.println("Sent registration: " + payload);
}

void handleMessage(WebsocketsMessage msg) {
  Serial.println("Received: " + msg.data());

  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, msg.data())) return;

  const char* type   = doc["msg_type"];
  const char* target = doc["device_id"];

  if (strcmp(type, "led_command") == 0 && strcmp(target, device_id) == 0) {
    const char* cmd = doc["value"];
    if(strcasecmp(cmd, "toggle")  == 0) { digitalWrite(LED_PIN, !digitalRead(LED_PIN)); ledState = !ledState; }
    else if(strcasecmp(cmd, "on")  == 0) { digitalWrite(LED_PIN, HIGH); ledState = true; }
    else if(strcasecmp(cmd, "off") == 0) { digitalWrite(LED_PIN, LOW);  ledState = false; }
  }
  else if (strcmp(type, "registration_ack") == 0 && strcmp(target, device_id) == 0) {
    long ts = doc["timestamp"];
    setTime(ts);
    Serial.printf("Server time synced: %ld\n", ts);
    drawScreen("Time synced");
  }
}
void timestamp2clocktime(time_t t, int &y, int &m, int &d, int &h, int &mi, int &s) {
  y  = year(t);
  m  = month(t);
  d  = day(t);
  h  = hour(t) + 8;
  mi = minute(t);
  s  = second(t);
}

void reconnectWiFi() {
  drawScreen("Reconnecting to WiFi ...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  drawScreen("WiFi Connected");
}

void reconnect() {
  drawScreen("Reconnecting to Server ...");
  while (!client.connect(websocket_server)) {
    Serial.println("Failed to connect to server");
    delay(1000);
  }
  Serial.println("Connected to server");
  drawScreen("Server Connected");
  delay(1000);
  sendRegistration();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(OLED_SDA, OLED_SCL);
  u8g2.begin();
  dht.begin();

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  drawScreen("Connecting to WiFi ...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  drawScreen("WiFi Connected");
  delay(1000);

  drawScreen("Connecting to Server ...");
  client.onMessage(handleMessage);
  if (client.connect(websocket_server)) {
    drawScreen("Server Connected");
    sendRegistration();
  } else {
    drawScreen("Server Failed");
  }

  delay(1000);

  setTime(0); 

  drawScreen();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastWiFiRetry > 10000) {   
      drawScreen("WiFi Disconnected");
      reconnectWiFi();
      lastWiFiRetry = millis();
    }
  }
  client.poll();
  if (!client.available()) {
    if (millis() - lastWsRetry > 5000) {
      drawScreen("Server Disconnected");
      reconnect();
      lastWsRetry = millis();
    }
  }

  static unsigned long lastSensor = 0;
  if (millis() - lastSensor >= 1000) {
    currentTemp = dht.readTemperature();
    currentHumi = dht.readHumidity();
    sendSensor("temperature", currentTemp);
    sendSensor("humidity", currentHumi);
    drawScreen();
    lastSensor = millis();
  }
}