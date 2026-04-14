# Cloud API Mock

This folder contains the first API contract implementation point.

`mock_api.py` is intentionally dependency-free. It validates a device command payload and publishes it to an injected MQTT-like publisher. This lets the local smoke test verify the complete command path before a real FastAPI service and real MQTT broker are available.

`app.py` is the first real FastAPI command service. It accepts browser commands and publishes them to MQTT.

## Install

```powershell
python -m pip install -r cloud_api\requirements.txt
```

## Run

From the project root:

```powershell
.\cloud_api\run_api.ps1 -HostName 127.0.0.1 -Port 8000
```

Then set the Web UI API endpoint to:

```text
http://127.0.0.1:8000/devices/command
```

Planned real API behavior:

```text
POST /devices/command
  -> authenticate user
  -> validate command allowlist
  -> audit request
  -> publish to devices/{device_id}/cmd
  -> return accepted response
```
