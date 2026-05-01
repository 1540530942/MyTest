# Known Issues And Real-Chain Notes

This file records anything that blocks or qualifies the real local chain.

For the layer-by-layer no-mock status and the offline-only test fallback, see `docs/real-chain-readiness.md`.

## 2026-04-15

| Area | Issue | Current handling | Next step |
| --- | --- | --- | --- |
| Frontend build | System `node` and `npm` are not in PATH. | Build, install audit, dev server, production preview, and browser-to-API smoke test passed using an existing local embedded Node runtime. | Install Node.js LTS for normal everyday shell workflow, or prepend the embedded Node runtime to `PATH` before frontend commands. |
| MQTT dependency | Resolved in this environment by installing `paho-mqtt==2.1.0` and `pyserial==3.5`. | Dependency-free core logic and `tests/smoke_chain.py` remain available for offline validation. | Keep `device_bridge/pc_serial_bridge/requirements.txt` as the reproducible install source. |
| API dependency | Resolved in this environment by installing FastAPI and uvicorn from `cloud_api/requirements.txt`. | Real API was tested against Docker Mosquitto and Arduino bridge. | Repeat the Docker no-mock probe after API changes. |
| MQTT broker | Docker Desktop is installed and Docker Mosquitto is running on `127.0.0.1:1883`. The standalone `mosquitto` CLI is still not installed, but it is not required for the Docker path. | `scripts/start_mqtt_docker.ps1` starts the preferred broker container. `amqtt` remains available as a fallback. | Keep Docker Desktop running before starting the bridge/API chain. |
| Arduino serial | Live Arduino Uno on `COM3` was exercised successfully. | Real chain returned `OK LED_ON`, `STATUS ON`, and `OK LED_OFF`. | Keep using `COM3` unless Windows changes the port. |
| Reboot command | `device_reboot` is not safe or implemented for Arduino Uno bridge. | UI button is disabled and API docs mark it as future work. | Add whitelist, confirmation policy, and firmware support before enabling. |
| GitHub push | GitHub access from this execution environment failed on port 443. | Local commits are preserved; continue local development. | Push manually when network is available: `git push origin feature/personal-domain-visual-control`. |
| Windows package manager | `winget`, `choco`, and `scoop` were not found in PATH. | Did not attempt system-level installs from scripts. | Install Node.js and Docker Desktop manually, then rerun `scripts/check_env.py`. |

## 2026-04-16 Verified Earlier Real Chain

The following no-mock data path passed before Docker Desktop was available:

```text
FastAPI POST /devices/command
  -> real local amqtt broker on 127.0.0.1:1883
  -> PC Serial Bridge
  -> Arduino Uno on COM3
  -> MQTT state publish
```

Verified commands:

```text
led_set on  -> serial LED_ON  -> OK LED_ON  -> state pin13 on
status_get  -> serial STATUS  -> STATUS ON  -> state pin13 on
led_set off -> serial LED_OFF -> OK LED_OFF -> state pin13 off
```

## 2026-04-16 Verified Browser UI Chain

The browser-facing path has passed with Vite, Chrome headless, the real FastAPI service, Docker Mosquitto, the PC Serial Bridge, and Arduino Uno on `COM3`:

```text
Web UI button click
  -> POST http://127.0.0.1:8000/devices/command
  -> Docker Mosquitto on 127.0.0.1:1883
  -> PC Serial Bridge
  -> Arduino Uno on COM3
  -> MQTT state publish
```

Verified browser actions:

```text
LED On      -> API accepted -> serial LED_ON  -> state pin13 on
Read Status -> API accepted -> serial STATUS  -> state pin13 on
LED Off     -> API accepted -> serial LED_OFF -> state pin13 off
```

## 2026-04-16 Verified Docker Broker Chain

After installing Docker Desktop, the preferred Docker broker path has also passed:

```text
FastAPI POST /devices/command
  -> Docker Mosquitto on 127.0.0.1:1883
  -> PC Serial Bridge
  -> Arduino Uno on COM3
  -> MQTT state publish
```

Verified commands:

```text
led_set on  -> serial LED_ON  -> OK LED_ON  -> state pin13 on
status_get  -> serial STATUS  -> STATUS ON  -> state pin13 on
led_set off -> serial LED_OFF -> OK LED_OFF -> state pin13 off
```
