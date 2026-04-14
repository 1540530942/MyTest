from __future__ import annotations

import argparse
import os

import paho.mqtt.client as mqtt


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch state, error, and heartbeat topics for one device.")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument("--device-id", default=os.getenv("DEVICE_ID", "desk-led"))
    args = parser.parse_args()

    topics = [
        (f"devices/{args.device_id}/state", 1),
        (f"devices/{args.device_id}/errors", 1),
        (f"devices/{args.device_id}/heartbeat", 1),
    ]

    def on_connect(client: mqtt.Client, _userdata, _flags, reason_code, _properties) -> None:
        print(f"Connected: {reason_code}")
        client.subscribe(topics)
        for topic, _qos in topics:
            print(f"Watching {topic}")

    def on_message(_client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
        print(f"\n{message.topic}")
        print(message.payload.decode("utf-8", errors="replace"))

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, keepalive=30)
    client.loop_forever()


if __name__ == "__main__":
    main()
