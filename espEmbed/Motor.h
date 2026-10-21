#ifndef MOTOR_H
#define MOTOR_H

#include <Arduino.h>

class Motor {
private:
  int pin;
  float kp, ki, kd;
  float setpoint;
  float input;
  float output;
  float lastInput;
  float integral;
  unsigned long lastTime;
  
public:
  // Constructor
  Motor(int pin, float kp, float ki, float kd);
  
  // Initialize motor
  void begin();
  
  // Update PID calculation
  void update(unsigned long deltaTime);
  
  // Set input (delta from center)
  void setInput(float value);
  
  // Get current output angle
  float getOutput();
  
  // Set position directly (0-270 degrees)
  void setPosition(float degrees);
  
  // PID tuning methods
  void setKp(float value);
  void setKi(float value);
  void setKd(float value);
  void setPID(float kp, float ki, float kd);
  
  // Get PID values
  float getKp();
  float getKi();
  float getKd();
  void getPID(float &kp, float &ki, float &kd);
  
  // Print current PID values
  void printPID();
  
  // Reset integral
  void resetIntegral();
};

#endif
