# Cloud API Mock

This folder contains the first API contract implementation point.

`mock_api.py` is intentionally dependency-free. It validates a device command payload and publishes it to an injected MQTT-like publisher. This lets the local smoke test verify the complete command path before a real FastAPI service and real MQTT broker are available.

Planned real API behavior:

```text
POST /devices/command
  -> authenticate user
  -> validate command allowlist
  -> audit request
  -> publish to devices/{device_id}/cmd
  -> return accepted response
```
