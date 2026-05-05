# 模块合入规范说明

本规范适用于 `wangyutang_platform` 下所有模块的新增、修改、部署和回滚。每次修改或新增模块时，必须记录修改内容，并在合入前明确说明已经满足哪些合入准则。

## 基本原则

1. 每次模块修改都要留下可追踪记录。
2. 每次新增模块都要明确模块边界、路由、健康检查、数据目录和部署方式。
3. 合入前必须完成本文件中的准入检查，不能只说明“已修改”。
4. 不能破坏已有模块的公网入口、本地入口、健康检查和数据卷。
5. 涉及服务器部署时，必须记录服务器改动、备份位置、验证结果和遗留风险。

## 必填记录

每次修改或新增模块后，必须在对应位置补充记录：

- 模块自己的 `README.md`
- 平台根目录 `README.md` 中的模块列表或运行说明
- `control_platform/modules/registry.json`
- 相关部署文件，例如 `docker-compose.yml`、`control_platform/infra/caddy/Caddyfile`
- 如有服务器部署，补充到 `docs/` 或 `docs/logs/` 中

记录内容至少包含：

- 修改日期
- 模块名称
- 修改人或执行人
- 修改目的
- 变更文件
- 新增或变更的接口
- 新增或变更的路由
- 本地验证结果
- 服务器验证结果，如已部署
- 已知问题和下一步计划

## 新增模块准入准则

新增模块必须满足以下条件，才能合入：

1. 有独立目录，例如 `new_module/`。
2. 有模块级 `README.md`，说明用途、运行方式、接口、路由和数据目录。
3. 有健康检查接口，优先使用 `/api/health`。
4. 已登记到 `control_platform/modules/registry.json`。
5. 已明确 `id`、`name`、`public_url`、`local_url`、`service_url`、`health_url`、`image`、`status`、`summary`、`capabilities`、`data_owner`。
6. 如需要容器运行，必须补充 `Dockerfile` 和 `docker-compose.yml` 服务配置。
7. 如需要公网访问，必须补充 Caddy 路由。
8. 如有持久化数据，必须使用明确的数据卷或数据目录，不能混放到其它模块数据里。
9. 本地启动和健康检查通过。
10. 不影响已有模块启动和访问。

## 修改已有模块准入准则

修改已有模块必须满足以下条件，才能合入：

1. 明确修改范围，避免顺手改无关模块。
2. 保留已有兼容入口，除非已经明确废弃计划。
3. 更新模块 README 中的行为说明。
4. 如接口、端口、路由、数据结构、环境变量发生变化，必须同步更新平台根 README、注册表、Compose 和 Caddy。
5. 涉及前端页面时，必须确认页面能打开，主要交互不报错。
6. 涉及后端时，必须至少完成语法检查和健康检查。
7. 涉及容器时，必须确认镜像能构建，容器能启动，健康检查能通过。
8. 涉及服务器时，必须先备份远端文件，再部署，再验证公网入口。
9. 不得删除用户数据、数据卷或历史配置，除非有明确备份和确认。

## 合入前检查清单

每次合入前必须逐项确认：

```text
[ ] 模块 README 已更新
[ ] 根目录 README 已更新，或确认无需更新
[ ] registry.json 已更新，或确认无需更新
[ ] docker-compose.yml 已更新，或确认无需更新
[ ] Caddyfile 已更新，或确认无需更新
[ ] 本地语法检查通过
[ ] 本地健康检查通过
[ ] 页面入口可打开，或确认该模块无页面
[ ] 新增/修改接口已验证
[ ] 未破坏已有模块入口
[ ] 如已部署服务器，远端文件已备份
[ ] 如已部署服务器，容器状态正常
[ ] 如已部署服务器，公网入口验证通过
[ ] 已记录已知问题和下一步计划
```

## 合入说明模板

每次新增或修改模块时，在提交说明、PR 描述、部署记录或对应日志中使用以下模板：

```markdown
## 模块合入说明

- 日期：
- 模块：
- 类型：新增 / 修改 / 修复 / 部署
- 目的：
- 变更文件：
- 新增或变更接口：
- 新增或变更路由：
- 数据目录或数据卷：
- 环境变量：

## 合入准则满足情况

- [ ] README 已更新
- [ ] 注册表已更新
- [ ] Compose 已更新或无需更新
- [ ] Caddy 已更新或无需更新
- [ ] 本地验证通过
- [ ] 服务器验证通过或未部署
- [ ] 不影响已有模块

## 验证结果

```text
填写实际命令和关键返回结果
```

## 已知问题

- 无 / 填写问题

## 下一步

- 填写下一步计划
```

## 推荐验证命令

本地检查：

```powershell
.\scripts\check-local.ps1
docker compose config --quiet
```

Python 模块检查：

```powershell
python -m compileall -q .\模块目录
```

公网接口检查示例：

```powershell
Invoke-WebRequest -Uri 'http://www.wangyutang.cn/web/api/health' -UseBasicParsing
Invoke-WebRequest -Uri 'http://www.wangyutang.cn/web/' -UseBasicParsing
```

服务器容器检查示例：

```bash
cd /root/control_platform
docker compose -f infra/docker-compose.platform.yml config --quiet
docker ps
docker logs --tail 80 web-manager
```

## 状态定义

`registry.json` 中的 `status` 字段建议使用：

- `ready`：已接入平台，页面和健康检查可用。
- `integration`：正在集成，主要链路尚未完全闭环。
- `scaffold`：已有骨架，功能仍在初始实现阶段。
- `extension-point`：预留扩展入口。
- `paused`：暂停维护或等待外部条件。
- `deprecated`：计划废弃，必须保留迁移说明。

## 严格要求

任何模块新增或修改，如果没有明确说明满足哪些合入准则，不视为完成合入。

任何服务器部署，如果没有备份路径和验证结果，不视为完成部署。

任何公网路由变更，如果没有验证新入口和兼容入口，不视为完成发布。
