# Implementation Plan For `action_move`

This is a practical plan for turning the tutorial findings into a web-controlled movement module.

## Recommended Architecture

```text
Web page / API
  -> Tencent cloud action_move service
  -> Raspberry Pi polling agent or SSH bridge
  -> ROS2 publish /cmd_vel or servo topic
  -> existing robot bringup
```

For the current platform style, the safest pattern is the same as `camera_snapshot`: the Raspberry Pi actively polls cloud tasks and executes them locally. This avoids needing inbound access to the Pi.

## Minimal Command Set

Movement:

```text
stop
forward
backward
strafe_left
strafe_right
turn_left
turn_right
```

Servo:

```text
pwm_servo_center
pwm_servo_set
bus_servo_set
```

## Task Schema Sketch

```json
{
  "id": "task-id",
  "type": "move",
  "action": "forward",
  "linear_x": 0.12,
  "linear_y": 0.0,
  "angular_z": 0.0,
  "duration_ms": 500,
  "status": "pending"
}
```

PWM servo task:

```json
{
  "id": "task-id",
  "type": "pwm_servo",
  "servo_id": 1,
  "position": 1500,
  "duration_ms": 300,
  "status": "pending"
}
```

## Raspberry Pi Executor Logic

1. Poll `/api/action_move/control`.
2. If task is `move`, publish `Twist` to `/cmd_vel` at 10 Hz for `duration_ms`.
3. Publish a zero `Twist` after every movement.
4. If task is `pwm_servo`, publish `SetPWMServoState`.
5. If task is `bus_servo`, publish `ServosPosition`.
6. Report task result and recent robot status back to cloud.

## Python ROS2 Publisher Skeleton

```python
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class MoveExecutor(Node):
    def __init__(self):
        super().__init__("action_move_executor")
        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)

    def publish_twist_for(self, x: float, y: float, z: float, duration: float):
        msg = Twist()
        msg.linear.x = x
        msg.linear.y = y
        msg.angular.z = z
        end_at = time.time() + duration
        while time.time() < end_at:
            self.cmd_vel_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.01)
            time.sleep(0.1)
        self.stop()

    def stop(self):
        self.cmd_vel_pub.publish(Twist())
```

## Safety Defaults

```text
max_abs_linear_x: 0.20
max_abs_linear_y: 0.15
max_abs_angular_z: 0.50
max_duration_ms: 1500
always_stop_after_move: true
reject_continuous_move_without_deadman: true
```

## Notes From Current Robot

- `/cmd_vel` is the correct high-level movement topic for the live mecanum node.
- `controller/cmd_vel` appears in keyboard launch/examples; use it only when launch remapping is active.
- Servo PWM center is `1500`.
- PWM servo UI range is `500..2500`, but first remote-control version should restrict to `1000..2000` or `1200..1800`.
- Direct motor topic should be hidden from user-facing controls except diagnostics.

