#ifndef ESP_EMBED_H
#define ESP_EMBED_H

#include <Arduino.h>

// Serial communication
#define BAUD_RATE 115200

// Timing
#define SAMPLE_TIME 20  // 50Hz update rate

// Servo configuration
#define PAN_SERVO_PIN 25
#define PITCH_SERVO_PIN 26

// Default PID values
#define DEFAULT_KP 2.0
#define DEFAULT_KI 0.0
#define DEFAULT_KD 0.5

#endif
