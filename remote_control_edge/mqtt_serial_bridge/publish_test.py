from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from uuid import uuid4

import paho.mqtt.client as mqtt


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_payload(device_id: str, command: str, value: str | None, pin: int) -> dict[str, object]:
    payload: dict[str, object] = {
        "request_id": f"req-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
        "cmd": command,
        "device_id": device_id,
        "pin": pin,
        "source": "test",
        "created_at": utc_now(),
    }
    if value:
        payload["value"] = value
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a test command to the MQTT serial bridge.")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument("--device-id", default=os.getenv("DEVICE_ID", "desk-led"))
    parser.add_argument("--cmd", default="led_set", choices=["led_set", "status_get", "device_reboot"])
    parser.add_argument("--value", choices=["on", "off"], default="on")
    parser.add_argument("--pin", type=int, default=13)
    args = parser.parse_args()

    topic = f"devices/{args.device_id}/cmd"
    payload = build_payload(args.device_id, args.cmd, args.value if args.cmd == "led_set" else None, args.pin)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(args.host, args.port, keepalive=30)
    client.loop_start()
    info = client.publish(topic, json.dumps(payload), qos=1)
    info.wait_for_publish()
    client.loop_stop()
    client.disconnect()

    print(f"Published to {topic}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
