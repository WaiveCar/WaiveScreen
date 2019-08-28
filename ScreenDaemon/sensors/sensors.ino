// WaiveCar WaiveScreen NanoNest Rev 0.2 Arduino Control
// By James Landau
// October 2018
//
// MPU6050 code borrowed from open source arduino.cc user "Krodal".
// version 1.1 (12.5.18) updated to account for current sense board options.


#include <Wire.h>
#include <math.h>
int fanPin = 9;    // fans connected to digital pin 5
int backlightPin = 6; // screen adj connected to digital pin 6 through amp
int resetPin = 4;
int fanSpeed = 150, backlightValue = 220;
#define THERMISTORPIN A0
#define VOLTAGEPIN A1
#define CURRENTPIN A2
#define NUMSAMPLES 100
bool autofan = true;
bool cpu_on = true;
bool ide_debug = false;
int j=0; // used to make sure the fan comes back on.
int backlight_adjust = 1; // used to lower current draw at low voltage to save the battery

// Sensor name is MPU-6050
// Declaring Relevant Register names 
#define MPU6050_ACCEL_XOUT_H       0x3B   // R  
#define MPU6050_ACCEL_XOUT_L       0x3C   // R  
#define MPU6050_ACCEL_YOUT_H       0x3D   // R  
#define MPU6050_ACCEL_YOUT_L       0x3E   // R  
#define MPU6050_ACCEL_ZOUT_H       0x3F   // R  
#define MPU6050_ACCEL_ZOUT_L       0x40   // R  
#define MPU6050_TEMP_OUT_H         0x41   // R  
#define MPU6050_TEMP_OUT_L         0x42   // R  
#define MPU6050_GYRO_XOUT_H        0x43   // R  
#define MPU6050_GYRO_XOUT_L        0x44   // R  
#define MPU6050_GYRO_YOUT_H        0x45   // R  
#define MPU6050_GYRO_YOUT_L        0x46   // R  
#define MPU6050_GYRO_ZOUT_H        0x47   // R  
#define MPU6050_GYRO_ZOUT_L        0x48   // R
#define MPU6050_PWR_MGMT_1         0x6B   // R/W
#define MPU6050_PWR_MGMT_2         0x6C   // R/W
#define MPU6050_WHO_AM_I           0x75   // R
// Default I2C address for the MPU-6050 is 0x68.
// But only if the AD0 pin is low.
// Some sensor boards have AD0 high, and the
// I2C address thus becomes 0x69.
#define MPU6050_I2C_ADDRESS 0x68


// MPU6050 setup
// Declaring an union for the registers and the axis values.
// The byte order does not match the byte order of 
// the compiler and AVR chip.
// The AVR chip (on the Arduino board) has the Low Byte 
// at the lower address.
// But the MPU-6050 has a different order: High Byte at
// lower address, so that has to be corrected.
// The register part "reg" is only used internally, 
// and are swapped in code.
typedef union accel_t_gyro_union
{
  struct
  {
    uint8_t x_accel_h;
    uint8_t x_accel_l;
    uint8_t y_accel_h;
    uint8_t y_accel_l;
    uint8_t z_accel_h;
    uint8_t z_accel_l;
    uint8_t t_h;
    uint8_t t_l;
    uint8_t x_gyro_h;
    uint8_t x_gyro_l;
    uint8_t y_gyro_h;
    uint8_t y_gyro_l;
    uint8_t z_gyro_h;
    uint8_t z_gyro_l;
  } reg;
  struct 
  {
    int16_t x_accel;
    int16_t y_accel;
    int16_t z_accel;
    int16_t temperature;
    int16_t x_gyro;
    int16_t y_gyro;
    int16_t z_gyro;
  } value;
};

// Use the following global variables and access functions to help store the overall
// rotation angle of the sensor
unsigned long last_read_time;
float         last_x_angle;  // These are the filtered angles
float         last_y_angle;
float         last_z_angle;  
float         last_gyro_x_angle;  // Store the gyro angles to compare drift
float         last_gyro_y_angle;
float         last_gyro_z_angle;

void set_last_read_angle_data(unsigned long time, float x, float y, float z, float x_gyro, float y_gyro, float z_gyro) {
  last_read_time = time;
  last_x_angle = x;
  last_y_angle = y;
  last_z_angle = z;
  last_gyro_x_angle = x_gyro;
  last_gyro_y_angle = y_gyro;
  last_gyro_z_angle = z_gyro;
}

