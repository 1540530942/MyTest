from __future__ import annotations

import argparse
import io
import os
import signal
import subprocess
import sys
import time
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests


DEFAULT_SERVER = os.environ.get("CAMERA_SNAPSHOT_SERVER", "http://127.0.0.1:8099")
DEFAULT_TOKEN = os.environ.get("CAMERA_SNAPSHOT_TOKEN", "")
DEFAULT_QUERY_GPIO = int(os.environ.get("CAMERA_SNAPSHOT_DEFAULT_GPIO", "26"))


running = True


def handle_signal(signum: int, frame: object) -> None:
    global running
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


@dataclass
class CameraBackend:
    name: str

    def capture_jpeg(self) -> bytes:
        raise NotImplementedError

    def close(self) -> None:
        return


class Picamera2Backend(CameraBackend):
    def __init__(self, width: int, height: int, quality: int) -> None:
        super().__init__("picamera2")
        from picamera2 import Picamera2

        self.quality = quality
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(main={"size": (width, height)})
        self.camera.configure(config)
        self.camera.start()
        time.sleep(1.0)

    def capture_jpeg(self) -> bytes:
        stream = io.BytesIO()
        self.camera.capture_file(stream, format="jpeg")
        return stream.getvalue()

    def close(self) -> None:
        self.camera.stop()


class OpenCvBackend(CameraBackend):
    def __init__(self, camera_index: int, width: int, height: int, quality: int) -> None:
        super().__init__("opencv")
        import cv2

        self.cv2 = cv2
        self.quality = quality
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(f"could not open camera index {camera_index}")

    def capture_jpeg(self) -> bytes:
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("camera read failed")
        ok, encoded = self.cv2.imencode(".jpg", frame, [int(self.cv2.IMWRITE_JPEG_QUALITY), self.quality])
        if not ok:
            raise RuntimeError("jpeg encode failed")
        return encoded.tobytes()

    def close(self) -> None:
        self.cap.release()


def build_camera(args: argparse.Namespace) -> CameraBackend:
    if args.backend in {"auto", "picamera2"}:
        try:
            return Picamera2Backend(args.width, args.height, args.quality)
        except Exception as exc:
            if args.backend == "picamera2":
                raise
            print(f"[WARN] picamera2 unavailable: {exc}", flush=True)

    if args.backend in {"auto", "opencv"}:
        return OpenCvBackend(args.camera_index, args.width, args.height, args.quality)

    raise RuntimeError(f"unsupported backend: {args.backend}")


