# TurboPi Motion And Servo Control Notes

This directory summarizes the motion-control material found under:

`C:\Users\Administrator\Desktop\Workspace\Project_Raspberry\1. Tutorials-20260425T133855Z-3-001`

The useful control stack is ROS2 based. For normal application code, prefer publishing `geometry_msgs/msg/Twist` to `/cmd_vel`; the existing `controller.mecanum` node converts it into four motor speeds and sends them to the STM32 controller.

## Eight LLM Skills

The first tool layer is defined in `skill_catalog.json` and can be executed by `action_move_executor.py`.

| User phrase | Skill id | Hardware path |
| --- | --- | --- |
| 向左看 | `look_left` | PWM servo 1, pan left |
| 向右看 | `look_right` | PWM servo 1, pan right |
| 向上看 | `look_up` | PWM servo 2, tilt up |
| 向下看 | `look_down` | PWM servo 2, tilt down |
| 向前走 | `move_forward` | `/cmd_vel linear.x > 0` |
| 向后走 | `move_backward` | `/cmd_vel linear.x < 0` |
| 向左走 | `move_left` | `/cmd_vel linear.y > 0` |
| 向右走 | `move_right` | `/cmd_vel linear.y < 0` |

Dry-run a natural Chinese command:

```bash
python3 action_move_executor.py 向左看 --dry-run
```

Execute it on the Raspberry Pi host while the `turbopi` ROS container is running:

```bash
python3 action_move_executor.py 向左看
```

After a camera look skill finishes, the executor requests `https://www.wangyutang.cn/camera/api/capture` so the camera page can refresh to the new direction. Base movement does not trigger a capture by default; set `capture_after_move` in `skill_catalog.json` if that becomes useful.

The camera look skills currently assume PWM servo 1 is the pan axis and PWM servo 2 is the tilt axis. Safe starting positions are `1200`, `1500`, and `1800`; if the physical direction is reversed after calibration, swap the affected values in `skill_catalog.json`.

## Data Flow

```text
App / keyboard / joystick
  -> geometry_msgs/Twist on /cmd_vel
  -> controller.mecanum
  -> ros_robot_controller/set_motor_speeds
  -> ros_robot_controller_node
  -> Board.set_motor_duty(...)
  -> STM32 / motor driver
  -> four mecanum wheels
```

Servo control uses a separate path:

```text
App
  -> ros_robot_controller/pwm_servo/set_state
  -> ros_robot_controller_node
  -> Board.pwm_servo_set_position(...)
  -> PWM servo 1/2/...
```

There is also a bus-servo path:

```text
App
  -> ros_robot_controller/bus_servo/set_position
  -> ros_robot_controller_node
  -> Board.bus_servo_set_position(...)
  -> serial bus servos
```

## Movement By `/cmd_vel`

Topic:

```text
/cmd_vel
```

Message:

```text
geometry_msgs/msg/Twist
```

Field meaning on this robot:

| Action | `linear.x` | `linear.y` | `angular.z` |
| --- | ---: | ---: | ---: |
| Stop | `0` | `0` | `0` |
| Forward | positive | `0` | `0` |
| Backward | negative | `0` | `0` |
| Strafe left | `0` | positive | `0` |
| Strafe right | `0` | negative | `0` |
| Turn left | `0` | `0` | positive |
| Turn right | `0` | `0` | negative |
| Forward while turning left | positive | `0` | positive |
| Forward while turning right | positive | `0` | negative |

Conservative speed values to start with:

```text
linear.x: +/-0.10 to +/-0.20
linear.y: +/-0.10 to +/-0.20
angular.z: +/-0.30 to +/-0.50
```

The tutorial examples sometimes use much larger angular values such as `8.0` or `9.0`; use those only after testing in a clear area.

## Mecanum Conversion

The mecanum node subscribes to `/cmd_vel`, computes four wheel speeds, clamps them to `-100..100`, and publishes:

```text
/ros_robot_controller/set_motor_speeds
ros_robot_controller_msgs/msg/MotorsSpeedControl
```

The important formula from `controller/mecanum.py`:

```python
motor1 = linear_x - linear_y - angular_z * (wheelbase + track_width) / 2
motor2 = linear_x + linear_y - angular_z * (wheelbase + track_width) / 2
motor3 = linear_x + linear_y + angular_z * (wheelbase + track_width) / 2
motor4 = linear_x - linear_y + angular_z * (wheelbase + track_width) / 2
motor_speeds = [convert(-motor1), convert(motor3), convert(-motor2), convert(motor4)]
```

For web or API control, `/cmd_vel` is the cleanest entrypoint because it preserves this wheel mapping.

## Direct Motor Control

Topic:

```text
/ros_robot_controller/set_motor_speeds
```

Message:

```text
ros_robot_controller_msgs/msg/MotorsSpeedControl
```

Nested item:

```text
ros_robot_controller_msgs/msg/MotorSpeedControl
uint16 id
float64 speed
```

Motor ids are `1..4`. Speed is a floating value, usually in `-100..100`.

Use direct motor control only for diagnostics or low-level tests. For normal movement, use `/cmd_vel`.

## PWM Servo Control

Topic:

```text
/ros_robot_controller/pwm_servo/set_state
```

Message:

```text
ros_robot_controller_msgs/msg/SetPWMServoState
ros_robot_controller_msgs/PWMServoState[] state
float64 duration
```

Nested `PWMServoState`:

```text
uint16[] id
uint16[] position
int16[] offset
```

Observed safe center and test positions from tutorials:

```text
servo 1: 1200, 1500, 1800
servo 2: 1200, 1500, 1800
center: 1500
typical UI range: 500..2500
```

The startup check centers PWM servos 1 and 2 at `1500`.

## Bus Servo Control

Position topic:

```text
/ros_robot_controller/bus_servo/set_position
```

Message:

```text
ros_robot_controller_msgs/msg/ServosPosition
float64 duration
ros_robot_controller_msgs/ServoPosition[] position
```

Nested `ServoPosition`:

```text
uint16 id
uint16 position
```

State topic:

```text
/ros_robot_controller/bus_servo/set_state
```

This is for id changes, offsets, angle limits, voltage/temp limits, torque, stop, and saving offsets. Treat it as a calibration/maintenance interface.

## Existing Running Nodes To Expect

On the Raspberry Pi, the bringup launch commonly starts:

```text
ros_robot_controller
mecanum_chassis_node
```

The observed live process earlier was:

```text
/usr/bin/python3 /opt/ros/humble/bin/ros2 launch bringup bringup.launch.py
/usr/bin/python3 /home/ubuntu/ros2_ws/install/controller/lib/controller/mecanum
/usr/bin/python3 /home/ubuntu/ros2_ws/install/ros_robot_controller/lib/ros_robot_controller/ros_robot_controller
```

## Safety Rules

- Always send a stop command after a timed movement.
- Use low speed first: `linear.x = 0.10`, `angular.z = 0.30`.
- Do not publish high direct motor speeds unless the robot is lifted or the wheels are clear.
- Keep PWM servo values within a known range first: `1200..1800`, center at `1500`.
- Avoid calling bus-servo id/offset/limit setters unless intentionally calibrating hardware.
