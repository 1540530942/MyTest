from __future__ import annotations

import json
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt

PC_CONTROLLER_DIR = Path(__file__).resolve().parents[1] / "pc_controller"
sys.path.insert(0, str(PC_CONTROLLER_DIR))

from serial_client import create_client  # noqa: E402


@dataclass(frozen=True)
class BridgeConfig:
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    device_id: str
    arduino_port: str
    arduino_baudrate: int

    @property
    def command_topic(self) -> str:
        return f"devices/{self.device_id}/cmd"

    @property
    def state_topic(self) -> str:
        return f"devices/{self.device_id}/state"

    @property
    def error_topic(self) -> str:
        return f"devices/{self.device_id}/errors"

    @property
    def heartbeat_topic(self) -> str:
        return f"devices/{self.device_id}/heartbeat"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def load_config() -> BridgeConfig:
    return BridgeConfig(
        mqtt_host=os.getenv("MQTT_HOST", "127.0.0.1"),
        mqtt_port=env_int("MQTT_PORT", 1883),
        mqtt_username=os.getenv("MQTT_USERNAME") or None,
        mqtt_password=os.getenv("MQTT_PASSWORD") or None,
        device_id=os.getenv("DEVICE_ID", "desk-led"),
        arduino_port=os.getenv("ARDUINO_PORT", "COM3"),
        arduino_baudrate=env_int("ARDUINO_BAUDRATE", 115200),
    )


def map_to_serial_command(payload: dict[str, Any]) -> str:
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


def publish_json(client: mqtt.Client, topic: str, payload: dict[str, Any], retain: bool = False) -> None:
    client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=retain)


class MqttSerialBridge:
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.serial_client = create_client(config.arduino_port, config.arduino_baudrate)
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"pc-serial-bridge-{config.device_id}")
        self.running = True

        if config.mqtt_username:
            self.mqtt_client.username_pw_set(config.mqtt_username, config.mqtt_password)

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

    def on_connect(self, client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any) -> None:
        print(f"Connected to MQTT broker: {reason_code}")
        client.subscribe(self.config.command_topic, qos=1)
        self.publish_heartbeat("online")
        print(f"Subscribed: {self.config.command_topic}")

    def on_disconnect(self, _client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any) -> None:
        print(f"Disconnected from MQTT broker: {reason_code}")

    def on_message(self, client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            serial_command = map_to_serial_command(payload)
            print(f"MQTT {message.topic}: {payload} -> {serial_command}")
            response = self.serial_client.send_command(serial_command)
            state = state_from_response(payload, serial_command, response)
            publish_json(client, self.config.state_topic, state)
            print(f"Published state: {state}")
        except Exception as exc:
            error_payload = {
                "device_id": self.config.device_id,
                "ok": False,
                "error": str(exc),
                "raw_payload": message.payload.decode("utf-8", errors="replace"),
                "updated_at": utc_now(),
            }
            publish_json(client, self.config.error_topic, error_payload)
            print(f"Published error: {error_payload}", file=sys.stderr)

    def publish_heartbeat(self, status: str) -> None:
        publish_json(
            self.mqtt_client,
            self.config.heartbeat_topic,
            {
                "device_id": self.config.device_id,
                "bridge": "pc_serial_bridge",
                "status": status,
                "arduino_port": self.config.arduino_port,
                "updated_at": utc_now(),
            },
            retain=True,
        )

    def stop(self, *_args: Any) -> None:
        self.running = False
        self.publish_heartbeat("offline")
        self.serial_client.disconnect()
        self.mqtt_client.disconnect()

    def run(self) -> None:
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        print(f"Connecting serial port {self.config.arduino_port} at {self.config.arduino_baudrate}")
        self.serial_client.connect()
        print(f"Connecting MQTT broker {self.config.mqtt_host}:{self.config.mqtt_port}")
        self.mqtt_client.connect(self.config.mqtt_host, self.config.mqtt_port, keepalive=30)
        self.mqtt_client.loop_start()

        while self.running:
            time.sleep(1)

        self.mqtt_client.loop_stop()


def main() -> None:
    MqttSerialBridge(load_config()).run()


if __name__ == "__main__":
    main()
