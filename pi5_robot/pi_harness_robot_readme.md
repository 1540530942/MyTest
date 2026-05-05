# Raspberry Pi Harness 巡查机器人执行方案 README

## 1. 项目定位

本项目旨在构建一套基于树莓派的移动巡查机器人系统。系统接入大模型 API，搭载摄像头、舵机云台、电机底盘、避障传感器等硬件，实现远程 Web 控制、自动巡查、室内定位、目标追踪、图像识别、任务日志记录与回放等能力。

本项目的核心不是让大模型直接控制电机，而是构建一套安全、可控、可观测、可回放的 Agent Harness 系统：

- 树莓派负责视觉采集、Web 服务、任务编排和大模型 API 调用；
- Arduino / Pico / ESP32 等辅助控制器负责电机、舵机、编码器和急停逻辑；
- 大模型负责高层任务理解、规划、视觉语义判断和报告生成；
- Harness 负责记录每一次感知、决策、工具调用、动作执行、异常和复盘。

一句话概括：

> 构建一个能够“看、想、走、停、查、记、复盘”的树莓派智能巡查机器人。

---

## 2. 建设目标

### 2.1 基础目标

完成一台可远程控制的树莓派移动小车，具备以下基础能力：

- 浏览器访问 Web 控制台；
- 实时查看摄像头画面；
- 手动控制前进、后退、左转、右转、停止；
- 控制舵机云台左右、上下转动；
- 拍照、录像、保存巡查图像；
- 读取距离传感器、IMU、电池等状态；
- 前方遇到障碍物自动停止；
- 所有动作和状态写入日志。

### 2.2 智能目标

在基础能力之上，接入大模型 API 和视觉能力，实现：

- 自然语言下发任务；
- 自动拆解任务步骤；
- 自动调用拍照、识别、移动、停止等工具；
- 对摄像头画面进行描述；
- 识别障碍物、人员、门窗状态、指定物体等；
- 自动生成巡查报告；
- 发现异常后拍照、记录位置和时间。

### 2.3 进阶目标

进一步实现：

- 基于编码器、IMU、视觉标记的室内定位；
- 基于 AprilTag / ArUco 的位置校正；
- 基于目标检测的低速目标跟随；
- 目标丢失后的云台搜索和重新捕获；
- 任务全过程回放；
- 巡查任务评测；
- 后续升级 ROS 2 / Nav2 / SLAM。

---

## 3. 总体架构

系统采用“高层智能 + 本地控制 + 安全兜底”的分层架构。

```text
用户 / 浏览器 / 手机 / 语音输入
        │
        ▼
Web 控制台
        │
        ▼
Agent Harness 任务编排层
        │
        ├── 大模型 API
        ├── 工具调用管理
        ├── 状态管理
        ├── 日志记录
        └── 任务复盘
        │
        ▼
技能层 Skill Layer
        │
        ├── 巡查 patrol
        ├── 定位 localize
        ├── 追踪 track
        ├── 搜索 search
        ├── 拍照 inspect
        └── 回家 return_home
        │
        ▼
本地控制层 Control Layer
        │
        ├── 电机控制
        ├── 舵机控制
        ├── 避障检测
        ├── 里程计
        ├── IMU 姿态
        └── 急停逻辑
        │
        ▼
硬件执行层 Hardware Layer
        │
        ├── 树莓派
        ├── 摄像头
        ├── 舵机云台
        ├── 电机底盘
        ├── 电机驱动板
        ├── 距离传感器
        └── 电池电源系统
```

### 3.1 核心设计原则

1. **大模型不直接控制 GPIO。**

   大模型只能调用受限工具，例如：

   ```json
   {
     "tool": "move_forward",
     "args": {
       "distance_cm": 30,
       "max_speed_mps": 0.2,
       "stop_if_obstacle": true
     }
   }
   ```

2. **所有移动动作必须经过安全检查。**

   每次前进、后退、转向前都应读取机器人状态和障碍物距离。

