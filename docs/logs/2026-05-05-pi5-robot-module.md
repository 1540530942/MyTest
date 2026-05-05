# Pi5 Robot 模块合入记录

## 模块合入说明

- 日期：2026-05-05
- 模块：`pi5_robot`
- 类型：新增
- 目的：将 Raspberry Pi 5 巡查机器人方案落地为可运行 MVP，提供仿真控制台、API、任务日志、配置和硬件接入骨架。
- 变更文件：`pi5_robot/`、`README.md`、`control_platform/modules/registry.json`、`docker-compose.yml`、`control_platform/infra/caddy/Caddyfile`
- 新增或变更接口：`GET /api/health`、`GET /api/robot/state`、`POST /api/robot/move`、`POST /api/robot/rotate`、`POST /api/robot/stop`、`POST /api/camera/capture`、`POST /api/vision/describe`、`POST /api/task`
- 新增或变更路由：本地 `http://127.0.0.1:8093/`，网关路径 `/robot/`
- 数据目录或数据卷：`episodes/`，容器卷 `pi5_robot_episodes`
- 环境变量：`PI5_ROBOT_IMAGE`、`PI5_ROBOT_PORT` 可选

## 合入准则满足情况

- [x] README 已更新
- [x] 注册表已更新
- [x] Compose 已更新
- [x] Caddy 已更新
- [x] 本地验证通过
- [x] 服务器验证未执行，本次仅推送代码
- [x] 不影响已有模块，未修改已有模块业务代码

## 验证结果

```text
python -m unittest discover -s tests
Ran 5 tests in 0.009s
OK

python -m compileall services tests
OK

GET http://127.0.0.1:8093/api/health
{"status":"ok","mode":"simulation","service":"pi5_robot"}
```

## 已知问题

- 真实 GPIO、电机、相机、编码器和 IMU 尚未接入，当前默认是安全仿真模式。
- GitHub CLI `gh` 未安装，因此本次无法自动创建草稿 PR。

## 下一步

- 接入真实相机。
- 将 `RobotController` 替换为串口硬件控制实现。
- 增加网关容器级验证和服务器部署验证。
