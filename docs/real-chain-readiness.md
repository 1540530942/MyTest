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
| Cloud API | Dependency-free API function | `cloud_api/mock_api.py` | Real FastAPI command service has not been implemented yet. |
| MQTT broker | In-memory message list | `tests/smoke_chain.py`, `tests/run_mock_chain.py` | No real Mosquitto/EMQX broker is running in this environment. |
| Arduino serial | Mock serial client | `tests/smoke_chain.py`, `tests/run_mock_chain.py` | No live Arduino serial port was tested in this run. |
| Browser runtime | Source-only frontend checks | `index.html`, `src/main.js` | Node.js/npm are not installed, so Vite cannot run here yet. |
| Device reboot | Disabled UI button | `index.html` | Reboot is not implemented or safe for the Arduino Uno bridge yet. |

## What Is Real Already

| Layer | Status | Evidence |
| --- | --- | --- |
| Python runtime | Real Python 3.13.12 is available. | `python --version` passed. |
| Bridge dependencies | Real `paho-mqtt==2.1.0` and `pyserial==3.5` installed. | `python scripts/check_env.py` reports both as OK. |
| Bridge core logic | Real command validation, serial mapping, and state formatting exist. | `device_bridge/pc_serial_bridge/core.py` |
| PC bridge runner | Real MQTT client + serial client runner exists. | `device_bridge/pc_serial_bridge/bridge.py` |
| MQTT config | Real Mosquitto config and Docker Compose template exist. | `infra/docker-compose.yml`, `infra/mosquitto/mosquitto.conf` |
| Environment check | Real readiness checker exists. | `scripts/check_env.py` |

## Environment Not Ready Yet

| Missing item | Current impact | Needed action |
| --- | --- | --- |
| Node.js/npm | Cannot run `npm install`, `npm run dev`, or `npm run build`. | Install Node.js LTS, then rerun `python scripts/check_env.py`. |
| Docker Desktop or Mosquitto | Cannot start a real local MQTT broker from this environment. | Install Docker Desktop, then run `cd scripts; .\start_mqtt_docker.ps1`. |
| Running MQTT broker on `127.0.0.1:1883` | Real bridge has nowhere to subscribe/publish. | Start Mosquitto/EMQX and confirm `scripts/check_env.py` reports `mqtt tcp` OK. |
| Arduino Uno connected on configured COM port | Real bridge cannot send `LED_ON`, `LED_OFF`, or `STATUS`. | Plug in Arduino Uno, confirm port, set `ARDUINO_PORT`, then run bridge. |
| Real HTTP API service | Browser cannot send commands into MQTT without using mock function. | Implement FastAPI service for `POST /devices/command`. |
| Frontend-to-API integration test | Browser request has not been tested against a real API. | Start real API + Vite, click LED buttons, confirm MQTT command appears. |

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

7. In another terminal, publish a real MQTT command:

```powershell
cd device_bridge\pc_serial_bridge
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd led_set --value on
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd status_get
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd led_set --value off
```

8. Confirm Arduino LED changes and bridge prints state publish logs.
9. Implement/start the real HTTP API service.
10. Start frontend:

```powershell
npm install
npm run dev
```

11. Set API endpoint in the browser and verify button clicks reach the real MQTT broker and Arduino.

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
