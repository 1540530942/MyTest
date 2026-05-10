from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CATALOG = BASE_DIR / "skill_catalog.json"
ROS_SETUP = "source /opt/ros/humble/setup.bash && source /home/ubuntu/ros2_ws/install/setup.bash"


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def flatten_skills(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for skill in catalog.get("skills", []):
        keys = [skill["id"], skill["name_zh"], *skill.get("aliases", [])]
        for key in keys:
            result[str(key).strip().lower()] = skill
    return result


def resolve_skill(catalog: dict[str, Any], text: str) -> dict[str, Any]:
    key = text.strip().lower()
    skills = flatten_skills(catalog)
    if key in skills:
        return skills[key]
    for alias, skill in skills.items():
        if alias and alias in key:
            return skill
    raise KeyError(f"unknown action: {text}")


def run_in_container(container: str, command: str, dry_run: bool) -> None:
    docker_command = ["docker", "exec", container, "bash", "-lc", command]
    if dry_run:
        print(" ".join(docker_command))
        return
    subprocess.run(docker_command, check=True)


def execute_camera_servo(skill: dict[str, Any], defaults: dict[str, Any], dry_run: bool) -> None:
    servo = skill["servo"]
    duration = float(defaults.get("servo_duration_s", 0.35))
    topic = str(defaults.get("pwm_servo_topic", "/ros_robot_controller/pwm_servo/set_state"))
    message = (
        "{"
        f"duration: {duration}, "
        f"state: [{{id: [{int(servo['id'])}], position: [{int(servo['position'])}], offset: []}}]"
        "}"
    )
    command = f"{ROS_SETUP} && ros2 topic pub --once {topic} ros_robot_controller_msgs/msg/SetPWMServoState '{message}'"
    run_in_container(str(defaults.get("ros_container", "turbopi")), command, dry_run)


def execute_base_move(skill: dict[str, Any], defaults: dict[str, Any], dry_run: bool) -> None:
    twist = skill["twist"]
    duration_ms = int(defaults.get("move_duration_ms", 600))
    rate = 10
    times = max(1, round(duration_ms / 1000 * rate))
    topic = str(defaults.get("cmd_vel_topic", "/cmd_vel"))
    move_msg = (
        "{"
        f"linear: {{x: {float(twist['linear_x'])}, y: {float(twist['linear_y'])}, z: 0.0}}, "
        f"angular: {{x: 0.0, y: 0.0, z: {float(twist['angular_z'])}}}"
        "}"
    )
    stop_msg = "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
    command = (
        f"{ROS_SETUP} && "
        f"ros2 topic pub --times {times} --rate {rate} {topic} geometry_msgs/msg/Twist '{move_msg}' && "
        f"ros2 topic pub --once {topic} geometry_msgs/msg/Twist '{stop_msg}'"
    )
    run_in_container(str(defaults.get("ros_container", "turbopi")), command, dry_run)


def execute_skill(skill: dict[str, Any], catalog: dict[str, Any], dry_run: bool) -> None:
    defaults = catalog.get("defaults", {})
    if skill["type"] == "camera_servo":
        execute_camera_servo(skill, defaults, dry_run)
        if bool(defaults.get("capture_after_servo", True)):
            request_camera_capture(defaults, dry_run)
    elif skill["type"] == "base_move":
        execute_base_move(skill, defaults, dry_run)
        if bool(defaults.get("capture_after_move", False)):
            request_camera_capture(defaults, dry_run)
    else:
        raise ValueError(f"unsupported skill type: {skill['type']}")


def request_camera_capture(defaults: dict[str, Any], dry_run: bool) -> None:
    settle_ms = int(defaults.get("capture_settle_ms", 500))
    server = str(defaults.get("camera_server", "")).rstrip("/")
    if not server:
        return
    if dry_run:
        print(f"POST {server}/api/capture {{\"mode\":\"single\"}}")
        return
    time.sleep(max(settle_ms, 0) / 1000)
    body = json.dumps({"mode": "single"}).encode("utf-8")
    request = urllib.request.Request(
        f"{server}/api/capture",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute TurboPi camera-look and base-move skills.")
    parser.add_argument("action", help="Skill id or Chinese phrase, for example: 向左看")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--dry-run", action="store_true", help="Print the docker/ROS command without executing it.")
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    try:
        skill = resolve_skill(catalog, args.action)
    except KeyError as exc:
        print(exc, file=sys.stderr)
        return 2

    print(f"[INFO] {skill['name_zh']} -> {skill['id']}")
    execute_skill(skill, catalog, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
