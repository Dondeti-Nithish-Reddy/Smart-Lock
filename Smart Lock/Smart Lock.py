#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduCAM.h>
#include <Wire.h>
#include <BlynkSimpleEsp32.h>
//#include<SD.h>
#include<SPI.h>
#include<SD.h>
const char* ssid = "YourWiFiSSID";
const char* password = "YourWiFiPassword";
const char* auth = "YourBlynkAuthToken";
// ArduCAM pin connections
#define OV2640 6
const int CS_PIN = 5;
const int RESET_PIN = 15;
const int SDA_PIN = 21;
const int SCL_PIN = 22;
int Switch_Pin = 9;
7
int Lock_Pin = 12;
const int TRIGGER_PIN = 27;
const int ECHO_PIN = 26;
BlynkTimer timer;
ArduCAM arduCam(OV2640, CS_PIN);
bool lockStatus = false; // Initially locked
void setup() {
Serial.begin(115200);
pinMode(Lock_Pin,OUTPUT);
digitalWrite(Lock_Pin,LOW);
pinMode(Switch_Pin, INPUT);
WiFi.begin(ssid, password);
while (WiFi.status() != WL_CONNECTED) {
delay(1000);
Serial.println("Connecting to WiFi...");
}
Serial.println("Connected to WiFi");
Blynk.begin(auth, ssid, password);
arduCam.InitCAM();
8
arduCam.set_format(JPEG);
arduCam.InitCAM();
arduCam.OV2640_set_JPEG_size(OV2640_320x240);
timer.setInterval(1000L, checkLockStatus);
// Virtual pin for lock control switch in Blynk app
Blynk.virtualWrite(V1, lockStatus);
setupServer();
}
void loop() {
Blynk.run();
timer.run();
}
void doorBell(){
if(digitalRead(Switch_Pin) == HIGH){
captureImage();
checkLockStatus();
}
else{
doorBell();
}
}
9
void checkPersonDetection() {
bool newPersonDetected = detectPerson();
bool personDetected = false;
if (newPersonDetected && !personDetected) {
personDetected = true;
captureImage();
} else if (!newPersonDetected && personDetected) {
personDetected = false;
}
}
bool detectPerson() {
// Generate ultrasonic pulse
digitalWrite(TRIGGER_PIN, LOW);
delayMicroseconds(2);
digitalWrite(TRIGGER_PIN, HIGH);
delayMicroseconds(10);
digitalWrite(TRIGGER_PIN, LOW);
// Measure the duration of the echo pulse
unsigned long duration = pulseIn(ECHO_PIN, HIGH);
// Calculate the distance based on the speed of sound
float distance = duration * 0.034 / 2;
10
// If a person is within a certain range, return true
if (distance < 100) {
Serial.println("Person detected");
return true;
} else {
Serial.println("No person detected");
return false;
}
}
void checkLockStatus() {
if (lockStatus) {
// Lock the door
lockDoor();
} else {
// Unlock the door
unlockDoor();
}
}
void lockDoor() {
// Code to lock the door using the smart lock
Serial.println("Locking the door...");
digitalWrite(Lock_Pin, HIGH); // Activate lock mechanism
11
Blynk.virtualWrite(V2, 255);
// Add your lock control code here
}
void unlockDoor() {
// Code to unlock the door using the smart lock
Serial.println("Unlocking the door...");
// Add your unlock control code here
digitalWrite(Lock_Pin, LOW); // Activate lock mechanism
Blynk.virtualWrite(V2, 0);
}
void viewLockStatus()
{
int lockStatus = digitalRead(Lock_Pin);
Blynk.virtualWrite(V2, lockStatus * 255); // Update lock status on Blynk app (LED widget)
}
void setupServer() {
AsyncWebServer server(80);
server.on("/capture", HTTP_GET, [](AsyncWebServerRequest *request) {
captureImage();
request->send(200, "text/plain", "Image captured");
});
server.begin();
12
}
void captureImage() {
char filename[13];
sprintf(filename, "/image-%lu.jpg", millis());
arduCam.clear_fifo_flag();
arduCam.start_capture();
while (!arduCam.get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK))
delay(1);
int total_bytes = arduCam.read_fifo_length();
int buf_len = total_bytes;
byte *image_buffer = new byte[buf_len];
arduCam.CS_LOW();
arduCam.set_fifo_burst();
for (int i = 0; i < total_bytes; i++) {
image_buffer[i] = SPI.transfer(0x00);
}
arduCam.CS_HIGH();
13
arduCam.clear_fifo_flag();
File file = SD.open(filename, FILE_WRITE);
if (file) {
file.write(image_buffer, buf_len);
file.close();
Serial.println("Image captured and saved: " + String(filename));
} else {
Serial.println("Failed to save image.");
}
delete[] image_buffer;
}
BLYNK_WRITE(V1) {
lockStatus = param.asInt();
}