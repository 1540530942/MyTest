# Known Issues And Mocks

This file records anything that blocks the real chain and the mock used to keep the architecture moving.

For a full layer-by-layer real-vs-mock breakdown, see `docs/real-chain-readiness.md`.

## 2026-04-15

| Area | Issue | Current handling | Next step |
| --- | --- | --- | --- |
| Frontend build | System `node` and `npm` are not in PATH. | Build passed using an existing local embedded Node runtime; `package-lock.json` is now generated. | Install Node.js LTS for normal development workflow. |
| MQTT dependency | Resolved in this environment by installing `paho-mqtt==2.1.0` and `pyserial==3.5`. | Dependency-free core logic and `tests/smoke_chain.py` remain available for offline validation. | Keep `device_bridge/pc_serial_bridge/requirements.txt` as the reproducible install source. |
| API dependency | Resolved in this environment by installing FastAPI and uvicorn from `cloud_api/requirements.txt`. | Real API was tested against a real local MQTT broker fallback and Arduino bridge. | Repeat after Docker Mosquitto is installed. |
| MQTT broker | Docker/Mosquitto is still not installed, but `amqtt` real broker fallback is installed and verified. | `scripts/run_real_local_chain.ps1` starts a temporary real MQTT broker on `127.0.0.1:1883`. | Install Docker Desktop for the preferred Mosquitto container path. |
| Arduino serial | Live Arduino Uno on `COM3` was exercised successfully. | Real chain returned `OK LED_ON`, `STATUS ON`, and `OK LED_OFF`. | Keep using `COM3` unless Windows changes the port. |
| Reboot command | `device_reboot` is not safe or implemented for Arduino Uno bridge. | UI button is disabled and API docs mark it as future work. | Add whitelist, confirmation policy, and firmware support before enabling. |
| GitHub push | GitHub access from this execution environment failed on port 443. | Local commits are preserved; continue local development. | Push manually when network is available: `git push origin feature/personal-domain-visual-control`. |
| Windows package manager | `winget`, `choco`, and `scoop` were not found in PATH. | Did not attempt system-level installs from scripts. | Install Node.js and Docker Desktop manually, then rerun `scripts/check_env.py`. |

## 2026-04-16 Verified Real Chain

The following no-mock data path has passed:

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
