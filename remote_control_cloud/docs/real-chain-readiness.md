# Real Chain Readiness

This document records the current real no-mock path and the offline-only test fallback.

## Target Real Chain

```text
Browser Web UI
  -> real HTTP API
  -> real MQTT broker
  -> real PC Serial Bridge
  -> real USB serial port
  -> real Arduino Uno firmware
  -> real MQTT state message
  -> Web/API displays real device state
```

## Offline-Only Test Fallback

| Layer | Offline substitute | File | Why it exists |
| --- | --- | --- | --- |
| Cloud API | Dependency-free API function | `cloud_api/mock_api.py` | Keeps offline unit tests working without starting FastAPI or MQTT. |
| MQTT broker | In-memory message list | `tests/smoke_chain.py`, `tests/run_mock_chain.py` | Unit tests can check schema/topic behavior without a broker. |
| Arduino serial | In-process serial substitute | `tests/smoke_chain.py`, `tests/run_mock_chain.py` | Unit tests can check command mapping without hardware. |
| Browser runtime | Source-only frontend checks | `index.html`, `src/main.js` | Real browser click testing has passed locally; CI/browser automation is not formalized. |
| Device reboot | Disabled UI button | `index.html` | Reboot is not implemented or safe for the Arduino Uno bridge yet. |

## What Is Real Already

| Layer | Status | Evidence |
| --- | --- | --- |
| Python runtime | Real Python 3.13.12 is available. | `python --version` passed. |
| Bridge dependencies | Real `paho-mqtt==2.1.0` and `pyserial==3.5` installed. | `python scripts/check_env.py` reports both as OK. |
| Bridge core logic | Real command validation, device ID guard, serial mapping, and state formatting exist. | `device_bridge/pc_serial_bridge/core.py` |
| PC bridge runner | Real MQTT client + serial client runner exists. | `device_bridge/pc_serial_bridge/bridge.py` |
| HTTP API implementation | Real FastAPI command publisher exists and has passed Docker broker tests. | `cloud_api/app.py` |
| Docker no-mock probe | Real API to Docker Mosquitto to real bridge to real Arduino COM3 has passed. | `runtime_logs/`, `scripts/run_real_docker_chain.ps1` |
| Earlier local real-chain probe | Real API to amqtt broker fallback to real bridge to real Arduino COM3 has passed. | `runtime_logs/`, `scripts/run_real_local_chain.ps1` |
| Docker MQTT broker | Real Docker Mosquitto broker is running on `127.0.0.1:1883` and has passed the API -> MQTT -> bridge -> Arduino chain. | `infra/docker-compose.yml`, `infra/mosquitto/mosquitto.conf`, `runtime_logs/docker_*` |
| MQTT config | Real Mosquitto config and Docker Compose template exist. | `infra/docker-compose.yml`, `infra/mosquitto/mosquitto.conf` |
| Environment check | Real readiness checker exists. | `scripts/check_env.py` |
| Frontend browser path | Real Vite page was opened in Chrome headless and clicked through the API, Docker Mosquitto, bridge, and Arduino. | `runtime_logs/ui2_*` |

## Environment Notes

| Missing item | Current impact | Needed action |
| --- | --- | --- |
| System Node.js/npm | Not installed in PATH. A local embedded Node runtime was used to verify `npm install`, build, dev server, production preview, and browser click testing. | Install Node.js LTS for normal development workflow, or prepend the embedded Node runtime to `PATH` before frontend commands. |
| Docker Desktop or Mosquitto CLI | Docker Desktop is installed and working. The standalone `mosquitto` CLI is not installed, but it is not required for the Docker path. | Keep Docker Desktop running for the preferred Mosquitto container path. |
| Running MQTT broker on `127.0.0.1:1883` | Docker Mosquitto is currently the preferred persistent local broker. | Start `scripts/start_mqtt_docker.ps1` before running bridge/API work if the container is stopped. |
| Arduino Uno connected on configured COM port | Passed on `COM3`. | Keep `ARDUINO_PORT=COM3` unless Windows changes the port. |
| Live API to broker test | Passed with both the amqtt fallback broker and Docker Mosquitto. | Keep using Docker Mosquitto for the normal local path. |
| Frontend-to-API integration test | Passed against real FastAPI, Docker Mosquitto, PC Serial Bridge, and Arduino Uno on `COM3`. | Repeat after UI/API changes or after changing the Arduino port. |

## Exact Steps To Run Without Mocks

Preferred one-command Docker probe:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_real_docker_chain.ps1 -ArduinoPort COM3
```

Manual workflow:

1. Install Node.js LTS, or prepend the known local embedded Node runtime to `PATH`.
2. Install Docker Desktop or install Mosquitto directly. Docker Desktop is verified in this environment.
3. Start MQTT broker:

```powershell
cd scripts
.\start_mqtt_docker.ps1
```

4. Confirm environment:

```powershell
cd ..
python scripts\check_env.py
```

Required real checks:

```text
[OK] paho-mqtt
[OK] pyserial
[OK] mqtt tcp: 127.0.0.1:1883
[OK] node
[OK] npm
```

5. Plug in Arduino Uno and confirm the serial port, for example `COM3`.
6. Start the real PC Serial Bridge:

```powershell
cd device_bridge\pc_serial_bridge
.\run_bridge.ps1 -MqttHost 127.0.0.1 -MqttPort 1883 -DeviceId desk-led -ArduinoPort COM3
```

7. In another terminal, watch state:

```powershell
cd device_bridge\pc_serial_bridge
python .\watch_state.py --host 127.0.0.1 --device-id desk-led
```

8. In another terminal, publish a real MQTT command:

```powershell
cd device_bridge\pc_serial_bridge
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd led_set --value on
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd status_get
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd led_set --value off
```

9. Confirm Arduino LED changes and `watch_state.py` prints real state messages.
10. Install and start the real HTTP API service:

```powershell
python -m pip install -r cloud_api\requirements.txt
.\cloud_api\run_api.ps1 -HostName 127.0.0.1 -Port 8000
```

11. Start frontend:

```powershell
npm install
npm run dev
```

12. Set API endpoint in the browser and verify button clicks reach the real MQTT broker and Arduino.

## Current No-Mock Status

The smallest no-mock milestone has passed:

```text
Real Mosquitto broker
  -> real PC Serial Bridge
  -> real Arduino Uno over COM port
  -> real MQTT state publish
```

This does not require the browser or real HTTP API, but those have also passed.

The full no-mock milestone has now passed locally:

```text
Real Web UI
  -> real HTTP API
  -> real MQTT broker
  -> real PC Serial Bridge
  -> real Arduino Uno
```

## Offline Commands That Are Safe To Keep

These commands remain useful for development and CI when hardware or Docker is unavailable:

```powershell
python -m unittest tests.smoke_chain
python tests\run_mock_chain.py
```

They do not prove hardware, network, broker, API server, or browser behavior. They only prove that schema validation, topic naming, serial command mapping, and state formatting stay consistent.