inline unsigned long get_last_time() {return last_read_time;}
inline float get_last_x_angle() {return last_x_angle;}
inline float get_last_y_angle() {return last_y_angle;}
inline float get_last_z_angle() {return last_z_angle;}
inline float get_last_gyro_x_angle() {return last_gyro_x_angle;}
inline float get_last_gyro_y_angle() {return last_gyro_y_angle;}
inline float get_last_gyro_z_angle() {return last_gyro_z_angle;}

//  Use the following global variables and access functions
//  to calibrate the acceleration sensor
float    base_x_accel;
float    base_y_accel;
float    base_z_accel;

float    base_x_gyro;
float    base_y_gyro;
float    base_z_gyro;


int read_gyro_accel_vals(uint8_t* accel_t_gyro_ptr) {
  // Read the raw values.
  // Read 14 bytes at once, 
  // containing acceleration, temperature and gyro.
  // With the default settings of the MPU-6050,
  // there is no filter enabled, and the values
  // are not very stable.  Returns the error value
  
  accel_t_gyro_union* accel_t_gyro = (accel_t_gyro_union *) accel_t_gyro_ptr;
   
  int error = MPU6050_read (MPU6050_ACCEL_XOUT_H, (uint8_t *) accel_t_gyro, sizeof(*accel_t_gyro));

  // Swap all high and low bytes.
  // After this, the registers values are swapped, 
  // so the structure name like x_accel_l does no 
  // longer contain the lower byte.
  uint8_t swap;
  #define SWAP(x,y) swap = x; x = y; y = swap

  SWAP ((*accel_t_gyro).reg.x_accel_h, (*accel_t_gyro).reg.x_accel_l);
  SWAP ((*accel_t_gyro).reg.y_accel_h, (*accel_t_gyro).reg.y_accel_l);
  SWAP ((*accel_t_gyro).reg.z_accel_h, (*accel_t_gyro).reg.z_accel_l);
  SWAP ((*accel_t_gyro).reg.t_h, (*accel_t_gyro).reg.t_l);
  SWAP ((*accel_t_gyro).reg.x_gyro_h, (*accel_t_gyro).reg.x_gyro_l);
  SWAP ((*accel_t_gyro).reg.y_gyro_h, (*accel_t_gyro).reg.y_gyro_l);
  SWAP ((*accel_t_gyro).reg.z_gyro_h, (*accel_t_gyro).reg.z_gyro_l);

  return error;
}

// The sensor should be motionless on a horizontal surface 
//  while calibration is happening
void calibrate_sensors() {
  int                   num_readings = 10;
  float                 x_accel = 0;
  float                 y_accel = 0;
  float                 z_accel = 0;
  float                 x_gyro = 0;
  float                 y_gyro = 0;
  float                 z_gyro = 0;
  accel_t_gyro_union    accel_t_gyro;
  
  //Serial.println("Starting Calibration");

  // Discard the first set of values read from the IMU
  read_gyro_accel_vals((uint8_t *) &accel_t_gyro);
  
  // Read and average the raw values from the IMU
  for (int i = 0; i < num_readings; i++) {
    read_gyro_accel_vals((uint8_t *) &accel_t_gyro);
    x_accel += accel_t_gyro.value.x_accel;
    y_accel += accel_t_gyro.value.y_accel;
    z_accel += accel_t_gyro.value.z_accel;
    x_gyro += accel_t_gyro.value.x_gyro;
    y_gyro += accel_t_gyro.value.y_gyro;
    z_gyro += accel_t_gyro.value.z_gyro;
    delay(100);
  }
  x_accel /= num_readings;
  y_accel /= num_readings;
  z_accel /= num_readings;
  x_gyro /= num_readings;
  y_gyro /= num_readings;
  z_gyro /= num_readings;
  
  // Store the raw calibration values globally
  base_x_accel = x_accel;
  base_y_accel = y_accel;
  base_z_accel = z_accel;
  base_x_gyro = x_gyro;
  base_y_gyro = y_gyro;
  base_z_gyro = z_gyro;
  
  //Serial.println("Finishing Calibration");
}