3. **实时控制不交给大模型。**

   追踪、避障、急停等高频控制由本地程序执行。

4. **所有关键过程必须落盘。**

   包括用户任务、传感器状态、图像、工具调用、大模型输出、执行结果、异常原因。

5. **系统必须支持人工接管。**

   包括 Web 停止按钮、实体急停按钮、任务取消接口。

---

## 4. 硬件方案

### 4.1 推荐硬件清单

| 模块 | 推荐配置 | 作用 |
|---|---|---|
| 主控 | Raspberry Pi 5，建议 8GB 或 16GB | 运行 Web 服务、相机、视觉、大模型 API 调用、日志系统 |
| 辅助控制器 | Arduino / Raspberry Pi Pico / ESP32 | 控制电机、舵机、编码器、急停逻辑 |
| 摄像头 | Raspberry Pi Camera Module 3 / USB 摄像头 / AI Camera | 前向视觉、拍照、识别、追踪 |
| 云台 | 二自由度舵机云台 | 实现左右、上下扫描 |
| 底盘 | 两轮差速或四轮差速小车 | 支持前进、后退、转向 |
| 电机 | 带编码器直流减速电机 | 支持里程计定位 |
| 电机驱动 | TB6612FNG / L298N / BTS7960 | 驱动左右轮电机 |
| 距离传感器 | 超声波 / ToF / 红外 / 可选 LiDAR | 避障和安全停车 |
| IMU | MPU6050 / BNO055 / ICM-20948 | 获取朝向和姿态 |
| 电池 | 独立供电方案 | 给树莓派和电机供电 |
| 急停 | 实体急停按钮 | 紧急切断运动控制 |

### 4.2 建议硬件连接拓扑

```text
Camera CSI / USB
        │
        ▼
┌────────────────────────┐
│ Raspberry Pi 5          │
│                        │
│ Web 控制台              │
│ Agent Harness           │
│ Vision 服务             │
│ 日志与回放              │
└───────────┬────────────┘
            │ USB Serial
            ▼
┌────────────────────────┐
│ Arduino / Pico / ESP32  │
│                        │
│ 电机 PID 控制            │
│ 舵机控制                │
│ 编码器读取              │
│ 急停逻辑                │
└───────┬────────┬───────┘
        │        │
        ▼        ▼
   电机驱动板   舵机云台
        │
        ▼
   轮子 / 底盘
```

### 4.3 电源注意事项

电源设计必须重视，否则树莓派容易重启、掉线或烧坏外设。

建议：

- 树莓派使用独立稳定电源；
- 电机使用独立电池或大电流电源；
- 树莓派与电机控制器共地；
- 电机电源线路加保险丝；
- 电机驱动板电流能力要大于电机峰值电流；
- 舵机不要直接从树莓派 5V 引脚大量取电；
- 电池电压低于阈值时禁止继续执行自动任务。

---

## 5. 软件架构

### 5.1 软件分层

```text
L4 任务层
    用户指令、大模型规划、任务报告

L3 Harness 层
    工具注册、工具调用、状态管理、日志、回放、评测

L2 Skill 层
    巡查、定位、搜索、追踪、拍照识别、返回起点

L1 控制层
    电机控制、舵机控制、避障、速度限制、急停

L0 硬件层
    相机、电机、编码器、IMU、距离传感器、电源
```

### 5.2 推荐技术栈

第一阶段不建议直接上 ROS 2，先用轻量方案快速跑通。

| 模块 | 推荐技术 |
|---|---|
| 后端服务 | Python + FastAPI |
| Web 页面 | HTML + JavaScript |
| 摄像头 | OpenCV / Picamera2 |
| 电机通信 | USB Serial |
| 控制固件 | Arduino C / MicroPython |
| 视觉识别 | OpenCV / YOLO / 大模型视觉 API |
| 大模型调用 | OpenAI 风格 API / 私有化模型 API |
| 日志 | JSONL + 图片文件 + Markdown 报告 |
| 配置 | YAML |
| 后期导航 | ROS 2 + Nav2 + SLAM |

