# 模块合入规范检查记录

日期：2026-05-05

检查范围：`wangyutang_platform` 下现有模块。

依据：[MODULE_MERGE_GUIDE.md](../MODULE_MERGE_GUIDE.md)

## 检查结论

现有模块已补齐模块 README、注册表关键字段、健康检查或替代验证说明。公网或容器化模块均已在 `control_platform/modules/registry.json` 中登记；边缘侧模块不作为公网服务独立部署，但已补充本地运行和验证要求；预研占位模块按扩展入口登记并说明例外。

## 模块检查表

| 模块 | README | 注册表 | 健康检查或替代验证 | Compose/Caddy | 结论 |
| --- | --- | --- | --- | --- | --- |
| `control_platform/` | 已有 | 平台自身服务 | `/api/health` | 已配置 | 符合 |
| `paper_learning_system/` | 已有 | `paper-learning` | `/api/health` | 已配置 | 符合 |
| `remote_control_cloud/` | 已有 | `remote-control` | `/api/health` | 已配置 | 符合 |
| `remote_control_edge/` | 已补齐 | 归属 `remote-control` | 本地服务、MQTT 桥、固件编译 | 不独立部署 | 符合 |
| `remote_sensing/` | 已有 | `remote-sensing` | `/api/health` | 已配置 | 符合 |
| `camera_snapshot/` | 已有 | `camera-snapshot` | `/api/health` | 已配置 | 符合 |
| `llm_manager/` | 已有 | `web-manager` | `/api/health`、`/api/modules` | 已配置 | 符合 |
| `pi5_robot/` | 已有 | `pi5-robot` | `/api/health` | 已配置 | 符合 |
| `pi_slam/` | 已补齐 | `pi-slam` | 预研占位，无运行服务 | 不独立部署 | 符合，按扩展入口管理 |

## 本次补齐

- 新增 `remote_control_edge/README.md`，明确边缘侧模块用途、本地运行、验证方式和密钥约束。
- 修正 `control_platform/modules/registry.json` 中 `remote-control` 和 `remote-sensing` 的 `local_url`。
- 保留 `future-systems` 作为扩展入口，允许 `service_url`、`health_url` 和 `image` 暂为空。
- 新增 `pi5_robot/` 可运行 MVP 模块，补齐 README、服务、健康检查、Compose、Caddy、注册表和合入记录。
- 新增 `pi_slam/README.md`，并将 `pi-slam` 按扩展入口登记，明确当前无运行服务。

## 合入准则满足情况

- [x] 模块 README 已检查并补齐。
- [x] 注册表关键字段已检查。
- [x] 健康检查或替代验证方式已明确。
- [x] Compose/Caddy 配置已检查。
- [x] 规划模块和边缘模块的例外情况已记录。
- [x] 未要求删除或迁移现有数据。

## 已知例外

- `future-systems` 是扩展入口，不是可运行服务，因此没有 `service_url`、`health_url` 和镜像。
- `pi-slam` 是预研占位模块，不是可运行服务，因此暂不提供 `service_url`、`health_url` 和镜像。
- `remote_control_edge/` 是本地硬件边缘侧模块，不提供公网路由和容器健康检查。
- `remote-control` 与 `remote-sensing` 当前公网子域仍可能依赖 DNS、证书或后续服务完善；合入状态分别保持为 `integration` 和 `scaffold`。
