# Cloud API

This folder contains the real HTTP command API for the local no-mock chain.

`app.py` is the FastAPI command service. It accepts browser commands, validates them, and publishes them to MQTT topic `devices/{device_id}/cmd`.

`mock_api.py` is kept only for offline unit tests when FastAPI, MQTT, or Arduino hardware are unavailable. Do not use it for normal local verification.

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

The API subscribes to MQTT state, error, and heartbeat topics in the background. Read the latest observed state with:

```text
http://127.0.0.1:8000/devices/desk-led/state
```

Current real API behavior:

```text
POST /devices/command
  -> validate command allowlist
  -> publish to devices/{device_id}/cmd
  -> return accepted response

MQTT devices/{device_id}/state
  -> cache latest bridge/Arduino state

GET /devices/{device_id}/state
  -> return latest state, error, and heartbeat seen by the API
```

Before exposing this API outside local development, add authentication, request audit logging, and MQTT credentials/TLS.