---

## 6. 代码工程结构

建议项目目录如下：

```text
pi_harness_robot/
  README.md

  configs/
    robot.yaml
    tools.yaml
    safety.yaml
    patrol_routes.yaml
    markers.yaml

  services/
    robotd/
      main.py
      motor_controller.py
      servo_controller.py
      serial_protocol.py
      odometry.py
      imu.py
      safety_guard.py

    visiond/
      main.py
      camera.py
      detector.py
      tracker.py
      marker_localizer.py
      scene_describer.py

    harnessd/
      main.py
      planner.py
      tool_registry.py
      executor.py
      memory.py
      logger.py
      replay.py
      report.py

    webui/
      app.py
      static/
        index.html
        app.js
        style.css
      templates/

  firmware/
    motor_controller/
      motor_controller.ino

  episodes/
    .gitkeep

  scripts/
    start_robotd.sh
    start_visiond.sh
    start_harnessd.sh
    start_all.sh

  tests/
    test_tools.py
    test_safety.py
    test_serial.py
    test_replay.py
```

---

## 7. Web 控制台设计

### 7.1 Web 控制台定位

Web 控制台是机器人系统的浏览器驾驶舱。用户通过手机、笔记本或平板访问树莓派 IP，即可完成远程控制、查看画面、下发 AI 任务和查看日志。

访问示例：

```text
http://树莓派IP:8000
```

### 7.2 Web 控制台功能

第一版建议包含以下区域：

```text
┌──────────────────────────────┐
│ Raspberry Pi Harness Robot    │
├──────────────────────────────┤
│ 实时摄像头画面                 │
├──────────────────────────────┤
│ 手动控制                       │
│        前进                    │
│ 左转   停止   右转              │
│        后退                    │
├──────────────────────────────┤
│ 舵机云台控制                   │
│ 左看 / 右看 / 上看 / 下看        │
├──────────────────────────────┤
│ 状态信息                       │
│ 电量 / 障碍物距离 / 当前模式     │
├──────────────────────────────┤
│ AI 任务输入                    │
│ 输入自然语言任务并执行           │
├──────────────────────────────┤
│ 任务日志                       │
│ 工具调用 / 传感器状态 / 异常记录 │
└──────────────────────────────┘
```

### 7.3 第一版按钮

必须包含：

- 前进；
- 后退；
- 左转；
- 右转；
- 停止；
- 云台左转；
- 云台右转；
- 云台上仰；
- 云台下俯；
- 拍照；
- 识别当前画面；
- 执行巡查任务；
- 取消任务；
- 急停。

---

## 8. 后端服务设计

### 8.1 robotd：机器人控制服务

负责硬件控制和安全状态。

主要能力：

- 电机控制；
- 舵机控制；
- 编码器读取；
- IMU 读取；
- 障碍物距离读取；
- 低电量检测；
- 急停状态检测；
- 运动安全检查。

建议接口：

```text
GET  /robot/state
GET  /robot/odom
GET  /robot/safety
POST /robot/move
POST /robot/rotate
POST /robot/stop
POST /robot/servo/pan_tilt
```

状态示例：

```json
{
  "pose": {
    "x": 1.25,
    "y": 0.42,
    "theta": 90.0,
    "confidence": 0.72
  },
  "battery": 78,
  "obstacle": {
    "front_cm": 63,
    "left_cm": 120,
    "right_cm": 95
  },
  "motion": {
    "mode": "idle",
    "linear_speed": 0.0,
    "angular_speed": 0.0
  },
  "safety": {
    "e_stop": false,
    "network_ok": true,
    "llm_allowed": true
  }
}
```

### 8.2 visiond：视觉服务

负责摄像头和视觉识别。

主要能力：

- 实时视频流；
- 拍照；
- 目标检测；
- 场景描述；
- 目标追踪；
- AprilTag / ArUco 标记识别；
- 异常图像保存。