void setup() {
  
  int error;
  uint8_t c;
  Serial.begin(115200);
  if(ide_debug) Serial.println("starting setup");
  // set analog reference aref pin (3v3)
  analogReference(EXTERNAL);
  pinMode(CURRENTPIN, INPUT);
  pinMode(VOLTAGEPIN, INPUT);
  pinMode(THERMISTORPIN, INPUT);
  pinMode(fanPin, OUTPUT);
  pinMode(backlightPin, OUTPUT);
  pinMode(resetPin, OUTPUT);
  // set the fanspeed and backlight before the MPU-6050 setup to avoid black screen during serial connection setups. 
  analogWrite(backlightPin, backlightValue);
  analogWrite(fanPin, fanSpeed);
  if(ide_debug) Serial.println("S1");
  
  // Initialize the 'Wire' class for the I2C-bus.
  Wire.begin();
  // default at power-up:
  //    Gyro at 250 degrees second
  //    Acceleration at 2g
  //    Clock source at internal 8MHz
  //    The device is in sleep mode.
  //
  if(ide_debug) Serial.println("S2");
  error = MPU6050_read (MPU6050_WHO_AM_I, &c, 1);
  // According to the datasheet, the 'sleep' bit
  // should read a '1'. But I read a '0'.
  // That bit has to be cleared, since the sensor
  // is in sleep mode at power-up. Even if the
  // bit reads '0'.
  if(ide_debug) Serial.println("S3");
  error = MPU6050_read (MPU6050_PWR_MGMT_2, &c, 1);

  // Clear the 'sleep' bit to start the sensor.
  MPU6050_write_reg (MPU6050_PWR_MGMT_1, 0);
  if(ide_debug) Serial.println("S4");
  //Initialize the angles
  calibrate_sensors();  
  set_last_read_angle_data(millis(), 0, 0, 0, 0, 0, 0);
  if(ide_debug) Serial.println("finishing setup");

}

