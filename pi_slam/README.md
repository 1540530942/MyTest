# Pi SLAM

`pi_slam` 是 Raspberry Pi / 机器人导航方向的预研占位模块，用于后续沉淀 ROS 2、SLAM、Nav2、LiDAR 或深度相机相关实验。

当前目录还没有可运行服务，不提供独立 Web 页面、容器、健康检查或公网入口。它在平台中按扩展入口管理，避免与已经可运行的 `pi5_robot/` 混淆。

## 当前状态

| 项 | 状态 |
| --- | --- |
| 模块类型 | 预研 / 扩展入口 |
| 运行服务 | 暂无 |
| 健康检查 | 暂无，需等服务落地后补 `/api/health` |
| Compose/Caddy | 暂无，需等服务落地后补 |
| 数据目录 | 暂无，后续应独立管理地图、bag、标定和日志数据 |

## 后续准入要求

正式实现前需要补齐：

- 独立 `README.md` 的运行说明和接口说明。
- 明确 `/api/health` 或替代验证方式。
- 如容器化，补充 Dockerfile、Compose 服务和数据卷。
- 如接入公网，补充 Caddy 路由。
- 将状态从 `extension-point` 更新为 `scaffold` 或 `integration`。
