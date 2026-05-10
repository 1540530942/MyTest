# ROS2 Command Examples

These examples assume the robot is already running its normal bringup and has:

```text
/cmd_vel
/ros_robot_controller/set_motor_speeds
/ros_robot_controller/pwm_servo/set_state
/ros_robot_controller/bus_servo/set_position
```

Before running commands on the Raspberry Pi:

```bash
source /opt/ros/humble/setup.bash
source /home/ubuntu/ros2_ws/install/setup.bash
```

## Check Topics

```bash
ros2 topic list | grep -E 'cmd_vel|motor|servo'
ros2 topic info /cmd_vel
ros2 topic info /ros_robot_controller/pwm_servo/set_state
ros2 topic info /ros_robot_controller/set_motor_speeds
```

## Stop

Always keep this command nearby:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

## Forward And Backward

Forward for one publish:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Backward for one publish:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Timed forward, then stop:

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" &
PID=$!
sleep 1
kill $PID
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

## Turn Left / Turn Right

Turn left:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.35}}"
```

Turn right:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -0.35}}"
```

Forward while turning:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.10, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.30}}"
```

## Strafe Left / Right

Because this is a mecanum chassis, lateral movement is available through `linear.y`.

Strafe left:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.10, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Strafe right:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: -0.10, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

## Direct Motor Test

Use only for diagnostics:

```bash
ros2 topic pub --once /ros_robot_controller/set_motor_speeds ros_robot_controller_msgs/msg/MotorsSpeedControl "{data: [{id: 1, speed: 30.0}]}"
```

Stop all motors directly:

```bash
ros2 topic pub --once /ros_robot_controller/set_motor_speeds ros_robot_controller_msgs/msg/MotorsSpeedControl "{data: [{id: 1, speed: 0.0}, {id: 2, speed: 0.0}, {id: 3, speed: 0.0}, {id: 4, speed: 0.0}]}"
```

## PWM Servo Examples

Center PWM servo 1:

```bash
ros2 topic pub --once /ros_robot_controller/pwm_servo/set_state ros_robot_controller_msgs/msg/SetPWMServoState "{duration: 0.2, state: [{id: [1], position: [1500], offset: []}]}"
```

Move PWM servo 1 left/right around center:

```bash
ros2 topic pub --once /ros_robot_controller/pwm_servo/set_state ros_robot_controller_msgs/msg/SetPWMServoState "{duration: 0.3, state: [{id: [1], position: [1200], offset: []}]}"
ros2 topic pub --once /ros_robot_controller/pwm_servo/set_state ros_robot_controller_msgs/msg/SetPWMServoState "{duration: 0.3, state: [{id: [1], position: [1800], offset: []}]}"
```

Center PWM servos 1 and 2 together:

```bash
ros2 topic pub --once /ros_robot_controller/pwm_servo/set_state ros_robot_controller_msgs/msg/SetPWMServoState "{duration: 0.2, state: [{id: [1], position: [1500], offset: []}, {id: [2], position: [1500], offset: []}]}"
```

## Bus Servo Position Examples

Move bus servo 1:

```bash
ros2 topic pub --once /ros_robot_controller/bus_servo/set_position ros_robot_controller_msgs/msg/ServosPosition "{duration: 0.5, position: [{id: 1, position: 500}]}"
```

Move bus servos 1 and 2 together:

```bash
ros2 topic pub --once /ros_robot_controller/bus_servo/set_position ros_robot_controller_msgs/msg/ServosPosition "{duration: 0.5, position: [{id: 1, position: 500}, {id: 2, position: 500}]}"
```

## Suggested Web API Mapping

For a future `action_move` service, map user actions to short timed `/cmd_vel` bursts:

| API action | Twist |
| --- | --- |
| `stop` | `linear.x=0`, `linear.y=0`, `angular.z=0` |
| `forward` | `linear.x=0.12` |
| `backward` | `linear.x=-0.12` |
| `left` | `linear.y=0.10` |
| `right` | `linear.y=-0.10` |
| `turn_left` | `angular.z=0.35` |
| `turn_right` | `angular.z=-0.35` |

Recommended defaults:

```text
duration_ms: 300..800
publish_rate: 10 Hz
stop_after_each_action: true
```