void loop() {
  if(ide_debug) Serial.print("four");
  int error;
  accel_t_gyro_union accel_t_gyro;

  // Read the raw values from the MPU6050.
  error = read_gyro_accel_vals((uint8_t*) &accel_t_gyro);
  
  // Get the time of reading for rotation computations
  unsigned long t_now = millis();
  // break up the time for transmission
  byte timeBuf[4];
  timeBuf[0] = t_now & 255;
  timeBuf[1] = (t_now >> 8) & 255;
  timeBuf[2] = (t_now >> 16) & 255;
  timeBuf[3] = (t_now >> 24) & 255;

  if(ide_debug) Serial.print("five");
  // Setup to take current and thermistor samples through A2 and A0, respectively
  int currentSamples[NUMSAMPLES];
  int voltageSamples[NUMSAMPLES];
  int thermSamples[NUMSAMPLES];
  float aveCurrentReading = 0;
  float aveVoltageReading = 0;
  float aveThermReading = 0;
  uint8_t i;
  // Take samples for smooth measurements, important for current due to natural oscillations due to the PWM outputs to fans/screen
  for(i=0; i < NUMSAMPLES; i++){
    currentSamples[i] = analogRead(CURRENTPIN);
    voltageSamples[i] = analogRead(VOLTAGEPIN);
    thermSamples[i] = analogRead(THERMISTORPIN);
  }
  for (i=0; i<NUMSAMPLES; i++){
    aveCurrentReading += currentSamples[i];
    aveVoltageReading += voltageSamples[i];
    aveThermReading += thermSamples[i];
  }
  aveCurrentReading /= NUMSAMPLES;
  aveVoltageReading /= NUMSAMPLES;
  aveThermReading /= NUMSAMPLES;
  // prepare readings for transmit through serial
  int currentTransmit, voltageTransmit, thermTransmit;
  currentTransmit =  aveCurrentReading;
  voltageTransmit = aveVoltageReading;
  thermTransmit = aveThermReading;
  if(ide_debug) Serial.print("six");
  float current = 0.0;
  if(aveCurrentReading > 511){    // different current sense chips are in opposite directions with different null offsets. 
    //ACS711EX
    current = aveCurrentReading/1023.0 * 73.3 - 36.7;
  }
  else{
    //GY-712-30A
    current = (513-aveCurrentReading)/1023.0 * 60.0;
  }

  float voltage = aveVoltageReading/1023.0 * 3.6; // voltage reading is based on aref which is appx 3.6V
  voltage = voltage * 368000.0/68000.0; // voltage is now v_in after reversing the voltage divider
  float temp_c = 1023.0/aveThermReading - 1;
  temp_c = log(temp_c)/3950;
  temp_c += (1/(25+273.13));
  temp_c = 1/temp_c - 273.15;

  // if the fanSpeed was set to 255 when the computer turns off, when it turns back on the fan does not come back
  // so it needs to be temporarily turned off before resuming.
  if (fanSpeed == 255){
    j++;
    if (j >= 50){
      analogWrite(fanPin, 0);
      delay(1);
      analogWrite(fanPin, fanSpeed);
      j = 0;
    }
  } 
  if(ide_debug) Serial.print("seven");
  // use temp to set fanspeed;
  int temp_levels[] = {15, 20, 30, 35, 40};
  int temp_settings[] = {0, 102, 140, 180, 220, 255};
  if (autofan == true) {
    if (temp_c < -40){
      // if thermistor breaks and becomes an open, temp is reported as -44C, in this instance, run fans at half speed to ensure no thermal damage.
      fanSpeed = temp_settings[3];
    }
    else if (temp_c < temp_levels[0]){
      fanSpeed = temp_settings[0];
    } else if (temp_c < temp_levels[4]){
      fanSpeed = ((temp_c - temp_levels[0])/(temp_levels[4] - temp_levels[0]) * (temp_settings[5]-temp_settings[1])) + temp_settings[1];
    } else {
      fanSpeed = temp_settings[5];
    }
  }   

  // set the fan and backlight each loop
  analogWrite(backlightPin, backlightValue);
  analogWrite(fanPin, fanSpeed);
  if(ide_debug) Serial.print("eight");
  if(!ide_debug) {
    // Send the data over the serial bus
    // write header (1B), generic 0xFF 
    Serial.write(0xFF);
    // write time
    Serial.write(timeBuf, 4);
    // write current reading and thermistor reading to serial (HB, LB)
    Serial.write(highByte(currentTransmit));
    Serial.write(lowByte(currentTransmit));
    Serial.write(highByte(voltageTransmit));
    Serial.write(lowByte(voltageTransmit));
    Serial.write(highByte(thermTransmit));
    Serial.write(lowByte(thermTransmit));
    //Write Accel data, Gyro data, fanSpeed, and backlightValue to serial
    Serial.write(highByte(accel_t_gyro.value.x_accel));
    Serial.write(lowByte(accel_t_gyro.value.x_accel));
    Serial.write(highByte(accel_t_gyro.value.y_accel));
    Serial.write(lowByte(accel_t_gyro.value.y_accel));
    Serial.write(highByte(accel_t_gyro.value.z_accel));
    Serial.write(lowByte(accel_t_gyro.value.z_accel));
    Serial.write(highByte(accel_t_gyro.value.x_gyro));
    Serial.write(lowByte(accel_t_gyro.value.x_gyro));
    Serial.write(highByte(accel_t_gyro.value.y_gyro));
    Serial.write(lowByte(accel_t_gyro.value.y_gyro));
    Serial.write(highByte(accel_t_gyro.value.z_gyro));
    Serial.write(lowByte(accel_t_gyro.value.z_gyro));
    Serial.write(fanSpeed);
    Serial.write(backlightValue);
  }

  if(ide_debug){
  ////  Optional switch to serial.print for troubleshooting.
    Serial.print(F("Elapsed time in ms: "));
    Serial.println(t_now);
    Serial.print(F("Current reading, value: "));
    Serial.print(aveCurrentReading);
    Serial.print(F(", "));
    Serial.println(current);
    Serial.print(F("Voltage reading, value: "));
    Serial.print(voltageTransmit);
    Serial.print(F(", "));
    Serial.println(voltage);
    Serial.print(F("Thermistor reading, temp_c value: "));
    Serial.print(thermTransmit);
    Serial.print(F(", "));
    Serial.println(temp_c);
    Serial.print(F("Accel X, Y, Z: "));
    Serial.print(accel_t_gyro.value.x_accel);
    Serial.print(F(", "));
    Serial.print(accel_t_gyro.value.y_accel);
    Serial.print(F(", "));
    Serial.println(accel_t_gyro.value.z_accel);
    Serial.print(F("Fan Speed, Backlight Brightness: "));
    Serial.print(fanSpeed);
    Serial.print(F(", "));
    Serial.println(backlightValue);
    }
//  if (current < 1.0){
//    cpu_on = false;
//    delay(1000);
//    if (voltage > 13.0){
//        digitalWrite(resetPin, HIGH);
//        delay (100);
//        digitalWrite(resetPin, LOW);
//        cpu_on == true;
//        delay(3000);
//    }
//  } else {
//    cpu_on = true;
//  }
//
//  if (voltage < 12.5 & cpu_on == true) {
//    backlight_adjust = 0;
//  } else {
//    backlight_adjust = 1;
//  }
  if(ide_debug) Serial.print("one");
  if (voltage < 13.0 & current < 2.0){
    delay(1000);
  }
  if(ide_debug) Serial.print("two");
  // check if there has been serial signal received (min 2 bytes)
  //
  // **********
  // INPUT LOOP
  // **********
  //
  if(Serial.available() > 1) {

    delay(10);

    // selector is first byte, options: 0x01 for fanSpeed, 0x10 for display brightness (generic)
    int selector = Serial.read();

    // setting is second byte, max 255
    int setting = Serial.read();
    delay(10);

    //
    // 01 01  Autofan
    // 01 xx  Fan to xx
    //
    // 02 NA  Get version
    //
    // 10 xx  Backlight to xx
    // 11 ff  Cpu on
    // 11 00  Cpu off
    //

    if (selector == 0x01){
      // set fan speed, min viable setting for 8x fans is 102/255 (40% duty cycle)
      if (setting == 0x01){
        autofan = true;
      } else {
        fanSpeed = setting;
        autofan = false;
      }
    }
    else if (selector == 0x10){
      // set display brightness
      backlightValue = setting;
    }
    else if (selector == 0x11){
      // turn cpu on or off
      if (setting == 0xff & cpu_on == false) {
        digitalWrite(resetPin, HIGH);
        delay (100);
        digitalWrite(resetPin, LOW);
        cpu_on = true;
        
      } else if (setting == 0x00 & cpu_on == true) {
        digitalWrite(resetPin, HIGH);
        delay (100);
        digitalWrite(resetPin, LOW);
        cpu_on = false;
      }
      
    }
    
  }
  // todo, adjust delay as desired - delay keeps serial port from being swamped.
//  delay(10);
  if(ide_debug) Serial.print("three");
}

