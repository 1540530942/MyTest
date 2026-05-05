from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class VisionService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.episodes_dir = root / "episodes"
        self.episodes_dir.mkdir(parents=True, exist_ok=True)
        self.frame_count = 0

    def capture(self, episode_id: str = "manual") -> dict[str, Any]:
        self.frame_count += 1
        episode_dir = self.episodes_dir / episode_id
        frames_dir = episode_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_name = f"{self.frame_count:06d}.json"
        frame_path = frames_dir / frame_name
        payload = {
            "frame_id": self.frame_count,
            "captured_at": time.time(),
            "mode": "simulation",
            "note": "simulated frame metadata; replace VisionService.capture for real camera input",
        }
        frame_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "frame_id": self.frame_count,
            "path": str(frame_path.relative_to(self.root)),
            "captured_at": payload["captured_at"],
        }

    def describe_scene(self, robot_state: dict[str, Any] | None = None) -> dict[str, Any]:
        front_cm = None
        if robot_state:
            front_cm = robot_state.get("obstacle", {}).get("front_cm")

        if isinstance(front_cm, (int, float)) and front_cm < 35:
            risk = "high"
            scene = "front obstacle is inside the configured stop distance"
        elif isinstance(front_cm, (int, float)) and front_cm < 80:
            risk = "medium"
            scene = "front path is partially constrained; slow movement is recommended"
        else:
            risk = "low"
            scene = "simulated indoor corridor with clear forward path"

        return {
            "ok": True,
            "mode": "simulation",
            "scene": scene,
            "risk": risk,
            "objects": [],
        }
