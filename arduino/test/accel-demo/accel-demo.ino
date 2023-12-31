/*
===Adafruit MMA8451 accelerometer demo===

---DESCRIPTION---
Obtains data from MMA8451 and outputs both raw reading and processed acceleration.

---COMPONENTS---
Adafruit MMA8451
Arduino UNO

---LAYOUT---
Arduino     MMA8451
5V          Vin
GND         GND
A4          SDA
A5          SCL

---REFERENCE---
http://www.arduinoprojects.net/sensor-projects/arduino-mma8451-accelerometer.php
*/

#include <Wire.h>
#include "Adafruit_MMA8451.h"
#include <Adafruit_Sensor.h>


Adafruit_MMA8451 mma = Adafruit_MMA8451();

void setup(void) {
  Serial.begin(9600);
  
  Serial.println("Adafruit MMA8451 test!");
  

  if (! mma.begin()) {
    Serial.println("Couldnt start");
    while (1);
  }
  Serial.println("MMA8451 found!");
  
  mma.setRange(MMA8451_RANGE_2_G);
  
  Serial.print("Range = "); Serial.print(2 << mma.getRange());  
  Serial.println("G");
  
}

void loop() {
  // Read the 'raw' data in 14-bit counts
  mma.read();
  Serial.print("X:\t"); Serial.print(mma.x); 
  Serial.print("\tY:\t"); Serial.print(mma.y); 
  Serial.print("\tZ:\t"); Serial.print(mma.z); 
  Serial.println();

  /* Get a new sensor event */ 
  sensors_event_t event; 
  mma.getEvent(&event);

  /* Display the results (acceleration is measured in m/s^2) */
  Serial.print("X: \t"); Serial.print(event.acceleration.x); Serial.print("\t");
  Serial.print("Y: \t"); Serial.print(event.acceleration.y); Serial.print("\t");
  Serial.print("Z: \t"); Serial.print(event.acceleration.z); Serial.print("\t");
  Serial.println("m/s^2 ");
  
  delay(500);
  
}
