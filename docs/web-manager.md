# Web Manager 模块记录

代码路径：`wangyutang_platform/llm_manager`

## 作用

`web-manager` 是平台里的模块网页监督台。它独立运行在 `web-manager:8092`，用于监督各模块网页和服务的执行状态，展示连接状态、当前开发进展、下一步计划，并继续提供大模型兼容接口管理和共享对话接口。

## 路由

```text
本地服务：http://127.0.0.1:8092/
公网路径：http://www.wangyutang.cn/web/
兼容路径：http://www.wangyutang.cn/llm/
健康检查：http://127.0.0.1:8092/api/health
模块状态：http://127.0.0.1:8092/api/modules
共享调用：http://127.0.0.1:8092/api/chat
```

## 数据

Provider 配置保存到模块数据卷：

```text
/app/data/providers.json
```

模块清单读取自：

```text
control_platform/modules/registry.json
```

容器内通过只读挂载暴露为：

```text
/app/control_platform/modules/registry.json
```

## API Key 策略

Provider 可以保存两种 Key 来源：

- `api_key`：直接保存到模块数据卷。
- `api_key_env`：只保存环境变量名，运行时从容器环境读取真实 Key。

推荐生产环境使用 `api_key_env`。
