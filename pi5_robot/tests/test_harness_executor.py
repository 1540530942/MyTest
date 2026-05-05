from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.harnessd.executor import HarnessExecutor
from services.harnessd.logger import EpisodeLogger
from services.robotd.simulator import RobotController
from services.visiond.simulator import VisionService


class HarnessExecutorTests(unittest.TestCase):
    def test_patrol_task_writes_trace_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            robot = RobotController()
            vision = VisionService(root)
            logger = EpisodeLogger(root)
            harness = HarnessExecutor(robot, vision, logger)

            task = harness.submit("巡查门口区域")

            self.assertEqual(task["status"], "completed")
            self.assertTrue((root / task["report_path"]).exists())
            trace = harness.trace(task["id"])
            self.assertGreaterEqual(len(trace), 4)
            self.assertEqual(trace[0]["event"], "task_received")


if __name__ == "__main__":
    unittest.main()
