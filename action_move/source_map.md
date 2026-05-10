# Source Map

This file lists the tutorial files that matter for servo and movement control.

## Core Bringup

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\driver\controller\launch\controller.launch.py`

- Starts `ros_robot_controller`.
- Starts `controller.mecanum` as `mecanum_chassis_node`.
- This is the smallest launch file that explains the motion stack.

## Mecanum Chassis

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\driver\controller\controller\mecanum.py`

- Subscribes: `/cmd_vel`
- Publishes: `/ros_robot_controller/set_motor_speeds`
- Converts `Twist.linear.x`, `Twist.linear.y`, `Twist.angular.z` into four mecanum wheel speeds.
- Motor output order in current code: motor ids `1..4`, with signs `[-motor1, motor3, -motor2, motor4]`.

Older/alternate files:

- `controller\mecanum_old.py`
- `controller\mecanum1.py`, which listens to `/controller/cmd_vel` instead of `/cmd_vel`

Use the current `mecanum.py` path for the live robot unless the launch file changes.

## STM32 / Controller Bridge

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\driver\ros_robot_controller\ros_robot_controller\ros_robot_controller_node.py`

Important subscriptions:

```text
~/set_motor_speeds
~/pwm_servo/set_state
~/bus_servo/set_state
~/bus_servo/set_position
~/set_buzzer
~/set_led
~/set_rgb
~/set_oled
```

Because the node name is `ros_robot_controller`, the public topics are:

```text
/ros_robot_controller/set_motor_speeds
/ros_robot_controller/pwm_servo/set_state
/ros_robot_controller/bus_servo/set_state
/ros_robot_controller/bus_servo/set_position
```

Important functions:

- `set_motor_speeds_callback`: converts `MotorsSpeedControl` into `Board.set_motor_duty(data)`.
- `set_pwm_servo_state`: handles PWM servo position and offset.
- `set_bus_servo_position`: handles bus servo position.
- `set_bus_servo_state`: handles bus servo id, offset, limits, torque, stop.
- `get_bus_servo_state`: reads bus servo id, position, voltage, temp, limits, torque.
- `get_pwm_servo_state`: reads PWM servo position and offset.

## Message Definitions

Directory:

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\driver\ros_robot_controller_msgs\msg`

Relevant messages:

- `MotorSpeedControl.msg`: `id`, `speed`
- `MotorsSpeedControl.msg`: array of `MotorSpeedControl`
- `SetPWMServoState.msg`: array of `PWMServoState`, `duration`
- `PWMServoState.msg`: `id[]`, `position[]`, `offset[]`
- `ServosPosition.msg`: `duration`, array of `ServoPosition`
- `ServoPosition.msg`: `id`, `position`
- `BusServoState.msg`: bus servo id, position, offset, limits, torque, stop fields

## Hardware Test

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\bringup\scripts\hardware_test.py`

Shows compact examples for:

- PWM servo 1 and 2: `1200`, `1500`, `1800`
- Individual motor test: motor ids `1..4`, speed `45`

This file is useful as a minimal reference, but it exits after running a test sequence.

## Startup Check

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\bringup\bringup\startup_check.py`

Centers PWM servos:

```text
servo 1 -> 1500
servo 2 -> 1500
duration 0.2
```

Also publishes a buzzer sound.

## Keyboard Control

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\peripherals\peripherals\teleop_key_control.py`

Publishes `Twist` to `controller/cmd_vel`, not `/cmd_vel` by default.

Key mapping:

```text
w: forward
s: backward
a: turn left
d: turn right
empty key: zero angular velocity
```

If used with the current mecanum node, check launch remapping or publish directly to `/cmd_vel`.

## Joystick Control

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\peripherals\peripherals\joystick_control.py`

Publishes two paths:

- `/cmd_vel` as `Twist`
- `/ros_robot_controller/set_motor_speeds` directly

Joystick mapping:

```text
left stick y -> forward/backward
left stick x -> strafe left/right
right stick x -> rotate left/right
```

Default parameters:

```text
max_linear: 0.1
max_angular: 9.0
deadzone: 0.1
```

## Vision / Sign Examples

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\example\example\yolov5\yolov5_demo.py`

Simple mapping from labels to `Twist`:

```text
green -> forward
red -> backward
right -> turn right
left -> turn left
other -> stop
```

`2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\src\example\example\yolov5\signpost.py`

More complex traffic-sign and line-following example. Useful values:

```text
forward: linear.x 0.4..0.7
turn right: linear.x 0.5, angular.z -7.0 to -8.0
turn left: linear.x 0.5, angular.z 7.0 to 8.0
sharp right: linear.x 0.3, angular.z -9.0
sharp left: linear.x 0.3, angular.z 9.0
stop: zero Twist
```

These are aggressive values. For remote web control, start much lower.

## Servo GUI Utilities

Directories:

```text
2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\software\Servo_upper_computer
2501 TurboPi AI Large Model (RPi5) Source Code\turbopi_ros2\software\lab_tool
```

Relevant files:

- `main.py`
- `ServoCmd.py`
- `ros_robot_controller_sdk.py`
- `servo_config.yaml`

The UI exposes servo sliders in the `500..2500` range and stores offsets/configuration. Good for calibration reference, not needed for a simple web action API.

