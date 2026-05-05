# Gateway Startup Dependency Fix

## 模块合入说明

- 日期：2026-05-06
- 模块：`caddy` gateway / `pi5_robot`
- 类型：修复
- 目的：避免新增 `pi5-robot` 模块健康状态阻塞主网关启动，保证 `https://www.wangyutang.cn/` 首页不被可选机器人模块影响。
- 变更文件：`docker-compose.yml`
- 新增或变更接口：无
- 新增或变更路由：无
- 数据目录或数据卷：无
- 环境变量：无

## 合入准则满足情况

- [x] README 已更新或无需更新
- [x] 注册表已更新或无需更新
- [x] Compose 已更新
- [x] Caddy 已更新或无需更新
- [x] 本地验证通过
- [x] 服务器验证未执行，本次仅推送代码
- [x] 不影响已有模块

## 验证结果

```text
docker compose config --quiet
OK

Invoke-WebRequest https://www.wangyutang.cn/
StatusCode: 200
```

## 已知问题

- `pi5-robot` 仍是 scaffold 模块；其自身失败时 `/robot/` 可能不可用，但不应影响主站首页。

## 下一步

- 如部署服务器，重新 `docker compose up -d caddy` 或重新拉起整体 compose，并验证首页、`/web/`、`/camera/`、`/robot/`。
