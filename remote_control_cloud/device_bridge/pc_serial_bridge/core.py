from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol


class SerialClient(Protocol):
    def send_command(self, command: str) -> str:
        ...


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def command_topic(device_id: str) -> str:
    return f"devices/{device_id}/cmd"


def state_topic(device_id: str) -> str:
    return f"devices/{device_id}/state"


def error_topic(device_id: str) -> str:
    return f"devices/{device_id}/errors"


def validate_command_payload(payload: dict[str, Any], expected_device_id: str | None = None) -> None:
    required = ["request_id", "cmd", "device_id", "source", "created_at"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    if expected_device_id and payload["device_id"] != expected_device_id:
        raise ValueError(f"Unexpected device_id: expected {expected_device_id}, got {payload['device_id']}")

    cmd = payload["cmd"]
    if cmd == "led_set":
        if payload.get("value") not in {"on", "off"}:
            raise ValueError("led_set requires value 'on' or 'off'")
        if int(payload.get("pin", 13)) != 13:
            raise ValueError("Arduino Uno demo only allows pin 13")
        return

    if cmd == "status_get":
        return

    raise ValueError(f"Unsupported command: {cmd}")


def map_to_serial_command(payload: dict[str, Any], expected_device_id: str | None = None) -> str:
    validate_command_payload(payload, expected_device_id=expected_device_id)

    cmd = payload.get("cmd")
    value = payload.get("value")

    if cmd == "led_set" and value == "on":
        return "LED_ON"
    if cmd == "led_set" and value == "off":
        return "LED_OFF"
    if cmd == "status_get":
        return "STATUS"

    raise ValueError(f"Unsupported command payload: cmd={cmd!r}, value={value!r}")


def state_from_response(payload: dict[str, Any], serial_command: str, response: str) -> dict[str, Any]:
    state: dict[str, str] = {}

    if response == "OK LED_ON" or response == "STATUS ON":
        state["pin13"] = "on"
    elif response == "OK LED_OFF" or response == "STATUS OFF":
        state["pin13"] = "off"

    return {
        "request_id": payload.get("request_id"),
        "device_id": payload.get("device_id"),
        "ok": response.startswith("OK") or response.startswith("STATUS"),
        "cmd": payload.get("cmd"),
        "serial_command": serial_command,
        "serial_response": response,
        "state": state,
        "updated_at": utc_now(),
    }


def error_from_exception(device_id: str, raw_payload: str, exc: Exception) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "ok": False,
        "error": str(exc),
        "raw_payload": raw_payload,
        "updated_at": utc_now(),
    }


def process_command(
    payload: dict[str, Any],
    serial_client: SerialClient,
    expected_device_id: str | None = None,
) -> dict[str, Any]:
    serial_command = map_to_serial_command(payload, expected_device_id=expected_device_id)
    response = serial_client.send_command(serial_command)
    return state_from_response(payload, serial_command, response)
