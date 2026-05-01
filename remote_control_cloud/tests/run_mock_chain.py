from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cloud_api.mock_api import accept_device_command
from device_bridge.pc_serial_bridge.core import command_topic
from device_bridge.pc_serial_bridge.core import process_command
from device_bridge.pc_serial_bridge.core import state_topic


class InMemoryMqttBus:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.messages.append((topic, payload))
        print(f"\nMQTT PUBLISH {topic}")
        print(json.dumps(payload, indent=2))

    def latest(self, topic: str) -> dict[str, Any]:
        for message_topic, payload in reversed(self.messages):
            if message_topic == topic:
                return payload
        raise RuntimeError(f"No message for topic {topic}")


class MockArduinoSerial:
    def __init__(self) -> None:
        self.led_state = "off"

    def send_command(self, command: str) -> str:
        print(f"\nSERIAL WRITE {command}")
        if command == "LED_ON":
            self.led_state = "on"
            return "OK LED_ON"
        if command == "LED_OFF":
            self.led_state = "off"
            return "OK LED_OFF"
        if command == "STATUS":
            return f"STATUS {self.led_state.upper()}"
        return f"ERR UNKNOWN_COMMAND {command}"


def run_command(bus: InMemoryMqttBus, serial_client: MockArduinoSerial, payload: dict[str, Any]) -> None:
    accepted = accept_device_command(payload, bus)
    print("\nAPI ACCEPTED")
    print(json.dumps(accepted, indent=2))

    state = process_command(bus.latest(command_topic(payload["device_id"])), serial_client)
    bus.publish(state_topic(payload["device_id"]), state)


def main() -> None:
    bus = InMemoryMqttBus()
    serial_client = MockArduinoSerial()
    device_id = "desk-led"

    commands = [
        {
            "request_id": "req-demo-001",
            "cmd": "led_set",
            "device_id": device_id,
            "pin": 13,
            "value": "on",
            "source": "mock-demo",
            "mqtt_topic": command_topic(device_id),
            "created_at": "2026-04-15T00:00:00Z",
        },
        {
            "request_id": "req-demo-002",
            "cmd": "status_get",
            "device_id": device_id,
            "pin": 13,
            "source": "mock-demo",
            "mqtt_topic": command_topic(device_id),
            "created_at": "2026-04-15T00:00:01Z",
        },
        {
            "request_id": "req-demo-003",
            "cmd": "led_set",
            "device_id": device_id,
            "pin": 13,
            "value": "off",
            "source": "mock-demo",
            "mqtt_topic": command_topic(device_id),
            "created_at": "2026-04-15T00:00:02Z",
        },
    ]

    for payload in commands:
        run_command(bus, serial_client, payload)

    print("\nMOCK CHAIN OK")


if __name__ == "__main__":
    main()
