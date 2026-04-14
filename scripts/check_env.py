from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def tcp_connectable(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def print_result(result: CheckResult) -> None:
    status = "OK" if result.ok else "MISSING"
    print(f"[{status}] {result.name}: {result.detail}")


def main() -> int:
    mqtt_host = os.getenv("MQTT_HOST", "127.0.0.1")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    arduino_port = os.getenv("ARDUINO_PORT", "COM3")

    results = [
        CheckResult("python", True, sys.version.split()[0]),
        CheckResult("paho-mqtt", module_available("paho.mqtt.client"), "Python MQTT client"),
        CheckResult("pyserial", module_available("serial"), "Python serial client"),
        CheckResult("fastapi", module_available("fastapi"), "Python HTTP API framework"),
        CheckResult("uvicorn", module_available("uvicorn"), "Python ASGI server"),
        CheckResult("node", shutil.which("node") is not None, shutil.which("node") or "not found"),
        CheckResult("npm", shutil.which("npm") is not None, shutil.which("npm") or "not found"),
        CheckResult("mosquitto", shutil.which("mosquitto") is not None, shutil.which("mosquitto") or "not found"),
        CheckResult("docker", shutil.which("docker") is not None, shutil.which("docker") or "not found"),
        CheckResult(
            "mqtt tcp",
            tcp_connectable(mqtt_host, mqtt_port),
            f"{mqtt_host}:{mqtt_port}",
        ),
        CheckResult("arduino port config", bool(arduino_port), arduino_port),
    ]

    for result in results:
        print_result(result)

    required = ["paho-mqtt", "pyserial", "fastapi", "uvicorn"]
    failed_required = [result.name for result in results if result.name in required and not result.ok]

    if failed_required:
        print(f"\nRequired checks failed: {', '.join(failed_required)}")
        return 1

    print("\nPython bridge and API dependencies are ready.")
    if not tcp_connectable(mqtt_host, mqtt_port):
        print("MQTT broker is not reachable yet. Start Mosquitto/EMQX before running the real bridge.")
    if shutil.which("node") is None or shutil.which("npm") is None:
        print("Node/npm are not installed yet. Frontend build remains blocked until Node.js is installed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
