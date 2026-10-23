import sys
import pigpio

# Define GPIO pins (BCM numbering)
PAN_PIN = 27
PITCH_PIN = 17

# Initialize pigpio connection
pi = pigpio.pi()
if not pi.connected:
  print(
      "Error: Could not connect to pigpiod. Make sure to run 'sudo pigpiod' first."
  )
  sys.exit(1)


def angle_to_pulsewidth(angle):
  """Maps a 0-270 degree angle to 500-2500 microseconds.

  - 0 deg -> 0.5 ms (500 µs) - 135 deg -> 1.5 ms (1500 µs) - 270 deg -> 2.5 ms
  (2500 µs)
  """
  # Clamp angle between 0 and 270 degrees
  angle = max(0.0, min(270.0, angle))
  # Linear mapping formula
  pulsewidth = 500 + (angle / 270.0) * 2000
  return int(pulsewidth)


def main():
  print("--- 2-Axis Servo Controller (Pan/Pitch) ---")
  print("Servo specs: 270° range | 0.5ms (0°) to 2.5ms (270°)")
  print("Enter angles as: pan,pitch (e.g., 135,135). Type 'q' to quit.\n")

  try:
    while True:
      user_input = input("Enter angles (pan, pitch): ").strip()
      if user_input.lower() == "q":
        break

      try:
        # Split input by comma
        parts = user_input.split(",")
        if len(parts) != 2:
          print("Please enter exactly two values separated by a comma.")
          continue

        pan_angle = float(parts[0].strip())
        pitch_angle = float(parts[1].strip())

        # Convert angles to microsecond pulse widths
        pan_pw = angle_to_pulsewidth(pan_angle)
        pitch_pw = angle_to_pulsewidth(pitch_angle)

        # Send pulse width commands to pigpio
        pi.set_servo_pulsewidth(PAN_PIN, pan_pw)
        pi.set_servo_pulsewidth(PITCH_PIN, pitch_pw)

        print(
            f"-> Moved | Pan: {pan_angle}° ({pan_pw}µs) | Pitch:"
            f" {pitch_angle}° ({pitch_pw}µs)"
        )

      except ValueError:
        print("Invalid input. Please enter valid numbers (e.g., 90, 180).")

  except KeyboardInterrupt:
    print("\nExiting...")

  finally:
    # Turn off servo pulses to prevent jitter/overheating and clean up
    pi.set_servo_pulsewidth(PAN_PIN, 0)
    pi.set_servo_pulsewidth(PITCH_PIN, 0)
    pi.stop()
    print("GPIO cleaned up. Goodbye!")


if __name__ == "__main__":
  main()