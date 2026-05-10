# Camera Servo Verification

本文记录根据网页摄像头图像反推云台舵机控制效果的验证结论，以及当前 `action_move` 的实现方法。

## 结论

当前网页图像上传链路正常，舵机控制命令也能发布到 ROS2 控制话题，但“摄像头随向左看/向右看/向上看/向下看明显转向”的实际效果尚未正确达成。

从图像结果看：

- `look_left` 和 `look_right` 都会触发新的图片上传，`task_id`、`frame_id`、时间水印会变化。
- 原始小幅度配置 `1200/1800` 下，左右两张图的明显变化像素约 `4.42%`，肉眼几乎是同一视角。
- 放大到 `1000/2000` 后，左右两张图明显变化像素仍约 `4.39%`，没有出现预期的大幅转向。
- 按教程源码线索测试 PWM 舵机 2 的 `800/2200` 后，摄像头画面变成全黑。
- 扫描 `servo1/servo2` 的 `1000/1500/2000` 九个组合后，图像仍为黑帧，亮度均值约 `0.39..0.40`。

因此，问题不是网页不更新，也不是拍照上传接口不生效，而是云台舵机映射/机械姿态/摄像头取景方向还没有校准正确。

## 证据文件

本地验证图片位于 `action_move` 目录下：

```text
_verify_look_left.jpg
_verify_look_right.jpg
_verify_wide_left.jpg
_verify_wide_right.jpg
_verify_wide_up.jpg
_verify_wide_down.jpg
_verify_pan_800.jpg
_verify_pan_2200.jpg
_verify_center_after_black.jpg
servo_scan/
```

关键图像现象：

- `_verify_wide_left.jpg` 和 `_verify_wide_right.jpg` 都能看到房间画面，但视角差异很小。
- `_verify_pan_800.jpg`、`_verify_pan_2200.jpg`、`_verify_center_after_black.jpg` 是黑帧，只剩时间水印。
- `servo_scan/` 中 9 个组合均为黑帧，说明不能靠简单中位恢复可视画面。

## 当前实现

技能定义在：

```text
action_move/skill_catalog.json
```

执行器在：

```text
action_move/action_move_executor.py
```

8 个大模型技能：

| 中文指令 | 技能 ID | 当前动作 |
| --- | --- | --- |
| 向左看 | `look_left` | 发布 PWM 舵机命令后触发摄像头截图 |
| 向右看 | `look_right` | 发布 PWM 舵机命令后触发摄像头截图 |
| 向上看 | `look_up` | 发布 PWM 舵机命令后触发摄像头截图 |
| 向下看 | `look_down` | 发布 PWM 舵机命令后触发摄像头截图 |
| 向前走 | `move_forward` | `/cmd_vel linear.x=0.12`，短时发布后停止 |
| 向后走 | `move_backward` | `/cmd_vel linear.x=-0.12`，短时发布后停止 |
| 向左走 | `move_left` | `/cmd_vel linear.y=0.10`，短时发布后停止 |
| 向右走 | `move_right` | `/cmd_vel linear.y=-0.10`，短时发布后停止 |

### 摄像头看向动作

执行器通过树莓派宿主机调用 Docker 容器内的 ROS2：

```bash
docker exec turbopi bash -lc \
  "source /opt/ros/humble/setup.bash && \
   source /home/ubuntu/ros2_ws/install/setup.bash && \
   ros2 topic pub --once /ros_robot_controller/pwm_servo/set_state \
   ros_robot_controller_msgs/msg/SetPWMServoState \
   '{duration: 0.35, state: [{id: [1], position: [1000], offset: []}]}'"
```

随后请求网页摄像头服务刷新图像：

```http
POST https://www.wangyutang.cn/camera/api/capture
Content-Type: application/json

{"mode":"single"}
```

### 底盘运动动作

底盘动作通过 `/cmd_vel` 发布短时 `Twist`，然后立即发布停止命令：

```bash
ros2 topic pub --times 6 --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

## 教程源码线索

教程中的 `face_tracking.py` 显示：

```text
servo_x range: 800..2200
servo_y range: 1000..1900
pwm_controller([1, servo_y], [2, servo_x])
```

这说明摄像头水平轴很可能是 PWM 舵机 2，垂直轴很可能是 PWM 舵机 1，而不是最初假设的“1 水平、2 垂直”。

但是按这个线索实际测试 PWM 舵机 2 的 `800/2200` 后，网页图像变成黑帧。因此还需要现场确认机械朝向和接线，不能只依赖源码默认映射。

## 问题判断

已排除：

- 云端接口不更新：每次动作后 `task_id`、`frame_id`、`updated_at` 都会变化。
- 树莓派不在线：`/camera/api/health` 显示 `turbopi-01` 在线。
- 摄像头上传服务完全失效：动作前能上传正常房间画面。
- ROS2 舵机话题不存在：容器内存在 `/ros_robot_controller/pwm_servo/set_state`，且发布命令成功。

待确认：

- 摄像头云台实际使用的是 PWM 舵机还是总线舵机。
- 摄像头水平/垂直轴分别接在哪个舵机编号。
- 当前物理姿态是否被转到遮挡区、线束是否拉住摄像头、摄像头是否贴近黑色物体。
- 舵机命令是否被上层节点或启动检查节点覆盖。

## 推荐校准方法

1. 现场观察摄像头云台，执行单个舵机的小步命令，例如 `servo1=1400/1600`、`servo2=1400/1600`，记录哪个舵机实际转动。
2. 不再先使用 `800/2200` 这种极限值，先用 `1400..1600` 找到可视方向。
3. 当网页恢复正常画面后，固定一个轴，只扫描另一个轴，记录每个值对应的图像方向。
4. 得到真实映射后再回写 `skill_catalog.json`：
   - 水平轴：`look_left` / `look_right`
   - 垂直轴：`look_up` / `look_down`
5. 每次修改后用图像差异验证，而不是只看 ROS 命令是否发布成功。

## 当前安全状态

最后已向 PWM 舵机 1 和 2 发布回中命令：

```text
servo1=1500
servo2=1500
```

但网页图像仍为黑帧，所以需要现场确认摄像头是否被遮挡或姿态是否已转到不可视区域。
