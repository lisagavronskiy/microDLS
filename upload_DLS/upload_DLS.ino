// dls readings
const unsigned int numReadings = 800;
unsigned int analogVals[numReadings];
long t, t0;

// switch + laser
const int transistor = 2;
char laser_on;

// calculation constants for temp
const float R1 = 10000;
float logR2, R2, T, Tc;  
const float c1 = 1.009249522e-03, c2 = 2.378405444e-04, c3 = 2.019202697e-07;

// Speed of the ADC
// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif


void setup() {
  Serial.begin(115200);

  // set prescale to 16
  sbi(ADCSRA, ADPS2) ; // cbi means clear bit
  cbi(ADCSRA, ADPS1) ; // sbi means set bit
  cbi(ADCSRA, ADPS0) ;

  pinMode (transistor,  OUTPUT);
}

void loop() {
  int light_in = analogRead(A1);
  int temp_in = analogRead(A2);

  if ((laser_on == 'H') && light_in < 150) {
      digitalWrite(transistor, HIGH);
  } 
  else if (laser_on == 'L') {
      digitalWrite(transistor, LOW);
  }
  
  
  if (light_in < 150){

    R2 = R1 * (1023.0 / (float)temp_in - 1.0);  
    logR2 = log(R2);
    T = (1.0 / (c1 + c2 * logR2 + c3 * logR2 * logR2 * logR2));
    Tc = T - 273.15;

    int dummy = analogRead(A0); // this is because the first point is usually of bad quality
    
    t0 = micros();
    
    // Construct the array
    for (int i=0; i < numReadings ; i++)
    {
      analogVals[i] = analogRead(A1);
    }
    t = micros()-t0;  // calculate elapsed time

    if (Serial.available() > 0) {  // Check if data is available to read
        laser_on = Serial.read();  // Read the incoming byte
    }

    // Send to computer
    for (int i=0; i < numReadings ; i++)
    {
      Serial.print(analogVals[i]);
      Serial.print(',');
    }
    Serial.print(t);
    Serial.print(',');
    Serial.println(Tc);
  }
  else{
    digitalWrite(transistor, LOW);
    Serial.println(-1);
  }
  delay(100);

}