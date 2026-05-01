# Flow Audit

This is the latest end-to-end process review.

## Intended Flow

```text
1. Browser builds command JSON
2. Browser POSTs to HTTP API
3. API validates command
4. API publishes command to MQTT topic devices/{device_id}/cmd
5. PC Serial Bridge subscribes to that command topic
6. Bridge validates command and expected device_id
7. Bridge maps JSON command to Arduino serial command
8. Arduino responds over USB serial
9. Bridge publishes state to devices/{device_id}/state
10. Web/API displays or observes state
```

## Current Coverage

| Step | Status | File |
| --- | --- | --- |
| 1 | Implemented in frontend source. | `src/main.js` |
| 2 | Frontend POST passed in Chrome headless against the real local FastAPI endpoint. | `src/main.js` |
| 3 | Implemented in shared core. | `device_bridge/pc_serial_bridge/core.py` |
| 4 | Implemented in real FastAPI API. Offline unit tests still keep a separate mock API helper. | `cloud_api/app.py`, `cloud_api/mock_api.py` |
| 5 | Implemented in real bridge. | `device_bridge/pc_serial_bridge/bridge.py` |
| 6 | Implemented after audit. Bridge rejects mismatched `device_id`. | `device_bridge/pc_serial_bridge/core.py` |
| 7 | Implemented for `led_set/on`, `led_set/off`, and `status_get`. | `device_bridge/pc_serial_bridge/core.py` |
| 8 | Live Arduino test passed on `COM3` with `LED_ON`, `STATUS`, and `LED_OFF`. | `device_bridge/pc_serial_bridge/serial_client.py` |
| 9 | Implemented in real bridge and verified through Docker Mosquitto. | `device_bridge/pc_serial_bridge/bridge.py` |
| 10 | API acceptance appears in frontend; real device state is observable through `watch_state.py`. | `device_bridge/pc_serial_bridge/watch_state.py` |

## Gaps Found And Fixed

| Gap | Fix |
| --- | --- |
| No real HTTP API implementation. | Added `cloud_api/app.py`, `cloud_api/requirements.txt`, and `cloud_api/run_api.ps1`. |
| Bridge did not reject mismatched `device_id` payloads. | Added `expected_device_id` validation and smoke test coverage. |
| No easy way to observe real MQTT state messages. | Added `device_bridge/pc_serial_bridge/watch_state.py`. |
| Environment checker did not report FastAPI/uvicorn. | Added API dependency checks to `scripts/check_env.py`. |
| No Docker/Mosquitto in current environment. | Resolved by installing Docker Desktop and starting Docker Mosquitto. Added `scripts/run_real_docker_chain.ps1` as the preferred no-mock probe. |

## Remaining Gaps

| Gap | Impact | Next action |
| --- | --- | --- |
| System Node/npm missing. | Normal Vite workflow is not available from PATH, although install/build/preview/browser tests passed with an embedded Node runtime. | Install Node.js LTS or prepend the embedded Node runtime to `PATH`. |
| Frontend does not consume state topic. | Web UI can show API acceptance only, not actual device state. | Add API state endpoint or WebSocket/SSE/MQTT-over-WebSocket state channel. |
| MQTT broker is anonymous in local config. | Fine for local MVP, not safe for remote deployment. | Add username/password or TLS before public exposure. |
| API auth is not implemented. | Unsafe for public domain use. | Add token/session auth before deploying beyond local network. |

## Minimum No-Mock Acceptance

```text
Mosquitto running on 127.0.0.1:1883
PC Serial Bridge running
Arduino Uno connected on configured COM port
watch_state.py shows state after publish_test.py sends commands
Arduino LED physically changes
```

Current result:

```text
Passed with Docker Mosquitto on 127.0.0.1:1883.
Also passed with the earlier amqtt broker fallback, but Docker is now preferred.
```

## Full No-Mock Acceptance

```text
Node/npm installed
Frontend running with Vite
FastAPI running
Mosquitto running
PC Serial Bridge running
Arduino connected
Browser button click changes LED
State is observable via watch_state.py or future Web UI state channel
```

Current result:

```text
Passed locally with Chrome headless, Vite, FastAPI, Docker Mosquitto, PC Serial Bridge, and Arduino Uno on COM3.
```
