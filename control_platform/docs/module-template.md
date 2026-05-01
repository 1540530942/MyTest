# Module Template

Use this checklist when adding a new visual-control module.

## Required Fields

Add a record to `modules/registry.json`:

```json
{
  "id": "module-id",
  "name": "模块名称",
  "public_url": "https://module.wangyutang.com/",
  "local_url": "http://127.0.0.1:PORT/",
  "route_strategy": "subdomain-first",
  "path_prefix": "/module-route/",
  "service_url": "http://module-service:PORT",
  "health_url": "http://module-service:PORT/api/health",
  "image": "module-image:tag",
  "status": "scaffold | integration | ready",
  "summary": "模块一句话说明",
  "capabilities": ["capability-a", "capability-b"],
  "data_owner": "docker_volume_name"
}
```

## Required Endpoints

```text
GET /api/health
```

Recommended:

```text
GET /api/status
GET /api/version
GET /api/events
```

## Docker Rules

```text
One Dockerfile per module
One named image per module
One named data volume per stateful module
No module writes into another module's volume
No hardware device is exposed unless the module owns that adapter
```

## Routing Rules

All public paths must live under the module prefix:

```text
papers.wangyutang.com
remote.wangyutang.com
sensing.wangyutang.com
```

Subdomain-first routing is preferred. Path prefixes are allowed only when the module supports a base path.

APIs should stay inside the module boundary:

```text
https://remote.wangyutang.com/api/command
https://sensing.wangyutang.com/api/layers
```
