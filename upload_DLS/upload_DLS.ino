// dls readings
const unsigned int numReadings = 800;
unsigned int analogVals[numReadings];
long t, t0;

// switch + laser
const int transistor = 7;
char laser_on;


// Speed of the ADC, defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif


void setup() {
  Serial.begin(115200);

  // set prescale to 16
  sbi(ADCSRA, ADPS2) ;
  cbi(ADCSRA, ADPS1) ; 
  cbi(ADCSRA, ADPS0) ;

  pinMode (transistor,  OUTPUT);
}

void loop() {
  int light_in = analogRead(A3);

  if ((laser_on == 'H') && light_in < 150) {
      digitalWrite(transistor, HIGH);
  } 
  else if (laser_on == 'L') {
      digitalWrite(transistor, LOW);
  }
  
  
  if (light_in < 150){    
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
    Serial.println(25);
  }
  else{
    digitalWrite(transistor, LOW);
    Serial.println(-1);
  }

}