def capture_screenshot_jpeg(quality: int) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
        output_path = Path(handle.name)
    output_path.unlink(missing_ok=True)
    try:
        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")
        result = subprocess.run(
            ["scrot", "-q", str(quality), str(output_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        data = output_path.read_bytes()
        if not data:
            raise RuntimeError("screen capture produced an empty file")
        if not data.startswith(b"\xff\xd8"):
            raise RuntimeError(f"screen capture was not JPEG: {result.stdout} {result.stderr}".strip())
        return data
    finally:
        try:
            output_path.unlink()
        except FileNotFoundError:
            pass


def fetch_control(session: requests.Session, server: str) -> dict[str, object]:
    try:
        response = session.get(f"{server}/api/control", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"[WARN] control poll failed: {exc}", flush=True)
        return {"task": None}


def normalize_gpio(value: object, default: int = DEFAULT_QUERY_GPIO) -> int:
    try:
        gpio = int(value)
    except (TypeError, ValueError):
        return default
    if 0 <= gpio <= 53:
        return gpio
    return default


def read_gpio_status(gpio: int) -> dict[str, object]:
    sampled_at = time.time()
    try:
        result = subprocess.run(
            ["pinctrl", "get", str(gpio)],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "gpio": gpio,
            "source": "pinctrl",
            "sampled_at": sampled_at,
            "error": "pinctrl not found",
        }
    except Exception as exc:
        return {"available": False, "gpio": gpio, "source": "pinctrl", "sampled_at": sampled_at, "error": str(exc)}

    raw = result.stdout.strip()
    parts = raw.split()
    level = ""
    for part in parts:
        if part in {"hi", "lo"}:
            level = part
            break
    return {
        "available": bool(level),
        "gpio": gpio,
        "source": "pinctrl",
        "level": level,
        "value": 1 if level == "hi" else 0 if level == "lo" else None,
        "sampled_at": sampled_at,
        "raw": raw,
    }


def upload_frame(
    session: requests.Session,
    server: str,
    token: str,
    device_id: str,
    frame_id: int,
    task_id: str,
    jpeg: bytes,
    gpio_status: dict[str, object],
) -> None:
    headers = {
        "Content-Type": "image/jpeg",
        "X-Device-ID": device_id,
        "X-Frame-ID": str(frame_id),
        "X-Task-ID": task_id,
    }
    if gpio_status:
        headers["X-Gpio-Available"] = "1" if gpio_status.get("available") else "0"
        headers["X-Gpio-Number"] = str(gpio_status.get("gpio") or "")
        headers["X-Gpio-Level"] = str(gpio_status.get("level") or "")
        value = gpio_status.get("value")
        headers["X-Gpio-Value"] = "" if value is None else str(value)
        headers["X-Gpio-Source"] = str(gpio_status.get("source") or "")
        sampled_at = gpio_status.get("sampled_at")
        headers["X-Gpio-Sampled-At"] = "" if sampled_at is None else str(sampled_at)
        headers["X-Gpio-Raw"] = str(gpio_status.get("raw") or gpio_status.get("error") or "")[:300]
        if gpio_status.get("gpio") == 16:
            headers["X-Led1-Available"] = headers["X-Gpio-Available"]
            headers["X-Led1-Gpio"] = headers["X-Gpio-Number"]
            headers["X-Led1-Level"] = headers["X-Gpio-Level"]
            headers["X-Led1-Value"] = headers["X-Gpio-Value"]
            headers["X-Led1-Source"] = headers["X-Gpio-Source"]
            headers["X-Led1-Sampled-At"] = headers["X-Gpio-Sampled-At"]
            headers["X-Led1-Raw"] = headers["X-Gpio-Raw"]
    if token:
        headers["X-Camera-Token"] = token
    response = session.post(f"{server}/api/frame", headers=headers, data=jpeg, timeout=15)
    response.raise_for_status()


def upload_gpio_status(
    session: requests.Session,
    server: str,
    token: str,
    device_id: str,
    gpio_status: dict[str, object],
) -> None:
    payload = {**gpio_status, "device_id": device_id}
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Camera-Token"] = token
    response = session.post(f"{server}/api/gpio", headers=headers, json=payload, timeout=5)
    response.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload Raspberry Pi camera snapshots to the cloud dashboard.")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Camera snapshot server base URL.")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="Optional upload token matching .camera_token on server.")
    parser.add_argument("--device-id", default=os.environ.get("CAMERA_DEVICE_ID", "turbopi"))
    parser.add_argument("--backend", choices=["auto", "picamera2", "opencv"], default="auto")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--quality", type=int, default=78)
    parser.add_argument("--idle-poll-ms", type=int, default=1000)
    args = parser.parse_args()

    server = args.server.rstrip("/")
    session = requests.Session()
    camera: CameraBackend | None = None
    print(f"[INFO] server: {server}", flush=True)

    frame_id = 0
    completed_tasks: set[str] = set()
    last_gpio_upload_at = 0.0
    try:
        while running:
            control = fetch_control(session, server)
            task = control.get("task")
            query_gpio = DEFAULT_QUERY_GPIO
            if isinstance(task, dict):
                query_gpio = normalize_gpio(task.get("query_gpio"))
            now = time.time()
            if now - last_gpio_upload_at >= 1.0:
                try:
                    upload_gpio_status(session, server, args.token, args.device_id, read_gpio_status(query_gpio))
                    last_gpio_upload_at = now
                except Exception as exc:
                    print(f"[WARN] gpio status upload failed: {exc}", flush=True)
            if not isinstance(task, dict) or not task.get("id"):
                time.sleep(max(args.idle_poll_ms, 250) / 1000)
                continue

            task_id = str(task["id"])
            if task_id in completed_tasks or task.get("status") in {"complete", "expired", "stopped"}:
                time.sleep(max(args.idle_poll_ms, 250) / 1000)
                continue

            max_frames = int(task.get("max_frames") or 1)
            interval_ms = int(task.get("interval_ms") or 0)
            deadline_at = float(task.get("deadline_at") or 0)
            mode = str(task.get("mode") or "single")
            uploaded = 0
            print(
                f"[INFO] running task {task_id} mode={mode} "
                f"max_frames={max_frames} query_gpio={query_gpio}",
                flush=True,
            )

            while running and (max_frames == 0 or uploaded < max_frames) and time.time() <= deadline_at:
                latest_control = fetch_control(session, server)
                latest_task = latest_control.get("task")
                if not isinstance(latest_task, dict) or latest_task.get("id") != task_id:
                    break
                if latest_task.get("status") in {"complete", "expired", "stopped"}:
                    break

                frame_id += 1
                try:
                    if mode == "screenshot":
                        jpeg = capture_screenshot_jpeg(args.quality)
                    else:
                        if camera is None:
                            camera = build_camera(args)
                            print(f"[INFO] camera backend: {camera.name}", flush=True)
                        jpeg = camera.capture_jpeg()
                    gpio_status = read_gpio_status(query_gpio)
                    upload_frame(session, server, args.token, args.device_id, frame_id, task_id, jpeg, gpio_status)
                    uploaded += 1
                    total_label = "continuous" if max_frames == 0 else str(max_frames)
                    print(f"[ OK ] uploaded task {task_id} frame {uploaded}/{total_label}", flush=True)
                except Exception as exc:
                    print(f"[WARN] upload failed: {exc}", flush=True)
                    if mode == "screenshot":
                        break
                if (max_frames == 0 or uploaded < max_frames) and interval_ms > 0:
                    time.sleep(max(interval_ms, 150) / 1000)

            completed_tasks.add(task_id)
            time.sleep(max(args.idle_poll_ms, 250) / 1000)
    finally:
        if camera is not None:
            camera.close()
        print("[INFO] stopped", flush=True)


if __name__ == "__main__":
    main()
