# Pi5 Robot

Raspberry Pi 5 巡查机器人最小可运行工程。当前版本先落地“能看结构、能启动服务、能模拟控制、能记录任务”的 MVP 骨架，真实电机、相机和传感器接入点已经预留。

原始长方案保留在 [pi_harness_robot_readme.md](pi_harness_robot_readme.md)，拆分后的设计文档在 [docs/](docs/)。

## 当前状态

| 模块 | 状态 |
| --- | --- |
| Web 控制台 | 已实现，提供手动控制、状态查看、拍照占位、任务触发 |
| robotd | 已实现仿真控制器，包含限速、限距、避障、急停状态 |
| visiond | 已实现仿真拍照和场景描述 |
| harnessd | 已实现同步任务执行、JSONL 事件日志、Markdown 报告 |
| 固件 | 已提供 Arduino 串口协议占位 |
| 真实硬件 | 待接入，默认不会直接操作 GPIO |

## 快速启动

```powershell
cd C:\Users\Administrator\Desktop\Workspace\Project_Codex\wangyutang_platform\pi5_robot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn services.webui.app:app --host 0.0.0.0 --port 8093 --reload
```

打开：

```text
http://127.0.0.1:8093
```

树莓派上也可以使用：

```bash
cd pi5_robot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/start_all.sh
```

## API 快查

```text
GET  /api/health
GET  /api/robot/state
GET  /api/robot/safety
POST /api/robot/move
POST /api/robot/rotate
POST /api/robot/stop
POST /api/robot/servo/pan_tilt
POST /api/camera/capture
POST /api/vision/describe
POST /api/task
GET  /api/task/{task_id}/status
GET  /api/task/{task_id}/trace
POST /api/task/{task_id}/cancel
```

示例：

```powershell
Invoke-RestMethod http://127.0.0.1:8093/api/robot/state
Invoke-RestMethod http://127.0.0.1:8093/api/robot/move -Method Post -ContentType 'application/json' -Body '{"direction":"forward","distance_cm":20}'
Invoke-RestMethod http://127.0.0.1:8093/api/task -Method Post -ContentType 'application/json' -Body '{"task":"巡查门口区域，发现障碍物就停"}'
```

## 开发顺序

1. 先保证电源、急停、避障和手动控制可靠。
2. 再接入真实相机、编码器、IMU 和电机控制器。
3. 最后加入视觉识别、定位、追踪和 ROS 2 / Nav2。

更多细节：

- [架构设计](docs/architecture.md)
- [硬件接入](docs/hardware.md)
- [安全约束](docs/safety.md)
- [路线图](docs/roadmap.md)

## 验证

```powershell
python -m unittest discover -s tests
python -m compileall services tests
```
