from __future__ import annotations

import argparse
import os
import re
import time

import paramiko
import requests


def read_gpio(host: str, username: str, password: str, gpio: int) -> dict[str, object]:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        username=username,
        password=password,
        timeout=10,
        banner_timeout=10,
        auth_timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        stdin, stdout, stderr = client.exec_command(f"pinctrl get {gpio}", timeout=10)
        raw = stdout.read().decode("utf-8", errors="replace").strip()
    finally:
        client.close()

    match = re.search(r"\b(hi|lo)\b", raw)
    level = match.group(1) if match else ""
    return {
        "available": bool(level),
        "gpio": gpio,
        "level": level,
        "value": 1 if level == "hi" else 0 if level == "lo" else None,
        "source": "pc-ssh-bridge",
        "sampled_at": time.time(),
        "raw": raw,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge Raspberry Pi GPIO state to camera-snapshot API over SSH.")
    parser.add_argument("--host", default="192.168.149.1")
    parser.add_argument("--username", default="pi")
    parser.add_argument("--password", default=os.environ.get("GPIO_SSH_PASSWORD", ""))
    parser.add_argument("--gpio", type=int, default=26)
    parser.add_argument("--server", default="https://www.wangyutang.cn/camera")
    parser.add_argument("--device-id", default="turbopi-01-via-pc")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    if not args.password:
        raise SystemExit("Missing SSH password. Pass --password or set GPIO_SSH_PASSWORD.")

    server = args.server.rstrip("/")
    session = requests.Session()
    while True:
        try:
            payload = read_gpio(args.host, args.username, args.password, args.gpio)
            payload["device_id"] = args.device_id
            response = session.post(f"{server}/api/gpio", json=payload, timeout=10)
            response.raise_for_status()
            print(f"[OK] GPIO{args.gpio} {payload.get('level')} {payload.get('raw')}", flush=True)
        except Exception as exc:
            print(f"[WARN] {exc}", flush=True)
        time.sleep(max(args.interval, 0.2))


if __name__ == "__main__":
    main()
