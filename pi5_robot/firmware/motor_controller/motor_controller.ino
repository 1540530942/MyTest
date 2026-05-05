/*
  Pi5 Robot motor controller placeholder.

  Serial commands:
    MOVE forward 20 0.2
    MOVE backward 10 0.1
    ROTATE 45
    SERVO 0 10
    STOP
    STATE

  Replace the stub handlers with board-specific motor, encoder, servo,
  e-stop, and distance-sensor logic before connecting real motors.
*/

String line;

void setup() {
  Serial.begin(115200);
  Serial.println("{\"ok\":true,\"service\":\"motor_controller\",\"mode\":\"stub\"}");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      handleCommand(line);
      line = "";
    } else if (c != '\r') {
      line += c;
    }
  }
}

void handleCommand(String command) {
  command.trim();
  if (command.length() == 0) {
    return;
  }

  if (command == "STOP") {
    stopMotors();
    Serial.println("{\"ok\":true,\"command\":\"STOP\"}");
    return;
  }

  if (command == "STATE") {
    Serial.println("{\"ok\":true,\"battery\":0,\"front_cm\":999,\"e_stop\":false}");
    return;
  }

  if (command.startsWith("MOVE ") || command.startsWith("ROTATE ") || command.startsWith("SERVO ")) {
    Serial.print("{\"ok\":false,\"error\":\"stub_not_connected\",\"command\":\"");
    Serial.print(command);
    Serial.println("\"}");
    return;
  }

  Serial.println("{\"ok\":false,\"error\":\"unknown_command\"}");
}

void stopMotors() {
  // Add motor driver stop/brake logic here.
}
