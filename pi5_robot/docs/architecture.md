# 架构设计

系统采用“高层智能 + 本地控制 + 安全兜底”的分层结构。

```text
Web 控制台
  |
  v
harnessd 任务编排
  |-- 大模型 API 接入点
  |-- 工具调用与任务日志
  |-- 报告与回放
  v
skill layer
  |-- patrol
  |-- localize
  |-- track
  |-- inspect
  v
robotd / visiond
  |-- 电机与舵机控制
  |-- 相机与视觉识别
  |-- 里程计、IMU、距离传感器
  v
硬件执行层
```

## 已落地的 MVP

- `services/webui/app.py`：统一 FastAPI 入口和静态控制台。
- `services/robotd/simulator.py`：仿真机器人控制器。
- `services/visiond/simulator.py`：仿真拍照和场景描述。
- `services/harnessd/executor.py`：任务执行器。
- `services/harnessd/logger.py`：episode 日志与报告。

MVP 默认使用仿真模式，不访问 GPIO，也不会向串口发送运动指令。

## 后续接入点

真实硬件接入时优先替换：

- `RobotController.move`
- `RobotController.rotate`
- `RobotController.stop`
- `RobotController.pan_tilt`
- `VisionService.capture`
- `VisionService.describe_scene`

替换时保留现有方法签名，Web API 和任务执行器就不需要大改。
