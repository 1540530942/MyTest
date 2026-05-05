# Primary Gateway Module Routes

## 模块合入说明

- 日期：2026-05-06
- 模块：`control_platform` Caddy gateway and module registry
- 类型：修改
- 目的：确保 `wangyutang_platform` 下的可运行模块都能通过 `https://www.wangyutang.cn` 和 `http://110.40.154.41` 两个主入口访问。
- 变更文件：`control_platform/infra/caddy/Caddyfile`、`control_platform/modules/registry.json`、`README.md`、`control_platform/README.md`、`remote_control_cloud/index.html`、`remote_control_cloud/src/main.js`
- 新增或变更接口：无新增 API；补齐路径反代。
- 新增或变更路由：
  - `/papers/` -> `paper-learning:8088`
  - `/remote/` -> `remote-control-web:5173`
  - `/remote/api/` and `/remote/devices/` -> `remote-control-api:8000`
  - `/@vite/` and `/src/` -> `remote-control-web:5173` for Vite dev assets requested by the `/remote/` page
  - `/sensing/` -> `remote-sensing:8090`
  - `/camera/` -> `camera-snapshot:8099`
  - `/web/` and `/llm/` -> `web-manager:8092`
  - `/robot/` -> `pi5-robot:8093`
  - `/modules/` -> `platform:8098`
- 数据目录或数据卷：无变化。
- 环境变量：无变化。

## 合入准则满足情况

- [x] README 已更新
- [x] 注册表已更新
- [x] Compose 已更新或无需更新
- [x] Caddy 已更新
- [x] 本地验证通过
- [x] 服务器验证未执行，本次仅推送代码
- [x] 不影响已有模块

## 验证结果

```text
python -m json.tool control_platform/modules/registry.json
OK

docker compose config --quiet
OK

python -m compileall control_platform remote_control_cloud
OK
```

## 已知问题

- 当前机器没有 `npm`，未执行 `remote_control_cloud` 前端构建；已把入口脚本改为相对路径，并让默认 API endpoint 支持 `/remote/` 网关路径。
- `pi_slam` 和 `future-systems` 是扩展入口，不是独立运行服务，映射到 `/modules/`。

## 下一步

- 服务器拉取后重启 Caddy 或整体 compose。
- 验证两个入口的 `/papers/`、`/remote/`、`/sensing/`、`/camera/`、`/web/`、`/llm/`、`/robot/`、`/modules/`。
