#include "espEmbed.h"
#include "Motor.h"

// Motor objects
Motor panMotor(PAN_SERVO_PIN, PAN_LEDC_CHANNEL, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD);
Motor pitchMotor(PITCH_SERVO_PIN, PITCH_LEDC_CHANNEL, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD);

// Timing
unsigned long lastTime = 0;

// PID tuning mode
bool pidTuningMode = false;
int currentMotorIndex = 0;  // 0 = pan, 1 = pitch

void setup() {
  Serial.begin(BAUD_RATE);
  delay(2000);
  
  // Initialize motors
  panMotor.begin();
  pitchMotor.begin();
  
  // Set motors to center (135 degrees)
  panMotor.setPosition(135);
  pitchMotor.setPosition(135);
  
  lastTime = millis();
  
  Serial.println("ESP32 Dual Motor PID Controller Ready");
  Serial.println("270-degree servos: 500-2500µs pulse width");
  Serial.println("Send format: pan_delta,pitch_delta (e.g., -150,50)");
  Serial.println("Range: -320 to 320 for typical 640px width");
  Serial.println();
  Serial.println("Commands:");
  Serial.println("  PID - Enter PID tuning mode");
  Serial.println("  HELP - Show this help");
}

void loop() {
  // Check for commands
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.equalsIgnoreCase("PID")) {
      enterPIDTuningMode();
    } else if (input.equalsIgnoreCase("HELP")) {
      printHelp();
    } else {
      // Parse as pan,pitch deltas
      processMotorInput(input);
    }
  }
  
  // Update PID control at fixed rate
  unsigned long now = millis();
  unsigned long deltaTime = now - lastTime;
  
  if (deltaTime >= SAMPLE_TIME) {
    panMotor.update(deltaTime);
    pitchMotor.update(deltaTime);
    lastTime = now;
  }
}

void processMotorInput(String input) {
  int commaIndex = input.indexOf(',');
  if (commaIndex > 0) {
    float panDelta = input.substring(0, commaIndex).toFloat();
    float pitchDelta = input.substring(commaIndex + 1).toFloat();
    
    // Clamp inputs to reasonable range
    panDelta = constrain(panDelta, -320, 320);
    pitchDelta = constrain(pitchDelta, -320, 320);
    
    panMotor.setInput(panDelta);
    pitchMotor.setInput(pitchDelta);
  }
}

void enterPIDTuningMode() {
  pidTuningMode = true;
  Serial.println();
  Serial.println("=== PID TUNING MODE ===");
  Serial.println("Select motor to tune:");
  Serial.println("  0 - Pan motor");
  Serial.println("  1 - Pitch motor");
  Serial.println();
  
  // Wait for motor selection
  while (pidTuningMode) {
    if (Serial.available() > 0) {
      String selection = Serial.readStringUntil('\n');
      selection.trim();
      
      if (selection == "0" || selection == "1") {
        currentMotorIndex = selection.toInt();
        tuneMotorPID();
        break;
      } else if (selection.equalsIgnoreCase("EXIT")) {
        pidTuningMode = false;
        Serial.println("Exiting PID tuning mode");
        break;
      } else {
        Serial.println("Invalid selection. Enter 0, 1, or EXIT");
      }
    }
  }
}

void tuneMotorPID() {
  Motor *motor = (currentMotorIndex == 0) ? &panMotor : &pitchMotor;
  String motorName = (currentMotorIndex == 0) ? "Pan" : "Pitch";
  
  Serial.println();
  Serial.print("Tuning ");
  Serial.print(motorName);
  Serial.println(" motor PID");
  Serial.println();
  
  while (pidTuningMode) {
    // Show current values
    Serial.print("Current PID values: ");
    motor->printPID();
    Serial.println();
    Serial.println("Enter new values as: kp,ki,kd (use - for no change)");
    Serial.println("Example: 2.5,-,0.8 (keep Ki unchanged)");
    Serial.println("Type EXIT to return to normal mode");
    Serial.print("> ");
    
    // Wait for input
    while (pidTuningMode && !Serial.available()) {
      delay(10);
    }
    
    if (!pidTuningMode) break;
    
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.equalsIgnoreCase("EXIT")) {
      pidTuningMode = false;
      Serial.println("Exiting PID tuning mode");
      break;
    }
    
    // Parse new PID values
    parseAndSetPID(motor, input);
  }
}

void parseAndSetPID(Motor *motor, String input) {
  float currentKp, currentKi, currentKd;
  motor->getPID(currentKp, currentKi, currentKd);
  
  float newKp = currentKp;
  float newKi = currentKi;
  float newKd = currentKd;
  
  int comma1 = input.indexOf(',');
  int comma2 = input.indexOf(',', comma1 + 1);
  
  if (comma1 > 0 && comma2 > comma1) {
    // All three values provided
    String kpStr = input.substring(0, comma1);
    String kiStr = input.substring(comma1 + 1, comma2);
    String kdStr = input.substring(comma2 + 1);
    
    if (kpStr != "-") newKp = kpStr.toFloat();
    if (kiStr != "-") newKi = kiStr.toFloat();
    if (kdStr != "-") newKd = kdStr.toFloat();
    
    motor->setPID(newKp, newKi, newKd);
    Serial.print("Updated to: ");
    motor->printPID();
    Serial.println();
  } else {
    Serial.println("Invalid format. Use: kp,ki,kd");
  }
}

void printHelp() {
  Serial.println();
  Serial.println("=== ESP32 Motor PID Controller ===");
  Serial.println();
  Serial.println("Normal Mode:");
  Serial.println("  Send: pan_delta,pitch_delta");
  Serial.println("  Example: -150,50 (object 150px left, 50px down)");
  Serial.println("  Range: -320 to 320");
  Serial.println();
  Serial.println("Commands:");
  Serial.println("  PID - Enter PID tuning mode");
  Serial.println("  HELP - Show this help");
  Serial.println();
  Serial.println("PID Tuning Mode:");
  Serial.println("  Select motor (0=Pan, 1=Pitch)");
  Serial.println("  Enter: kp,ki,kd (use - for no change)");
  Serial.println("  Example: 2.5,-,0.8");
  Serial.println("  Type EXIT to return to normal mode");
  Serial.println();
}
