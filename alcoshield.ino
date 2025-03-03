#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "Steam school 4";
const char* password = "Qaz12345";

ESP8266WebServer server(80);

const int mq3Pin = A0;
const int in1 = D5;
const int in2 = D6;
const int in3 = D7;
const int in4 = D8;
const int enA = D3;
const int enB = D4;

unsigned long lastActivationTime = 0;
bool motorsBlocked = false;

void handleRoot() {
    int alcoholLevel = analogRead(mq3Pin);
    String json = "{\"value\": " + String(alcoholLevel) + "}";
    server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  server.on("/data", handleRoot);
  server.begin();

  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  pinMode(enA, OUTPUT);
  pinMode(enB, OUTPUT);

  analogWrite(enA, 255);
  analogWrite(enB, 255);

  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
}

void loop() {
  server.handleClient();

  int alcoholLevel = analogRead(mq3Pin);
  Serial.println("Alcohol Level: " + String(alcoholLevel));

  if (alcoholLevel > 850 && !motorsBlocked) {
    motorsBlocked = true;
    lastActivationTime = millis();
  }

  if (motorsBlocked && (millis() - lastActivationTime >= 3600000)) {
    motorsBlocked = false;
  }

  if (motorsBlocked) {
    analogWrite(enA, 0);
    analogWrite(enB, 0);
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    digitalWrite(in3, LOW);
    digitalWrite(in4, LOW);
  } else {
    analogWrite(enA, 255);
    analogWrite(enB, 255);
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
    digitalWrite(in3, HIGH);
    digitalWrite(in4, LOW);
  }

  delay(500);
}