// --------------------------------------------------------
// MPU6050_read
//
// This is a common function to read multiple bytes 
// from an I2C device.
//
// It uses the boolean parameter for Wire.endTransMission()
// to be able to hold or release the I2C-bus. 
// This is implemented in Arduino 1.0.1.
//
// Only this function is used to read. 
// There is no function for a single byte.
//
int MPU6050_read(int start, uint8_t *buffer, int size)
{
  int i, n, error;

  Wire.beginTransmission(MPU6050_I2C_ADDRESS);
  n = Wire.write(start);
  if (n != 1)
    return (-10);

  n = Wire.endTransmission(false);    // hold the I2C-bus
  if (n != 0)
    return (n);

  // Third parameter is true: relase I2C-bus after data is read.
  Wire.requestFrom(MPU6050_I2C_ADDRESS, size, true);
  i = 0;
  while(Wire.available() && i<size)
  {
    buffer[i++]=Wire.read();
  }
  if ( i != size)
    return (-11);

  return (0);  // return : no error
}


// --------------------------------------------------------
// MPU6050_write
//
// This is a common function to write multiple bytes to an I2C device.
//
// If only a single register is written,
// use the function MPU_6050_write_reg().
//
// Parameters:
//   start : Start address, use a define for the register
//   pData : A pointer to the data to write.
//   size  : The number of bytes to write.
//
// If only a single register is written, a pointer
// to the data has to be used, and the size is
// a single byte:
//   int data = 0;        // the data to write
//   MPU6050_write (MPU6050_PWR_MGMT_1, &c, 1);
//
int MPU6050_write(int start, const uint8_t *pData, int size)
{
  int n, error;

  Wire.beginTransmission(MPU6050_I2C_ADDRESS);
  n = Wire.write(start);        // write the start address
  if (n != 1)
    return (-20);

  n = Wire.write(pData, size);  // write data bytes
  if (n != size)
    return (-21);

  error = Wire.endTransmission(true); // release the I2C-bus
  if (error != 0)
    return (error);

  return (0);         // return : no error
}

// --------------------------------------------------------
// MPU6050_write_reg
//
// An extra function to write a single register.
// It is just a wrapper around the MPU_6050_write()
// function, and it is only a convenient function
// to make it easier to write a single register.
//
int MPU6050_write_reg(int reg, uint8_t data)
{
  int error;

  error = MPU6050_write(reg, &data, 1);

  return (error);
}