建议接口：

```text
GET  /camera/stream
POST /camera/capture
POST /vision/detect
POST /vision/describe
POST /vision/find_target
POST /vision/read_marker
```

视觉输出示例：

```json
{
  "objects": [
    {
      "label": "person",
      "confidence": 0.91,
      "bbox": [320, 140, 510, 430],
      "center": [415, 285],
      "distance_estimate_m": 1.8
    }
  ],
  "scene": "front corridor, one person, no visible obstacle",
  "risk": "low"
}
```

### 8.3 harnessd：Agent Harness 服务

负责自然语言任务、工具调用、日志记录和复盘。

主要能力：

- 接收用户任务；
- 调用大模型 API；
- 生成任务计划；
- 调用受限工具；
- 执行安全检查；
- 保存事件日志；
- 生成报告；
- 支持任务回放。

建议接口：

```text
POST /task
GET  /task/{id}/status
GET  /task/{id}/trace
POST /task/{id}/cancel
POST /task/{id}/replay
```

任务输入示例：

```json
{
  "task": "巡查客厅一圈，检查地上有没有障碍物，发现人就保持一米距离跟随 30 秒。",
  "mode": "supervised_autonomy",
  "safety_level": "strict"
}
```

---

## 9. Agent 工具设计

### 9.1 第一版工具

最小可用版本只需要 6 个工具：

```text
get_robot_state
capture_image
describe_scene
move_forward
rotate
stop
```

这 6 个工具可以实现：

- 查看当前状态；
- 拍照；
- 描述画面；
- 小范围移动；
- 原地旋转；
- 安全停止。

### 9.2 第二版工具

增加巡查和定位能力：

```text
detect_objects
pan_camera
localize
mark_event
patrol_route
generate_report
```

### 9.3 第三版工具

增加追踪和搜索能力：

```text
find_target
track_target
search_target
return_home
ask_human_confirm
compare_with_baseline
```

### 9.4 工具调用约束

所有运动工具必须限制范围。

例如：

```json
{
  "tool": "move_forward",
  "args_schema": {
    "distance_cm": {
      "type": "number",
      "minimum": 1,
      "maximum": 50
    },
    "max_speed_mps": {
      "type": "number",
      "minimum": 0.05,
      "maximum": 0.3
    },
    "stop_if_obstacle": {
      "type": "boolean",
      "default": true
    }
  }
}
```

---

## 10. 巡查功能设计

### 10.1 巡查流程

```text
接收用户任务
  ↓
读取巡查路线
  ↓
定位当前位置
  ↓
前往第一个巡查点
  ↓
云台左右扫描
  ↓
拍照 / 目标检测 / 场景描述
  ↓
大模型判断是否异常
  ↓
记录图片、位置、时间、异常说明
  ↓
前往下一个巡查点
  ↓
生成巡查报告
```

### 10.2 巡查点配置示例

```yaml
route_name: living_room_patrol
waypoints:
  - id: door
    name: 门口
    pose: [0.0, 0.0, 0]
    actions:
      - pan_scan
      - capture
      - detect_obstacle

  - id: window
    name: 窗边
    pose: [1.5, 0.3, 90]
    actions:
      - capture
      - check_window_open

  - id: desk
    name: 桌子旁
    pose: [2.2, 1.1, 180]
    actions:
      - capture
      - detect_person
      - detect_object_change
```

### 10.3 异常类型

| 异常类型 | 判断方式 |
|---|---|
| 地面障碍物 | 距离传感器 + 图像识别 + 大模型判断 |
| 人员出现 | 目标检测 |
| 门窗状态变化 | 图像对比 + 大模型判断 |
| 指定物品不在 | 图像匹配 / 目标检测 |
| 路线被挡 | 距离传感器 + 图像判断 |
| 光线异常 | 图像亮度统计 |
| 设备状态异常 | 仪表识别 / OCR / 指示灯识别 |

---

## 11. 定位功能设计

