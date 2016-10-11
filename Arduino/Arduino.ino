
#include <Wire.h>

#define SLAVE_ADDRESS 0x04

#define IGNITION_PIN A0
#define WAKE_PIN A5

#define TURN_ON_TIME 0 //wait millis till pi starts 
#define SHUT_DOWN_TIME 15000 // wait millis till pi stops

int number = 0;
int state = 0;

int piAlive = 0;

unsigned long ignitionTurnedOn = 0;
unsigned long ignitionTurnedOff = 0;

void setup() 
{
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(IGNITION_PIN, INPUT);
  digitalWrite(IGNITION_PIN, HIGH);

  Serial.begin(9600); // to enable outputinitialize
  Serial.println("Ready");
}

void setupI2C()
{
  Wire.begin(SLAVE_ADDRESS); // i2c as slave

  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
}

void wakePi()
{ 
  TWCR = 0; // reset TwoWire Control Register to default, inactive state
  pinMode(WAKE_PIN, OUTPUT);
  digitalWrite(WAKE_PIN, LOW);
  
  delay(500);

  digitalWrite(WAKE_PIN, HIGH);
  pinMode(WAKE_PIN, INPUT);
  
  setupI2C();
}

void loop()
{
  int ignition = analogRead(IGNITION_PIN);
  if(ignition < 200)
  {
    ignitionTurnedOn = 0;
    if (ignitionTurnedOff == 0)
    {
      ignitionTurnedOff = millis();
    }
    else if ((millis()- ignitionTurnedOff) > SHUT_DOWN_TIME)
    {
      digitalWrite(LED_BUILTIN, LOW);
      number = 0;
      Serial.println("shutdown");
    }
  }
  else if (ignition > 800)
  {
    ignitionTurnedOff = 0;
    if (ignitionTurnedOn == 0)
    {
      ignitionTurnedOn = millis();
    }
    if ((millis() - ignitionTurnedOn) > TURN_ON_TIME && number == 0)
    {
      Serial.println("startPi");
      digitalWrite(LED_BUILTIN, HIGH);

      wakePi();
      number = 1;
    }
    piAlive = 0;
  }
  delay(100);
}

//callback for received data
void receiveData(int byteCount)
{
  while(Wire.available())
  {
    piAlive = Wire.read();
  }
}

//callback for sending data
void sendData()
{
  Wire.write(number);
}

