#include <Arduino.h>

static const int led_pin = 13;
static bool led_state = false;
static String command_buffer;

void applyLedState(bool on) {
  led_state = on;
  digitalWrite(led_pin, on ? HIGH : LOW);
}

void handleCommand(const String &raw_command) {
  String command = raw_command;
  command.trim();
  command.toUpperCase();

  if (command == "LED_ON") {
    applyLedState(true);
    Serial.println("OK LED_ON");
    return;
  }

  if (command == "LED_OFF") {
    applyLedState(false);
    Serial.println("OK LED_OFF");
    return;
  }

  if (command == "STATUS") {
    Serial.println(led_state ? "STATUS ON" : "STATUS OFF");
    return;
  }

  if (command.length() == 0) {
    return;
  }

  Serial.print("ERR UNKNOWN_COMMAND ");
  Serial.println(command);
}

void setup() {
  Serial.begin(115200);
  pinMode(led_pin, OUTPUT);
  applyLedState(false);
  command_buffer.reserve(32);
  Serial.println("READY REMOTE_LED_13");
}

void loop() {
  while (Serial.available() > 0) {
    char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n' || incoming == '\r') {
      if (command_buffer.length() > 0) {
        handleCommand(command_buffer);
        command_buffer = "";
      }
      continue;
    }

    command_buffer += incoming;
  }
}
