# 平台模块合规刷新记录

## 模块合入说明

- 日期：2026-05-05
- 模块：`wangyutang_platform` 全量模块清单
- 类型：修改 / 修复
- 目的：按 `MODULE_MERGE_GUIDE.md` 重新检查 `wangyutang_platform` 下各模块，补齐新增模块和预研占位模块的登记、说明和审计记录。
- 变更文件：`README.md`、`control_platform/README.md`、`control_platform/modules/registry.json`、`docs/module-compliance-audit.md`、`pi_slam/README.md`
- 新增或变更接口：无新增接口；补充 `pi-slam` 扩展入口登记。
- 新增或变更路由：无新增可运行路由；`pi-slam` 仅使用 `/modules/` 扩展入口说明。
- 数据目录或数据卷：`pi_slam` 暂无数据目录；后续正式实现时需独立管理地图、bag、标定和日志数据。
- 环境变量：无新增。

## 合入准则满足情况

- [x] README 已更新
- [x] 注册表已更新
- [x] Compose 已更新或无需更新
- [x] Caddy 已更新或无需更新
- [x] 本地验证通过
- [x] 服务器验证未执行，本次仅推送代码
- [x] 不影响已有模块

## 验证结果

```text
python -m json.tool control_platform/modules/registry.json
OK

docker compose config --quiet
OK

python -m compileall control_platform camera_snapshot remote_sensing llm_manager paper_learning_system pi5_robot remote_control_cloud remote_control_edge
OK

模块入口导入检查：

control_platform.app.main -> OK
camera_snapshot.server -> OK
remote_sensing.app.main -> OK
llm_manager.app.main -> OK
paper_learning_system/app.main，按模块目录启动 -> OK
paper_learning_system.hermes_gateway.main -> OK
pi5_robot.services.webui.app -> OK
remote_control_cloud/cloud_api.app，按模块目录启动 -> OK
remote_control_edge/pc_controller/app，按模块目录启动 -> OK

pi5_robot 单元测试：

python -m unittest discover -s tests
Ran 5 tests
OK
```

## 已知问题

- `pi_slam` 仍是预研占位模块，尚未提供可运行服务。
- `remote_control_edge` 是边缘侧硬件模块，不提供平台容器健康检查。
- 当前机器未安装 `npm`，因此没有执行 `remote_control_cloud` 的 Vite 前端构建；Python 侧和 Compose 配置已验证。

## 下一步

- 正式开发 `pi_slam` 时补齐服务、健康检查、容器、数据卷和路由。
- 持续让 `control_platform/modules/registry.json` 与根目录模块列表保持一致。