### 11.1 阶段一：弱定位

使用：

```text
轮速编码器 + IMU + 人工标定起点
```

能力：

- 知道从起点大概走了多远；
- 知道大致转向角度；
- 支持短距离巡查。

缺点：

- 轮子打滑会导致误差；
- 时间越长漂移越大；
- 不适合复杂路径。

### 11.2 阶段二：视觉标记辅助定位

在室内关键位置贴 AprilTag / ArUco 标记。

机器人看到标记后，可以根据标记 ID 修正自身位置。

示例：

```yaml
markers:
  - id: marker_01
    name: 客厅门口
    pose: [0.0, 0.0, 0]

  - id: marker_02
    name: 窗边
    pose: [1.8, 0.5, 90]

  - id: marker_03
    name: 桌子旁
    pose: [2.4, 1.2, 180]
```

推荐定位组合：

```text
轮速里程计连续估计位置
IMU 辅助估计朝向
AprilTag / ArUco 周期性校正位置
```

这是第一版最推荐的室内定位方案。

### 11.3 阶段三：SLAM 定位

后期增加：

- 2D LiDAR；
- 深度相机；
- ROS 2；
- SLAM；
- Nav2。

实现：

```text
建图 → 定位 → 路径规划 → 避障 → 到点巡查
```

---

## 12. 追踪功能设计

### 12.1 设计原则

目标追踪不能让大模型逐帧决策。

正确做法：

```text
视觉检测模型负责每秒多次识别目标
本地 PID 控制负责跟随
大模型只负责选择目标、解释任务、处理异常策略
```

### 12.2 追踪状态机

```text
IDLE 空闲
  ↓
ACQUIRE_TARGET 捕获目标
  ↓
FOLLOWING 跟随中
  ↓
TARGET_LOST 目标丢失
  ↓
SEARCHING 原地搜索
  ↓
REACQUIRE 重新捕获
  ↓
DONE / FAILED
```

### 12.3 跟随逻辑

如果目标在画面偏左：

```text
小车慢速左转
```

如果目标在画面偏右：

```text
小车慢速右转
```

如果目标太远：

```text
小车慢速前进
```

如果目标太近：

```text
小车停止或后退
```

如果目标丢失：

```text
停车 → 云台扫描 → 重新识别 → 重新跟随或结束任务
```

### 12.4 追踪安全约束

必须设置：

```text
最大跟随速度 ≤ 0.3 m/s
最小安全距离 ≥ 0.8 m
前方障碍距离 < 40 cm 必停
目标丢失超过 5 秒必停
只允许追踪用户明确指定的目标
追踪过程中允许人工随时停止
```

---

## 13. Harness 日志与回放设计

### 13.1 Episode 目录结构

每一次任务保存为一个 episode。

```text
episodes/
  patrol_20260505_001/
    metadata.yaml
    events.jsonl
    states.jsonl
    tool_calls.jsonl
    frames/
      000001.jpg
      000002.jpg
    videos/
      front.mp4
    report.md
    replay.html
```

### 13.2 events.jsonl 示例

```json
{"t": 0.0, "event": "task_received", "text": "巡查客厅"}
{"t": 0.2, "event": "state", "battery": 82, "pose": [0, 0, 0]}
{"t": 1.0, "event": "tool_call", "tool": "capture_image"}
{"t": 1.4, "event": "vision_result", "objects": ["chair", "person"]}
{"t": 2.0, "event": "tool_call", "tool": "move_forward", "distance_cm": 30}
{"t": 3.2, "event": "safety_stop", "reason": "front obstacle 28cm"}
{"t": 3.5, "event": "llm_replan", "decision": "rotate right and bypass"}
```

### 13.3 日志必须记录的内容

- 用户原始任务；
- 大模型规划结果；
- 每一次工具调用；
- 工具参数；
- 工具执行结果；
- 执行前机器人状态；
- 执行后机器人状态；
- 摄像头图片；
- 视觉识别结果；
- 异常事件；
- 人工接管事件；
- 最终任务报告。

