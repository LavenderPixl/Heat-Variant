#include <HTTPClient.h>

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_BME680.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define BME_SCK 13
#define BME_MISO 12
#define BME_MOSI 11
#define BME_CS 10

const char *ssid = "skpdatawifi";    // Change this to your WiFi SSID
const char *password = "maske4040";  // Change this to your WiFi password
const int httpPort = 8000;                // This should not be changed

Adafruit_BME680 bme; // I2C
String macAddress;
WiFiClient client;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(100);
  }

  // We start by connecting to a WiFi network

  Serial.println();
  Serial.println("**");
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println(WiFi.macAddress());

  // Set up oversampling and filter initialization
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150); // 320*C for 150 ms
}

void loop() {
  // Prepare JSON document
  DynamicJsonDocument doc(2048);

  if (!bme.begin(0x76)) {
  Serial.println("Could not find a valid BME680 sensor, check wiring!");
  while (1);
  }

  if (! bme.performReading()) {
    Serial.println("Failed to perform reading :(");
    delay(5000);
    return;
  }

  String json;

  doc["mc_id"] = WiFi.macAddress();
  doc["temperature"] = bme.temperature;
  doc["pressure"] = bme.pressure / 100.0;
  doc["humidity"] = bme.humidity;
  doc["air_quality"] = bme.gas_resistance / 1000.0;

  serializeJson(doc, json);

  HTTPClient http;

  // Send request
  String serverPath = "http://10.11.6.168:8000/get-air-data";
  http.begin(client, serverPath);
  http.addHeader("Content-Type", "application/json");
  
  int result = http.POST(json);
  Serial.print(json);
  if (result > 0) {
    // HTTP headers, response code, and body
    Serial.printf("HTTP Response code: %d\n", result);
    String payload = http.getString();
    // Serial.println(payload);
  } else {
    // Error occurred
    // Serial.printf("Error code: %d\n", result);
    Serial.println(http.errorToString(result).c_str());
  }

  // Disconnect
  http.end();

  // READ --------------------------------------------------------------------------------------------
  delay(10000);
}