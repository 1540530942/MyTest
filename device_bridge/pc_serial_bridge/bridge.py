from __future__ import annotations

import json
import os
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any

import paho.mqtt.client as mqtt

from core import error_from_exception
from core import process_command
from core import utc_now
from serial_client import create_client


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def load_config() -> BridgeConfig:
    load_env_file()
    load_env_file(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    return BridgeConfig(
        mqtt_host=os.getenv("MQTT_HOST", "127.0.0.1"),
        mqtt_port=env_int("MQTT_PORT", 1883),
        mqtt_username=os.getenv("MQTT_USERNAME") or None,
        mqtt_password=os.getenv("MQTT_PASSWORD") or None,
        device_id=os.getenv("DEVICE_ID", "desk-led"),
        arduino_port=os.getenv("ARDUINO_PORT", "COM3"),
        arduino_baudrate=env_int("ARDUINO_BAUDRATE", 115200),
    )


def publish_json(client: mqtt.Client, topic: str, payload: dict[str, Any], retain: bool = False) -> None:
    client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=retain)


class MqttSerialBridge:
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.serial_client = create_client(config.arduino_port, config.arduino_baudrate)
        self.mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"pc-serial-bridge-{config.device_id}",
        )
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
            print(f"MQTT {message.topic}: {payload}")
            state = process_command(payload, self.serial_client, expected_device_id=self.config.device_id)
            publish_json(client, self.config.state_topic, state)
            print(f"Published state: {state}")
        except Exception as exc:
            raw_payload = message.payload.decode("utf-8", errors="replace")
            error_payload = error_from_exception(self.config.device_id, raw_payload, exc)
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