### 13.4 日志价值

日志用于回答以下问题：

- 小车为什么停了？
- 大模型为什么调用这个动作？
- 当时摄像头看到了什么？
- 传感器是否异常？
- 是规划错误、视觉错误，还是控制错误？
- 是否可以构造评测集和回归测试？

---

## 14. 安全设计

### 14.1 硬件安全

必须实现：

- 实体急停按钮；
- 电机独立供电；
- 树莓派独立稳压供电；
- 电机与树莓派共地；
- 电源过流保护；
- 电池低压保护；
- 舵机独立供电；
- 电机驱动散热。

### 14.2 软件安全

必须实现：

- 动作超时自动停止；
- 前方距离过近自动停止；
- LLM 超时自动停止；
- 网络断开自动停止；
- 工具参数越界拒绝执行；
- 低电量拒绝远距离任务；
- 定位置信度低时禁止长距离移动；
- 连续动作之间必须重新读取传感器；
- 自动任务期间允许人工随时接管。

### 14.3 大模型安全约束

系统提示词中必须明确：

```text
你是机器人任务规划 Agent。
你不能直接控制 GPIO。
你只能调用系统提供的工具。
每次移动前必须查询机器人状态。
如果前方障碍物距离小于安全阈值，必须停止。
如果定位置信度低，不允许执行长距离移动。
如果工具返回失败，必须重新规划或请求人工接管。
追踪任务必须保持安全距离。
禁止高速移动。
禁止连续执行多个运动命令而不检查状态。
```

---

## 15. 配置文件示例

### 15.1 robot.yaml

```yaml
robot:
  name: pi-harness-01
  drive_type: differential
  wheel_diameter_cm: 6.5
  wheel_base_cm: 14.0
  max_speed_mps: 0.3
  max_angular_speed_dps: 60

serial:
  port: /dev/ttyACM0
  baudrate: 115200

camera:
  type: picamera2
  resolution: [1280, 720]
  fps: 15

servo:
  pan_range: [-90, 90]
  tilt_range: [-35, 45]

safety:
  front_stop_distance_cm: 35
  side_stop_distance_cm: 20
  command_timeout_ms: 500
  require_obstacle_check: true
```

### 15.2 tools.yaml

```yaml
tools:
  move_forward:
    max_distance_cm: 50
    require_clear_path: true
    timeout_s: 5

  move_backward:
    max_distance_cm: 30
    timeout_s: 5

  rotate:
    max_angle_deg: 90
    timeout_s: 5

  pan_camera:
    pan_min: -90
    pan_max: 90
    tilt_min: -35
    tilt_max: 45

  track_target:
    max_duration_s: 60
    max_speed_mps: 0.25
    min_distance_m: 0.8
```

### 15.3 safety.yaml

```yaml
safety:
  emergency_stop_enabled: true
  max_linear_speed_mps: 0.3
  max_angular_speed_dps: 60
  front_stop_distance_cm: 35
  front_slow_distance_cm: 80
  target_lost_timeout_s: 5
  llm_timeout_s: 30
  command_timeout_ms: 500
  min_battery_percent_for_auto_task: 30
  require_state_check_before_motion: true
  allow_manual_override: true
```

---

## 16. 部署步骤

### 16.1 树莓派系统准备

1. 安装 Raspberry Pi OS；
2. 开启 SSH；
3. 配置 Wi-Fi；
4. 更新系统；
5. 安装 Python 环境；
6. 启用摄像头；
7. 配置静态 IP 或固定 DHCP 地址；
8. 确认电脑可以访问树莓派。

示例：

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

### 16.2 创建项目环境

