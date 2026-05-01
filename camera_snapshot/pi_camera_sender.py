from __future__ import annotations

import argparse
import io
import os
import signal
import sys
import time
from dataclasses import dataclass

import requests


DEFAULT_SERVER = os.environ.get("CAMERA_SNAPSHOT_SERVER", "http://127.0.0.1:8099")
DEFAULT_TOKEN = os.environ.get("CAMERA_SNAPSHOT_TOKEN", "")


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


def fetch_control(session: requests.Session, server: str) -> dict[str, object]:
    try:
        response = session.get(f"{server}/api/control", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"[WARN] control poll failed: {exc}", flush=True)
        return {"task": None}


def upload_frame(
    session: requests.Session,
    server: str,
    token: str,
    device_id: str,
    frame_id: int,
    task_id: str,
    jpeg: bytes,
) -> None:
    headers = {
        "Content-Type": "image/jpeg",
        "X-Device-ID": device_id,
        "X-Frame-ID": str(frame_id),
        "X-Task-ID": task_id,
    }
    if token:
        headers["X-Camera-Token"] = token
    response = session.post(f"{server}/api/frame", headers=headers, data=jpeg, timeout=15)
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
    camera = build_camera(args)
    print(f"[INFO] camera backend: {camera.name}", flush=True)
    print(f"[INFO] server: {server}", flush=True)

    frame_id = 0
    completed_tasks: set[str] = set()
    try:
        while running:
            control = fetch_control(session, server)
            task = control.get("task")
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
            uploaded = 0
            print(f"[INFO] running task {task_id} mode={task.get('mode')} max_frames={max_frames}", flush=True)

            while running and (max_frames == 0 or uploaded < max_frames) and time.time() <= deadline_at:
                latest_control = fetch_control(session, server)
                latest_task = latest_control.get("task")
                if not isinstance(latest_task, dict) or latest_task.get("id") != task_id:
                    break
                if latest_task.get("status") in {"complete", "expired", "stopped"}:
                    break

                frame_id += 1
                try:
                    jpeg = camera.capture_jpeg()
                    upload_frame(session, server, args.token, args.device_id, frame_id, task_id, jpeg)
                    uploaded += 1
                    total_label = "continuous" if max_frames == 0 else str(max_frames)
                    print(f"[ OK ] uploaded task {task_id} frame {uploaded}/{total_label}", flush=True)
                except Exception as exc:
                    print(f"[WARN] upload failed: {exc}", flush=True)
                if (max_frames == 0 or uploaded < max_frames) and interval_ms > 0:
                    time.sleep(max(interval_ms, 150) / 1000)

            completed_tasks.add(task_id)
            time.sleep(max(args.idle_poll_ms, 250) / 1000)
    finally:
        camera.close()
        print("[INFO] stopped", flush=True)


if __name__ == "__main__":
    main()
