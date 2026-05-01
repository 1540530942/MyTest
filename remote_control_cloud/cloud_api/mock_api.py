from __future__ import annotations

from typing import Any, Protocol

from device_bridge.pc_serial_bridge.core import command_topic
from device_bridge.pc_serial_bridge.core import validate_command_payload


class Publisher(Protocol):
    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        ...


def accept_device_command(payload: dict[str, Any], publisher: Publisher) -> dict[str, Any]:
    validate_command_payload(payload)
    topic = payload.get("mqtt_topic") or command_topic(payload["device_id"])
    expected_topic = command_topic(payload["device_id"])

    if topic != expected_topic:
        raise ValueError(f"Invalid mqtt_topic: expected {expected_topic}, got {topic}")

    publisher.publish(topic, payload)
    return {
        "accepted": True,
        "request_id": payload["request_id"],
        "device_id": payload["device_id"],
        "mqtt_topic": topic,
    }
