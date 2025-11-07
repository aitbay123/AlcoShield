
const char* ssid = "1"; 
const char* password = "12345678"; 

const int mq3Pin = A0;
const int in1 = D5;
const int in2 = D6;
const int in3 = D7;
const int in4 = D8;
const int enA = D3;
const int enB = D4;

unsigned long lastActivationTime = 0;
bool motorsBlocked = false;



void setup() {
  Serial.begin(115200); 
  

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

  Serial.println("System Initialized. Reading MQ-3 Sensor Data...");
}

void loop() {


  int alcoholLevel = analogRead(mq3Pin);
  

  Serial.print("Alcohol Level (A0): ");
  Serial.println(alcoholLevel);


  
  if (alcoholLevel > 880 && !motorsBlocked) {
    Serial.println(">>> ALCOHOL THRESHOLD EXCEEDED! MOTORS BLOCKED for 1 hour.");
    motorsBlocked = true;
    lastActivationTime = millis();
  }

  if (motorsBlocked && (millis() - lastActivationTime >= 3600000)) { 
    Serial.println("<<< BLOCK TIME ENDED. MOTORS UNBLOCKED.");
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