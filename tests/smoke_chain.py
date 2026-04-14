from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cloud_api.mock_api import accept_device_command
from device_bridge.pc_serial_bridge.core import command_topic
from device_bridge.pc_serial_bridge.core import error_topic
from device_bridge.pc_serial_bridge.core import process_command
from device_bridge.pc_serial_bridge.core import state_topic


class InMemoryMqttBus:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.messages.append((topic, payload))

    def latest(self, topic: str) -> dict[str, Any]:
        for message_topic, payload in reversed(self.messages):
            if message_topic == topic:
                return payload
        raise AssertionError(f"No message for topic {topic}")


class MockSerialClient:
    def __init__(self) -> None:
        self.led_state = "off"
        self.commands: list[str] = []

    def send_command(self, command: str) -> str:
        self.commands.append(command)
        if command == "LED_ON":
            self.led_state = "on"
            return "OK LED_ON"
        if command == "LED_OFF":
            self.led_state = "off"
            return "OK LED_OFF"
        if command == "STATUS":
            return f"STATUS {self.led_state.upper()}"
        return f"ERR UNKNOWN_COMMAND {command}"


class SmokeChainTest(unittest.TestCase):
    def test_api_to_bridge_to_state_led_on(self) -> None:
        bus = InMemoryMqttBus()
        serial_client = MockSerialClient()
        device_id = "desk-led"
        payload = {
            "request_id": "req-smoke-001",
            "cmd": "led_set",
            "device_id": device_id,
            "pin": 13,
            "value": "on",
            "source": "web",
            "mqtt_topic": command_topic(device_id),
            "created_at": "2026-04-15T00:00:00Z",
        }

        accepted = accept_device_command(payload, bus)
        self.assertTrue(accepted["accepted"])
        self.assertEqual(bus.latest(command_topic(device_id)), payload)

        state = process_command(bus.latest(command_topic(device_id)), serial_client)
        bus.publish(state_topic(device_id), state)

        self.assertEqual(serial_client.commands, ["LED_ON"])
        self.assertTrue(bus.latest(state_topic(device_id))["ok"])
        self.assertEqual(bus.latest(state_topic(device_id))["state"], {"pin13": "on"})

    def test_invalid_command_is_rejected_before_serial(self) -> None:
        bus = InMemoryMqttBus()
        serial_client = MockSerialClient()
        device_id = "desk-led"
        payload = {
            "request_id": "req-smoke-002",
            "cmd": "led_set",
            "device_id": device_id,
            "pin": 12,
            "value": "on",
            "source": "web",
            "mqtt_topic": command_topic(device_id),
            "created_at": "2026-04-15T00:00:00Z",
        }

        with self.assertRaises(ValueError):
            accept_device_command(payload, bus)

        self.assertEqual(serial_client.commands, [])
        bus.publish(error_topic(device_id), {"ok": False, "error": "validation failed"})
        self.assertFalse(bus.latest(error_topic(device_id))["ok"])


if __name__ == "__main__":
    unittest.main()
