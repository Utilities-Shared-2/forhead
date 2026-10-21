#include "Motor.h"

// LEDC Configuration
#define LEDC_RESOLUTION 16
#define LEDC_FREQ 50  // 50Hz for servo

// Servo PWM limits (16-bit resolution at 50Hz)
// Based on 270-degree servos: 500µs (0°) to 2500µs (270°)
#define SERVO_MIN_PULSE 500    // 0.5ms
#define SERVO_MAX_PULSE 2500   // 2.5ms
#define PWM_MIN (SERVO_MIN_PULSE * (65536.0 / 20000.0))
#define PWM_MAX (SERVO_MAX_PULSE * (65536.0 / 20000.0))

// Center position (135 degrees for 270° range)
#define CENTER_DEGREES 135

Motor::Motor(int pin, float kp, float ki, float kd) {
  this->pin = pin;
  this->kp = kp;
  this->ki = ki;
  this->kd = kd;
  this->setpoint = 0.0;
  this->input = 0.0;
  this->output = 0.0;
  this->lastInput = 0.0;
  this->integral = 0.0;
  this->lastTime = millis();
}

void Motor::begin() {
  ledcAttach(pin, LEDC_FREQ, LEDC_RESOLUTION);
}

void Motor::update(unsigned long deltaTime) {
  float error = setpoint - input;
  
  // Proportional
  float P = kp * error;
  
  // Integral
  integral += error * (deltaTime / 1000.0);
  float I = ki * integral;
  
  // Derivative
  float derivative = (input - lastInput) / (deltaTime / 1000.0);
  float D = kd * derivative;
  
  // Calculate output
  output = P + I - D;
  
  // Update state
  lastInput = input;
  
  // Convert output to absolute degrees (0-270)
  float degrees = CENTER_DEGREES + constrain(output, -135, 135);
  setPosition(degrees);
}

void Motor::setInput(float value) {
  input = value;
}

float Motor::getOutput() {
  return output;
}

void Motor::setPosition(float degrees) {
  float clampedDegrees = constrain(degrees, 0, 270);
  float pulsewidth = SERVO_MIN_PULSE + clampedDegrees * ((SERVO_MAX_PULSE - SERVO_MIN_PULSE) / 270.0);
  uint32_t pwmValue = pulsewidth * (65536.0 / 20000.0);
  ledcWrite(pin, (uint32_t)constrain(pwmValue, PWM_MIN, PWM_MAX));
}

void Motor::setKp(float value) { kp = value; }
void Motor::setKi(float value) { ki = value; }
void Motor::setKd(float value) { kd = value; }

void Motor::setPID(float kp, float ki, float kd) {
  this->kp = kp;
  this->ki = ki;
  this->kd = kd;
  resetIntegral();
}

float Motor::getKp() { return kp; }
float Motor::getKi() { return ki; }
float Motor::getKd() { return kd; }

void Motor::getPID(float &kp, float &ki, float &kd) {
  kp = this->kp;
  ki = this->ki;
  kd = this->kd;
}

void Motor::printPID() {
  Serial.print("Kp=");
  Serial.print(kp);
  Serial.print(", Ki=");
  Serial.print(ki);
  Serial.print(", Kd=");
  Serial.print(kd);
}

void Motor::resetIntegral() {
  integral = 0.0;
}
