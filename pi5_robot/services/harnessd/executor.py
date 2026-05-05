from __future__ import annotations

from typing import Any

from services.harnessd.logger import EpisodeLogger
from services.robotd.simulator import RobotCommandError, RobotController
from services.visiond.simulator import VisionService


class HarnessExecutor:
    def __init__(self, robot: RobotController, vision: VisionService, logger: EpisodeLogger) -> None:
        self.robot = robot
        self.vision = vision
        self.logger = logger
        self.tasks: dict[str, dict[str, Any]] = {}

    def submit(self, task_text: str, mode: str = "supervised_autonomy") -> dict[str, Any]:
        task_text = task_text.strip()
        if not task_text:
            raise ValueError("task must not be empty")

        episode_id = self.logger.start_episode("task")
        task = {
            "id": episode_id,
            "status": "running",
            "task": task_text,
            "mode": mode,
            "report_path": "",
            "error": "",
        }
        self.tasks[episode_id] = task
        self.logger.record(episode_id, "task_received", text=task_text, mode=mode)

        try:
            summary = self._run_plan(episode_id, task_text)
            task["status"] = "completed"
            task["report_path"] = self.logger.write_report(episode_id, "巡查任务报告", summary, task["status"])
            self.logger.record(episode_id, "task_completed", report_path=task["report_path"])
        except Exception as exc:
            task["status"] = "failed"
            task["error"] = str(exc)
            task["report_path"] = self.logger.write_report(episode_id, "巡查任务报告", str(exc), task["status"])
            self.logger.record(episode_id, "task_failed", error=str(exc))

        return dict(task)

    def status(self, task_id: str) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        if task:
            return dict(task)
        trace = self.logger.trace(task_id)
        if trace:
            return {"id": task_id, "status": "archived", "events": len(trace)}
        return {"id": task_id, "status": "not_found"}

    def trace(self, task_id: str) -> list[dict[str, Any]]:
        return self.logger.trace(task_id)

    def cancel(self, task_id: str) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            return {"id": task_id, "status": "not_found"}
        if task["status"] == "running":
            self.robot.stop("task_cancelled")
            task["status"] = "cancelled"
            self.logger.record(task_id, "task_cancelled")
        return dict(task)

    def _run_plan(self, episode_id: str, task_text: str) -> str:
        state = self.robot.snapshot()
        self.logger.record(episode_id, "state", state=state)

        capture = self.vision.capture(episode_id)
        self.logger.record(episode_id, "tool_call", tool="capture_image", result=capture)

        description = self.vision.describe_scene(state)
        self.logger.record(episode_id, "tool_call", tool="describe_scene", result=description)

        summary_parts = [f"初始场景：{description['scene']}，风险：{description['risk']}。"]

        if any(keyword in task_text for keyword in ["巡查", "门口", "看看", "patrol"]):
            moved = self._safe_move_forward(episode_id, 30)
            summary_parts.append(moved)
            rotated = self.robot.rotate(45)
            self.logger.record(episode_id, "tool_call", tool="rotate", args={"angle_deg": 45}, result=rotated)
            second_capture = self.vision.capture(episode_id)
            self.logger.record(episode_id, "tool_call", tool="capture_image", result=second_capture)
            second_description = self.vision.describe_scene(rotated)
            self.logger.record(episode_id, "tool_call", tool="describe_scene", result=second_description)
            summary_parts.append(f"旋转观察后：{second_description['scene']}。")
        elif any(keyword in task_text for keyword in ["跟随", "追踪", "track"]):
            self.logger.record(episode_id, "tracking_deferred", reason="tracking requires real detector and local PID loop")
            summary_parts.append("目标追踪需要真实检测器和本地闭环控制，当前 MVP 只记录请求，不执行跟随。")
        else:
            summary_parts.append("已完成一次状态读取、模拟拍照和场景描述。")

        return "\n\n".join(summary_parts)

    def _safe_move_forward(self, episode_id: str, distance_cm: float) -> str:
        try:
            moved = self.robot.move("forward", distance_cm, max_speed_mps=0.2, stop_if_obstacle=True)
            self.logger.record(
                episode_id,
                "tool_call",
                tool="move_forward",
                args={"distance_cm": distance_cm, "max_speed_mps": 0.2},
                result=moved,
            )
            return f"已安全前进 {distance_cm:g} cm。"
        except RobotCommandError as exc:
            stopped = self.robot.stop("move_forward_rejected")
            self.logger.record(episode_id, "safety_stop", reason=str(exc), state=stopped)
            return f"移动被安全约束拒绝：{exc}。"
