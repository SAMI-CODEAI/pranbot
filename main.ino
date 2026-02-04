#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// ================= WIFI =================
const char* ssid = "Gas_Robot_AP";
const char* password = "12345678";

// ================= SERVER =================
WebServer server(80);

// ================= MQ GAS SENSORS =================
#define MQ2_PIN     34
#define MQ3_PIN     35
#define MQ7_PIN     32
#define MQ135_PIN   33
#define BAT_PIN     36

// ================= IR SENSORS =================
#define IR_LEFT_PIN   4
#define IR_RIGHT_PIN  5

// ================= L298N MOTOR =================
#define IN1 25
#define IN2 26
#define IN3 27
#define IN4 14
#define ENA 12
#define ENB 13

// ================= SERVO RADAR =================
#define SERVO_PIN 15
Servo radarServo;
int radarAngle = 90;
int radarStep = 3;
unsigned long lastRadarMove = 0;

// ================= HC-SR04 =================
#define TRIG_PIN 18
#define ECHO_PIN 19
long radarDistance = 0;

// ================= AUTONOMOUS =================
bool autonomous = false;
unsigned long lastAutoMove = 0;

// ================= MOTOR CONTROL =================
void stopRobot() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
  ledcWrite(0, 0); ledcWrite(1, 0);
}

void moveRobot(String d, int speed) {
  ledcWrite(0, speed);
  ledcWrite(1, speed);

  if (d == "f") {
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  } else if (d == "b") {
    digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
    digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
  } else if (d == "l") {
    digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  } else if (d == "r") {
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
  } else stopRobot();
}

// ================= ULTRASONIC =================
long readUltrasonic() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long d = pulseIn(ECHO_PIN, HIGH, 25000);
  if (!d) return 400;
  return d * 0.034 / 2;
}

// ================= RADAR =================
void radarSweep() {
  if (millis() - lastRadarMove < 40) return;
  radarAngle += radarStep;
  if (radarAngle >= 160 || radarAngle <= 20) radarStep = -radarStep;
  radarServo.write(radarAngle);
  radarDistance = readUltrasonic();
  lastRadarMove = millis();
}

// ================= AUTONOMOUS =================
void autonomousLogic() {
  int smoke = analogRead(MQ2_PIN);
  int co = analogRead(MQ7_PIN);

  if (smoke > 2000 || co > 1500) {
    stopRobot();
    return;
  }

  if (radarDistance < 25) {
    moveRobot("b", 180); delay(300);
    moveRobot("l", 180); delay(300);
    return;
  }

  moveRobot("f", 200);
}

// ================= HTML PAGE =================
const char PAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gas Robot</title>
<style>
body { font-family: Arial; text-align: center; background:#111; color:#0f0; }
button { font-size:22px; padding:15px; margin:8px; width:120px; }
.warn { color:red; font-size:20px; }
</style>
</head>
<body>

<h2>🤖 Gas Detection Robot</h2>

<button onclick="cmd('f')">⬆</button><br>
<button onclick="cmd('l')">⬅</button>
<button onclick="cmd('s')">⏹</button>
<button onclick="cmd('r')">➡</button><br>
<button onclick="cmd('b')">⬇</button>

<h3>Mode</h3>
<button onclick="auto(1)">AUTO ON</button>
<button onclick="auto(0)">AUTO OFF</button>

<h3>Sensors</h3>
<div id="data">Loading...</div>

<script>
function cmd(d){
 fetch('/cmd?d='+d);
}

function auto(v){
 fetch('/auto?v='+v);
}

function update(){
 fetch('/data').then(r=>r.json()).then(d=>{
  let warn = (d.smoke>2000||d.co>1500)?"<div class='warn'>🚨 GAS ALERT</div>":"";
  document.getElementById('data').innerHTML =
   warn+
   "Smoke: "+d.smoke+"<br>"+
   "Methane: "+d.methane+"<br>"+
   "CO: "+d.co+"<br>"+
   "Air: "+d.air+"<br>"+
   "Battery: "+d.battery+"<br>"+
   "Radar: "+d.radar_distance+" cm";
 });
}
setInterval(update, 500);
</script>

</body>
</html>
)rawliteral";

// ================= SETUP =================
void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(IR_LEFT_PIN, INPUT);
  pinMode(IR_RIGHT_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT_PULLDOWN);

  ledcSetup(0, 1000, 8);
  ledcAttachPin(ENA, 0);
  ledcSetup(1, 1000, 8);
  ledcAttachPin(ENB, 1);

  radarServo.attach(SERVO_PIN, 500, 2400);
  radarServo.write(90);

  WiFi.softAP(ssid, password);
  Serial.println(WiFi.softAPIP());

  server.on("/", [](){ server.send_P(200, "text/html", PAGE); });

  server.on("/data", [](){
    String j="{";
    j+="\"smoke\":"+String(analogRead(MQ2_PIN))+",";
    j+="\"methane\":"+String(analogRead(MQ3_PIN))+",";
    j+="\"co\":"+String(analogRead(MQ7_PIN))+",";
    j+="\"air\":"+String(analogRead(MQ135_PIN))+",";
    j+="\"battery\":"+String(analogRead(BAT_PIN))+",";
    j+="\"radar_distance\":"+String(radarDistance);
    j+="}";
    server.send(200,"application/json",j);
  });

  server.on("/cmd", [](){
    if (autonomous) return server.send(403,"text/plain","AUTO");
    String d=server.arg("d");
    if(d=="s") stopRobot(); else moveRobot(d,200);
    server.send(200,"text/plain","OK");
  });

  server.on("/auto", [](){
    autonomous = (server.arg("v")=="1");
    if(!autonomous) stopRobot();
    server.send(200,"text/plain",autonomous?"ON":"OFF");
  });

  server.begin();
}

// ================= LOOP =================
void loop() {
  server.handleClient();
  radarSweep();
  if (autonomous && millis()-lastAutoMove>200){
    autonomousLogic();
    lastAutoMove=millis();
  }
}
//QZAs
