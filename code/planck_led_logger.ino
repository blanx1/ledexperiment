// Planck's constant LED experiment - ESP32 voltage/current logger
//
// Wiring:
//   VIN (5V) -> pot outer pin 1
//   GND      -> pot outer pin 3
//   pot wiper -> 440-470 ohm resistor -> LED anode (long leg)
//   LED anode -> 10k resistor -> PIN_ANODE   (10k protects the pin)
//   LED cathode (short leg) -> R_SENSE (100 ohm) -> GND
//   LED cathode -> PIN_SENSE
//
// Readings above ~3.1 V clip. Only a blue LED near full knob gets there; stop the sweep there.
//
// LED voltage = V(anode) - V(cathode)
// LED current = V(cathode) / R_SENSE
//
// Pins below are ADC1 pins on the original ESP32. On an ESP32-S3 use e.g. 1 and 2;
// on an ESP32-C3 use e.g. 0 and 1.

const int   PIN_ANODE = 34;     // LED anode / pot wiper
const int   PIN_SENSE = 35;     // LED cathode / top of sense resistor
const float R_SENSE   = 100.0;  // ohms - measure your actual resistor and put the value here
const int   SAMPLES   = 64;     // readings averaged per data point (reduces ADC noise)

float readMilliVolts(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLES; i++) {
    sum += analogReadMilliVolts(pin);   // uses the chip's factory calibration
  }
  return sum / (float)SAMPLES;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);       // full ~0-3.1 V input range
  delay(500);
  Serial.println("t_ms,V_led_mV,I_mA");
}

void loop() {
  float vAnode = readMilliVolts(PIN_ANODE);
  float vSense = readMilliVolts(PIN_SENSE);

  float vLed = vAnode - vSense;         // mV
  float iLed = vSense / R_SENSE;        // mV / ohm = mA

  Serial.printf("%lu,%.1f,%.4f\n", millis(), vLed, iLed);
  delay(50);
}
