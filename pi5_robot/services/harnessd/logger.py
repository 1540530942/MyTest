from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


class EpisodeLogger:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.episodes_dir = root / "episodes"
        self.episodes_dir.mkdir(parents=True, exist_ok=True)

    def start_episode(self, prefix: str = "task") -> str:
        safe_prefix = re.sub(r"[^a-zA-Z0-9_-]+", "_", prefix).strip("_") or "task"
        episode_id = f"{safe_prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}"
        episode_dir = self.episodes_dir / episode_id
        (episode_dir / "frames").mkdir(parents=True, exist_ok=True)
        (episode_dir / "events.jsonl").touch()
        (episode_dir / "report.md").write_text(f"# Episode {episode_id}\n\nStatus: running\n", encoding="utf-8")
        return episode_id

    def record(self, episode_id: str, event: str, **data: Any) -> dict[str, Any]:
        payload = {
            "t": time.time(),
            "event": event,
            **data,
        }
        events_path = self.episodes_dir / episode_id / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload

    def trace(self, episode_id: str) -> list[dict[str, Any]]:
        events_path = self.episodes_dir / episode_id / "events.jsonl"
        if not events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        with events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def write_report(self, episode_id: str, title: str, summary: str, status: str) -> str:
        report = f"# {title}\n\nStatus: {status}\n\n{summary}\n"
        report_path = self.episodes_dir / episode_id / "report.md"
        report_path.write_text(report, encoding="utf-8")
        return str(report_path.relative_to(self.root))
