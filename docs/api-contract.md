# API Contract

前端默认发送 `POST` 请求到页面中配置的远端服务地址。

## Request

```http
POST /device
Content-Type: application/json
```

```json
{
  "command": "led:on",
  "source": "personal-domain-dashboard",
  "timestamp": "2026-04-15T00:00:00.000Z"
}
```

## Commands

| Command | Description |
| --- | --- |
| `led:on` | 打开 LED |
| `led:off` | 关闭 LED |
| `device:status` | 读取设备状态 |
| `device:reboot` | 请求设备重启 |

## Response

建议远端服务返回 `2xx` 状态码，并在响应正文中返回简短状态文本或 JSON。
