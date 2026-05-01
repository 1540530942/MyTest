from __future__ import annotations

import json
import os
import threading
from typing import Any

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from device_bridge.pc_serial_bridge.core import command_topic
from device_bridge.pc_serial_bridge.core import error_topic
from device_bridge.pc_serial_bridge.core import state_topic
from device_bridge.pc_serial_bridge.core import validate_command_payload


app = FastAPI(title="Remote Device Command API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("API_CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

state_lock = threading.Lock()
last_states: dict[str, dict[str, Any]] = {}
last_errors: dict[str, dict[str, Any]] = {}
last_heartbeats: dict[str, dict[str, Any]] = {}
state_mqtt_client: mqtt.Client | None = None


def allowed_device_ids() -> set[str]:
    configured = os.getenv("API_ALLOWED_DEVICE_IDS") or os.getenv("DEVICE_ID")
    if not configured:
        return set()
    return {device_id.strip() for device_id in configured.split(",") if device_id.strip()}


def mqtt_host() -> str:
    return os.getenv("MQTT_HOST", "127.0.0.1")


def mqtt_port() -> int:
    return int(os.getenv("MQTT_PORT", "1883"))


def apply_mqtt_credentials(client: mqtt.Client) -> None:
    username = os.getenv("MQTT_USERNAME")
    if username:
        client.username_pw_set(username, os.getenv("MQTT_PASSWORD"))


def ensure_allowed_device_id(device_id: str) -> None:
    allowed_devices = allowed_device_ids()
    if allowed_devices and device_id not in allowed_devices:
        raise ValueError(
            f"Unknown device_id: {device_id}. "
            f"Allowed device_id values: {', '.join(sorted(allowed_devices))}"
        )


def device_id_from_topic(topic: str) -> str | None:
    parts = topic.split("/")
    if len(parts) == 3 and parts[0] == "devices":
        return parts[1]
    return None


def on_state_message(_client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage) -> None:
    device_id = device_id_from_topic(message.topic)
    if not device_id:
        return

    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except json.JSONDecodeError:
        payload = {"device_id": device_id, "raw_payload": message.payload.decode("utf-8", errors="replace")}

    with state_lock:
        if message.topic == state_topic(device_id):
            last_states[device_id] = payload
        elif message.topic == error_topic(device_id):
            last_errors[device_id] = payload
        elif message.topic == f"devices/{device_id}/heartbeat":
            last_heartbeats[device_id] = payload


@app.on_event("startup")
def start_state_listener() -> None:
    global state_mqtt_client
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"remote-device-api-state-cache-{os.getpid()}",
    )
    apply_mqtt_credentials(client)
    client.on_message = on_state_message
    client.connect(mqtt_host(), mqtt_port(), keepalive=30)
    client.subscribe("devices/+/state", qos=1)
    client.subscribe("devices/+/errors", qos=1)
    client.subscribe("devices/+/heartbeat", qos=1)
    client.loop_start()
    state_mqtt_client = client


@app.on_event("shutdown")
def stop_state_listener() -> None:
    global state_mqtt_client
    if state_mqtt_client:
        state_mqtt_client.loop_stop()
        state_mqtt_client.disconnect()
        state_mqtt_client = None


def publish_command(payload: dict[str, Any]) -> str:
    validate_command_payload(payload)
    ensure_allowed_device_id(payload["device_id"])

    topic = payload.get("mqtt_topic") or command_topic(payload["device_id"])
    expected_topic = command_topic(payload["device_id"])

    if topic != expected_topic:
        raise ValueError(f"Invalid mqtt_topic: expected {expected_topic}, got {topic}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    apply_mqtt_credentials(client)
    client.connect(mqtt_host(), mqtt_port(), keepalive=30)
    client.loop_start()
    info = client.publish(topic, json.dumps(payload), qos=1)
    info.wait_for_publish()
    client.loop_stop()
    client.disconnect()
    return topic


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


@app.get("/api/health")
def api_health() -> dict[str, str]:
    return health()


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


@app.get("/devices/{device_id}/state")
def device_state(device_id: str) -> dict[str, Any]:
    try:
        ensure_allowed_device_id(device_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    with state_lock:
        state = last_states.get(device_id)
        error = last_errors.get(device_id)
        heartbeat = last_heartbeats.get(device_id)

    if not state and not error and not heartbeat:
        raise HTTPException(status_code=404, detail=f"No state has been observed for device_id: {device_id}")

    return {
        "device_id": device_id,
        "state": state,
        "error": error,
        "heartbeat": heartbeat,
    }
