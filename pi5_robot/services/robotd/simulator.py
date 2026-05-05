from __future__ import annotations

import math
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any


class RobotCommandError(ValueError):
    """Raised when a robot command violates a safety or range constraint."""


@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    confidence: float = 1.0


@dataclass
class Obstacle:
    front_cm: float = 120.0
    left_cm: float = 120.0
    right_cm: float = 120.0


@dataclass
class Motion:
    mode: str = "idle"
    linear_speed: float = 0.0
    angular_speed: float = 0.0
    last_command: str = ""


@dataclass
class Servo:
    pan_deg: float = 0.0
    tilt_deg: float = 0.0


@dataclass
class Safety:
    e_stop: bool = False
    network_ok: bool = True
    llm_allowed: bool = True
    manual_override: bool = True
    front_stop_distance_cm: float = 35.0
    min_battery_percent_for_auto_task: int = 30


class RobotController:
    def __init__(self) -> None:
        self.pose = Pose()
        self.obstacle = Obstacle()
        self.motion = Motion()
        self.servo = Servo()
        self.safety_state = Safety()
        self.battery_percent = 82.0
        self.mode = "simulation"
        self.updated_at = time.time()
        self._lock = threading.RLock()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "mode": self.mode,
                "pose": asdict(self.pose),
                "battery": round(self.battery_percent, 1),
                "obstacle": asdict(self.obstacle),
                "motion": asdict(self.motion),
                "servo": asdict(self.servo),
                "safety": asdict(self.safety_state),
                "updated_at": self.updated_at,
            }

    def safety(self) -> dict[str, Any]:
        data = self.snapshot()
        return {
            "ok": self._is_safe_for_motion(data),
            "battery": data["battery"],
            "obstacle": data["obstacle"],
            "safety": data["safety"],
        }

    def set_obstacle(self, front_cm: float | None = None, left_cm: float | None = None, right_cm: float | None = None) -> None:
        with self._lock:
            if front_cm is not None:
                self.obstacle.front_cm = float(front_cm)
            if left_cm is not None:
                self.obstacle.left_cm = float(left_cm)
            if right_cm is not None:
                self.obstacle.right_cm = float(right_cm)
            self.updated_at = time.time()

    def set_estop(self, enabled: bool) -> None:
        with self._lock:
            self.safety_state.e_stop = bool(enabled)
            if enabled:
                self._stop_locked("e_stop")
            self.updated_at = time.time()

    def move(self, direction: str, distance_cm: float, max_speed_mps: float = 0.2, stop_if_obstacle: bool = True) -> dict[str, Any]:
        direction = direction.lower().strip()
        if direction not in {"forward", "backward"}:
            raise RobotCommandError("direction must be forward or backward")

        distance_cm = float(distance_cm)
        max_speed_mps = float(max_speed_mps)
        max_distance = 50.0 if direction == "forward" else 30.0
        if not 1 <= distance_cm <= max_distance:
            raise RobotCommandError(f"{direction} distance must be 1..{int(max_distance)} cm")
        if not 0.05 <= max_speed_mps <= 0.3:
            raise RobotCommandError("max_speed_mps must be 0.05..0.3")

        with self._lock:
            self._require_motion_allowed_locked()
            if direction == "forward" and stop_if_obstacle:
                if self.obstacle.front_cm < self.safety_state.front_stop_distance_cm:
                    self._stop_locked("front_obstacle")
                    raise RobotCommandError("front obstacle is inside stop distance")

            sign = 1.0 if direction == "forward" else -1.0
            distance_m = sign * distance_cm / 100.0
            theta_rad = math.radians(self.pose.theta)
            self.pose.x += math.cos(theta_rad) * distance_m
            self.pose.y += math.sin(theta_rad) * distance_m
            self.pose.confidence = max(0.2, self.pose.confidence - 0.01)
            self.battery_percent = max(0.0, self.battery_percent - abs(distance_m) * 0.4)
            self.motion = Motion(
                mode="idle",
                linear_speed=0.0,
                angular_speed=0.0,
                last_command=f"move_{direction}_{distance_cm:g}cm",
            )
            self.updated_at = time.time()
            return self.snapshot()

    def rotate(self, angle_deg: float) -> dict[str, Any]:
        angle_deg = float(angle_deg)
        if not -90 <= angle_deg <= 90:
            raise RobotCommandError("angle_deg must be -90..90")

        with self._lock:
            self._require_motion_allowed_locked()
            self.pose.theta = (self.pose.theta + angle_deg) % 360
            self.pose.confidence = max(0.2, self.pose.confidence - 0.005)
            self.battery_percent = max(0.0, self.battery_percent - abs(angle_deg) * 0.002)
            self.motion = Motion(
                mode="idle",
                linear_speed=0.0,
                angular_speed=0.0,
                last_command=f"rotate_{angle_deg:g}deg",
            )
            self.updated_at = time.time()
            return self.snapshot()

    def stop(self, reason: str = "manual") -> dict[str, Any]:
        with self._lock:
            self._stop_locked(reason)
            self.updated_at = time.time()
            return self.snapshot()

    def pan_tilt(self, pan_deg: float | None = None, tilt_deg: float | None = None) -> dict[str, Any]:
        with self._lock:
            if pan_deg is not None:
                self.servo.pan_deg = self._clamp(float(pan_deg), -90.0, 90.0)
            if tilt_deg is not None:
                self.servo.tilt_deg = self._clamp(float(tilt_deg), -35.0, 45.0)
            self.motion.last_command = f"servo_{self.servo.pan_deg:g}_{self.servo.tilt_deg:g}"
            self.updated_at = time.time()
            return self.snapshot()

    def _require_motion_allowed_locked(self) -> None:
        if self.safety_state.e_stop:
            raise RobotCommandError("emergency stop is active")
        if not self.safety_state.network_ok:
            raise RobotCommandError("network is not healthy")
        if self.battery_percent < self.safety_state.min_battery_percent_for_auto_task:
            raise RobotCommandError("battery is below automatic task threshold")

    def _stop_locked(self, reason: str) -> None:
        self.motion = Motion(mode="idle", linear_speed=0.0, angular_speed=0.0, last_command=f"stop_{reason}")

    def _is_safe_for_motion(self, snapshot: dict[str, Any]) -> bool:
        safety = snapshot["safety"]
        obstacle = snapshot["obstacle"]
        return (
            not safety["e_stop"]
            and safety["network_ok"]
            and snapshot["battery"] >= safety["min_battery_percent_for_auto_task"]
            and obstacle["front_cm"] >= safety["front_stop_distance_cm"]
        )

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