```bash
git clone <your_repo_url> pi_harness_robot
cd pi_harness_robot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 16.3 启动服务

第一版可以先只启动一个总服务：

```bash
python services/webui/app.py
```

后期拆分为：

```bash
bash scripts/start_robotd.sh
bash scripts/start_visiond.sh
bash scripts/start_harnessd.sh
```

或者：

```bash
bash scripts/start_all.sh
```

### 16.4 浏览器访问

```text
http://树莓派IP:8000
```

---

## 17. 阶段实施计划

### 阶段一：能看、能动、能停

目标：完成最小可用小车。

任务：

- 树莓派系统安装；
- 摄像头画面采集；
- Web 控制台页面；
- 电机驱动调试；
- 前进、后退、左转、右转、停止；
- 舵机云台控制；
- 距离传感器避障；
- 动作日志记录。

验收标准：

- 浏览器能看到实时画面；
- 浏览器能控制小车移动；
- 点击停止后小车立即停止；
- 前方障碍物距离低于阈值时自动停止；
- 所有操作写入日志。

### 阶段二：能拍照识别、能简单巡查

目标：接入大模型 API，实现简单巡查。

任务：

- 接入大模型 API；
- 实现 capture_image 工具；
- 实现 describe_scene 工具；
- 实现简单目标检测；
- 配置固定巡查点；
- 自动拍照；
- 生成 Markdown 巡查报告。

验收标准：

- 输入“巡查房间一圈”后，机器人能执行几个固定动作；
- 能拍摄巡查图片；
- 能描述当前画面；
- 能输出一份简单巡查报告。

### 阶段三：能定位、能找目标

目标：实现室内弱定位和视觉标记校正。

任务：

- 调试编码器；
- 读取 IMU；
- 实现里程计；
- 粘贴 AprilTag / ArUco 标记；
- 配置 marker 地图；
- 实现 localize 工具；
- 实现 search_target 工具。

验收标准：

- 机器人能输出当前大致位置；
- 看到视觉标记后能校正位置；
- 机器人迷路后能通过原地扫描寻找标记；
- 定位信息能写入任务日志。

### 阶段四：能追踪

目标：实现指定目标的低速安全跟随。

任务：

- 实现 person / object 检测；
- 实现目标框中心跟随；
- 实现距离保持；
- 实现目标丢失搜索；
- 实现追踪安全限制；
- 记录追踪日志。

验收标准：

- 机器人能跟随指定目标；
- 能保持安全距离；
- 目标丢失后能停止并搜索；
- 前方有障碍物时自动停止；
- 追踪过程可回放。

### 阶段五：ROS 2 / Nav2 升级

目标：升级为更标准的机器人导航系统。

任务：

- 接入 ROS 2；
- 发布 odom topic；
- 发布 camera topic；
- 接入 LiDAR 或深度相机；
- 建图；
- 定位；
- 路径规划；
- Nav2 导航；
- Harness 调用 ROS action。

验收标准：

- 能完成室内地图构建；
- 能在地图上导航到指定点；
- 能避开障碍；
- Harness 能调用导航能力执行巡查任务。

---

## 18. 第一版 MVP 范围

第一版不要做太大。建议先完成：

```text
树莓派 5
+ 摄像头
+ 两轮差速底盘
+ Arduino / Pico 电机控制
+ 前向距离传感器
+ 二自由度舵机云台
+ Web 控制台
+ Python FastAPI
+ 大模型 API
+ JSONL 日志
```

第一版只开放 6 个工具：

```text
get_state
capture_image
describe_scene
move_forward
rotate
stop
```

第一版能完成的任务：

```text
向前走一点，看看前面有什么。
拍照并描述当前画面。
巡查门口区域。
发现障碍物就停。
生成一次简单巡查记录。
```

---

## 19. 典型任务流程

### 19.1 巡查任务

用户输入：

```text
巡查客厅一圈，检查地上有没有障碍物。
```

系统执行：

```text
1. get_robot_state
2. localize
3. move_forward 30cm
4. capture_image
5. detect_objects
6. describe_scene
7. rotate 45°
8. capture_image
9. detect_objects
10. mark_event
11. generate_report
```

输出：

```text
巡查完成。
共检查 5 个视角，发现 1 个疑似障碍物，位于客厅门口右侧，距离约 1.2 米。
已保存图片和日志。
```

### 19.2 定位任务

用户输入：

```text
你现在在哪？
```

系统执行：

```text
1. 获取里程计
2. 获取 IMU 朝向
3. 云台扫描寻找视觉标记
4. 如果识别到 marker，则校正位置
5. 返回坐标和置信度
```

输出：

```text
我当前位于客厅门口附近，距离初始点约 1.8 米，朝向东侧。
定位置信度 0.76。最近一次视觉标记校正来自 marker_02。
```

### 19.3 追踪任务

用户输入：

```text
跟随前面那个人，保持一米距离。
```

系统执行：

```text
1. detect_objects: person
2. ask_human_confirm: 是否追踪画面中的人
3. track_target: person_1
4. 本地视觉闭环跟随
5. 遇障停止
6. 目标丢失后云台搜索
7. 超时结束
```

输出：

```text
已跟随 30 秒，期间保持约 0.9 至 1.3 米距离。
中途出现一次目标短暂丢失，已重新捕获。
未发生碰撞风险。
```

---

## 20. 开发优先级

建议严格按照以下顺序开发：

```text
1. 硬件能稳定供电
2. 树莓派能稳定联网
3. 摄像头能出图
4. Web 页面能访问
5. 小车能手动控制
6. 停止按钮和急停可靠
7. 障碍物距离能读取
8. 遇障自动停止
9. 动作日志能保存
10. 大模型 API 能调用
11. 图像能发送给大模型识别
12. 自然语言能触发工具
13. 固定路线巡查
14. 视觉标记定位
15. 目标追踪
16. ROS 2 / SLAM 升级
```

不要一开始就做复杂的自主导航。先让系统可控、可停、可观察，再逐步增加智能能力。

---

## 21. 风险与应对

| 风险 | 表现 | 应对 |
|---|---|---|
| 电源不稳定 | 树莓派重启、相机掉线 | 树莓派和电机独立供电，增加稳压模块 |
| 电机控制不准 | 走偏、转向角不准 | 使用编码器，做 PID，低速调试 |
| 定位漂移 | 走一段后位置不准 | 使用 AprilTag / ArUco 周期性校正 |
| 大模型延迟高 | 任务响应慢 | 实时控制放本地，大模型只做高层决策 |
| 视觉识别不稳定 | 漏检、误检 | 本地检测 + 大模型复核 + 人工确认 |
| 小车撞障碍物 | 避障不及时 | 距离传感器硬约束 + 急停 + 限速 |
| 日志缺失 | 难以复盘问题 | 所有工具调用和状态变化写入 JSONL |
| 网络断开 | 无法远程控制 | 网络断开自动停车，保留实体急停 |

---

## 22. 最终系统形态

完成后，系统应具备以下能力：

- 通过浏览器查看机器人摄像头画面；
- 通过浏览器手动控制机器人；
- 通过自然语言下发巡查任务；
- 机器人自动移动、拍照、识别、记录；
- 机器人知道自己的大致位置；
- 机器人可以识别和低速跟随指定目标；
- 遇到障碍物、低电量、定位不确定、模型超时等情况会自动停车；
- 每一次任务都生成完整日志和报告；
- 所有任务可以回放和复盘；
- 后续可以平滑升级到 ROS 2、SLAM 和更复杂的多 Agent Harness。

---

## 23. 项目一句话总结

本项目不是简单地“树莓派接大模型控制小车”，而是构建一个以树莓派为边缘计算核心、以辅助控制器为实时安全控制核心、以大模型为任务规划和语义理解核心、以 Harness 为全过程记录和复盘核心的智能巡查机器人系统。

最终目标是让机器人具备：

```text
可远程控制
可自动巡查
可室内定位
可目标追踪
可安全停车
可日志回放
可持续迭代
```

这套架构既能快速做出第一版 MVP，也能为后续升级到完整机器人导航系统和 Agentic RL 实验平台打基础。
