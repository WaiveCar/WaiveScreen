#include<Wire.h>
const int MPU = 0x68;
int fanPin = 9;    // fans connected to digital pin 5
int backlightPin = 6; // screen adj connected to digital pin 6 through amp
int fanSpeed = 150, backlightValue = 50;
unsigned long time;
#define THERMISTORPIN A0
#define CURRENTPIN A2
#define NUMSAMPLES 100

void setup() {
  // setup for MPU (GY-521)
  Wire.begin();
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
  // setup for serial communication todo; choose baud rate
  Serial.begin(9600);
  // set analog reference aref pin (3v3)
  analogReference(EXTERNAL);
}

void loop() {
  // write header (1B), generic 0xFF 
  Serial.write(0xFF);

  // get elapsed on time in milliseconds, write to serial LSB first (can reverse order if wanted)
  time = millis();
  byte timeBuf[4];
  timeBuf[0] = time & 255;
  timeBuf[1] = (time >> 8) & 255;
  timeBuf[2] = (time >> 16) & 255;
  timeBuf[3] = (time >> 24) & 255;
  Serial.write(timeBuf, 4);

  // get data from MPU (GY-521)
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU, 14, true);
  //read accel data (AcX HB, AcX LB, AcY HB, AcY LB, AcZ HB, AcZ LB) Signed 2Byte each
  byte Ac[] = {Wire.read(), Wire.read(), Wire.read(), Wire.read(), Wire.read(), Wire.read()};

  //read temperature data (not transmitted (throw away))
  byte temp[] = {Wire.read(), Wire.read()}; 

  //read gyro data (GyX HB, GyX LB, GyY HB, GyY LB, GyZ HB, GyZ LB) Signed 2Byte each
  byte Gy[] = {Wire.read(), Wire.read(), Wire.read(), Wire.read(), Wire.read(), Wire.read()};

  // Setup to take current and thermistor samples through A2 and A0, respectively
  int currentSamples[NUMSAMPLES];
  int thermSamples[NUMSAMPLES];
  float aveCurrentReading = 0;
  float aveThermReading = 0;
  uint8_t i;
  // Take samples for smooth measurements, important for current due to natural oscillations due to the PWM outputs to fans/screen
  for(i=0; i < NUMSAMPLES; i++){
    currentSamples[i] = analogRead(CURRENTPIN);
    thermSamples[i] = analogRead(THERMISTORPIN);
  }
  for (i=0; i<NUMSAMPLES; i++){
    aveCurrentReading += currentSamples[i];
    aveThermReading += thermSamples[i];
  }
  // prepare readings for transmit through serial
  int currentTransmit, thermTransmit;
  currentTransmit =  aveCurrentReading / NUMSAMPLES;
  thermTransmit = aveThermReading / NUMSAMPLES;
  // write current reading and thermistor reading to serial (LB, HB)
  Serial.write(currentTransmit);
  Serial.write((currentTransmit >> 8) & 255);
  Serial.write(thermTransmit);
  Serial.write((thermTransmit >> 8) & 255);

  //set screen brightness to 'backlightValue'
  analogWrite(backlightPin, backlightValue);

  //set fanspeed to 'fanSpeed'
  analogWrite(fanPin, fanSpeed);

  //Write Accel data, Gyro data, fanSpeed, and backlightValue to serial
  Serial.write(Ac, sizeof(Ac));
  Serial.write(Gy, sizeof(Gy));
  Serial.write(fanSpeed);
  Serial.write(backlightValue);


  // check if there has been serial signal received (min 2 bytes)
  if(Serial.available() > 1) {
    delay(10);
    // selector is first byte, options: 0x01 for fanSpeed, 0x10 for display brightness (generic)
    int selector = Serial.read();
    // setting is second byte, max 255
    int setting = Serial.read();
    if (setting > 255){
      setting = 255;
    }
    delay(10);
    if (selector == 0x01){
      // set fan speed, min viable setting for 8x fans is 102/255 (40% duty cycle)
      if (setting < 102){
        setting = 102
      }
      fanSpeed = setting;
    }
    else if (selector == 0x10){
      // set display brightness
      backlightValue = setting;
    }
    
  }
  // todo, adjust delay as desired
  delay(333);
}
