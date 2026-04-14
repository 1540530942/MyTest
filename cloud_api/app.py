from __future__ import annotations

import json
import os
from typing import Any

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from device_bridge.pc_serial_bridge.core import command_topic
from device_bridge.pc_serial_bridge.core import validate_command_payload


app = FastAPI(title="Remote Device Command API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("API_CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


def publish_command(payload: dict[str, Any]) -> str:
    validate_command_payload(payload)
    topic = payload.get("mqtt_topic") or command_topic(payload["device_id"])
    expected_topic = command_topic(payload["device_id"])

    if topic != expected_topic:
        raise ValueError(f"Invalid mqtt_topic: expected {expected_topic}, got {topic}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    username = os.getenv("MQTT_USERNAME")
    if username:
        client.username_pw_set(username, os.getenv("MQTT_PASSWORD"))
    client.connect(os.getenv("MQTT_HOST", "127.0.0.1"), int(os.getenv("MQTT_PORT", "1883")), keepalive=30)
    client.loop_start()
    info = client.publish(topic, json.dumps(payload), qos=1)
    info.wait_for_publish()
    client.loop_stop()
    client.disconnect()
    return topic


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


@app.post("/devices/command")
def devices_command(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        topic = publish_command(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "accepted": True,
        "request_id": payload["request_id"],
        "device_id": payload["device_id"],
        "mqtt_topic": topic,
    }
