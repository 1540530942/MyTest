from __future__ import annotations

import unittest

from services.robotd.simulator import RobotCommandError, RobotController


class RobotSafetyTests(unittest.TestCase):
    def test_forward_move_updates_pose(self) -> None:
        robot = RobotController()
        state = robot.move("forward", 20)
        self.assertAlmostEqual(state["pose"]["x"], 0.2)
        self.assertEqual(state["motion"]["last_command"], "move_forward_20cm")

    def test_front_obstacle_blocks_forward_motion(self) -> None:
        robot = RobotController()
        robot.set_obstacle(front_cm=20)
        with self.assertRaises(RobotCommandError):
            robot.move("forward", 10)

    def test_backward_distance_is_limited(self) -> None:
        robot = RobotController()
        with self.assertRaises(RobotCommandError):
            robot.move("backward", 40)

    def test_rotate_is_limited(self) -> None:
        robot = RobotController()
        with self.assertRaises(RobotCommandError):
            robot.rotate(120)


if __name__ == "__main__":
    unittest.main()
