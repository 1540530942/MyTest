# Real Chain Readiness

This document separates the current mock path from the real no-mock path.

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

## What Is Mocked Now

| Layer | Mock used now | File | Why it exists |
| --- | --- | --- | --- |
| Cloud API mock | Dependency-free API function | `cloud_api/mock_api.py` | Keeps smoke tests working without FastAPI or MQTT broker. |
| MQTT broker in tests | In-memory message list | `tests/smoke_chain.py`, `tests/run_mock_chain.py` | Unit tests stay broker-free, even though a real local broker probe has now passed. |
| Arduino serial in tests | Mock serial client | `tests/smoke_chain.py`, `tests/run_mock_chain.py` | Unit tests stay hardware-free, even though live COM3 serial has now passed. |
| Browser runtime in tests | Source-only frontend checks | `index.html`, `src/main.js` | Frontend build has passed with a local Node runtime, but browser click testing is still pending. |
| Device reboot | Disabled UI button | `index.html` | Reboot is not implemented or safe for the Arduino Uno bridge yet. |

## What Is Real Already

| Layer | Status | Evidence |
| --- | --- | --- |
| Python runtime | Real Python 3.13.12 is available. | `python --version` passed. |
| Bridge dependencies | Real `paho-mqtt==2.1.0` and `pyserial==3.5` installed. | `python scripts/check_env.py` reports both as OK. |
| Bridge core logic | Real command validation, device ID guard, serial mapping, and state formatting exist. | `device_bridge/pc_serial_bridge/core.py` |
| PC bridge runner | Real MQTT client + serial client runner exists. | `device_bridge/pc_serial_bridge/bridge.py` |
| HTTP API implementation | Real FastAPI command publisher exists, but dependency install and live broker test are still pending. | `cloud_api/app.py` |
| Local real-chain probe | Real API to real MQTT broker fallback to real bridge to real Arduino COM3 has passed. | `runtime_logs/`, `scripts/run_real_local_chain.ps1` |
| MQTT config | Real Mosquitto config and Docker Compose template exist. | `infra/docker-compose.yml`, `infra/mosquitto/mosquitto.conf` |
| Environment check | Real readiness checker exists. | `scripts/check_env.py` |

## Environment Not Ready Yet

| Missing item | Current impact | Needed action |
| --- | --- | --- |
| System Node.js/npm | Not installed in PATH. A local embedded Node runtime was used to verify build. | Install Node.js LTS for normal development workflow. |
| Docker Desktop or Mosquitto | Not installed in PATH. | Install Docker Desktop for the preferred Mosquitto container path. |
| Running MQTT broker on `127.0.0.1:1883` | Not persistent after probes stop. | Start `scripts/start_mqtt_amqtt.ps1` or Docker Mosquitto before running bridge. |
| Arduino Uno connected on configured COM port | Passed on `COM3`. | Keep `ARDUINO_PORT=COM3` unless Windows changes the port. |
| Live API to broker test | Passed with amqtt fallback broker. | Repeat after Docker Mosquitto is installed. |
| Frontend-to-API integration test | Browser request has not been tested against a live API and MQTT broker. | Start real API + Vite, click LED buttons, confirm MQTT command appears. |

## Exact Steps To Run Without Mocks

1. Install Node.js LTS.
2. Install Docker Desktop or install Mosquitto directly.
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

## Current No-Mock Blockers

The smallest no-mock milestone is:

```text
Real Mosquitto broker
  -> real PC Serial Bridge
  -> real Arduino Uno over COM port
  -> real MQTT state publish
```

This does not require the browser or real HTTP API yet.

The full no-mock milestone additionally requires:

```text
Real Web UI
  -> real HTTP API
  -> real MQTT broker
  -> real PC Serial Bridge
  -> real Arduino Uno
```

## Mock Commands That Are Safe To Keep

These commands remain useful for development and CI:

```powershell
python -m unittest tests.smoke_chain
python tests\run_mock_chain.py
```

They do not prove hardware, network, broker, or browser behavior. They only prove that schema validation, topic naming, serial command mapping, and state formatting stay consistent.
