#include <math.h> // Include math library for log()

const int dlsVoltageIn = A0;  // Define the analog input pin
const int tempIn = A2;  // Define the analog input pin
const int sampleRate = 1100; // Sampling rate in Hz 

const float R1 = 10000;
float logR2, R2, T, Tc;  
const float c1 = 1.009249522e-03, c2 = 2.378405444e-04, c3 = 2.019202697e-07;

void setup() {
  Serial.begin(230400); // Start serial communication at 115200 baud rate
}

void loop() {
  unsigned long startTime = micros();  // Get current time
  
  // Read DLS value and temperature sensor value
  int dlsValue = analogRead(dlsVoltageIn); 
  int tempValue = analogRead(tempIn);

  // Calculate temperature
  R2 = R1 * (1023.0 / (float)tempValue - 1.0);  
  logR2 = log(R2);
  T = (1.0 / (c1 + c2 * logR2 + c3 * logR2 * logR2 * logR2));
  Tc = T - 273.15;

  // Print values to Serial Monitor
  Serial.print(dlsValue);
  Serial.print(",");
  Serial.println(Tc);
  
  // Wait for the next sample
  unsigned long elapsedTime = micros() - startTime;
  unsigned long delayTime = (1000000 / sampleRate) - elapsedTime; // Ensure constant sampling rate
  if (delayTime > 0) {
    delayMicroseconds(delayTime);
  }
}
