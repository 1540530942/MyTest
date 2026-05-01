# Personal Domain IoT Control Dashboard

This project is the web entry point for the `Arduino_interact` roadmap.

The current MVP uses the transition architecture:

```text
Web UI
  -> HTTPS API
  -> command validator
  -> MQTT publish devices/{device_id}/cmd
  -> PC Serial Bridge
  -> USB Serial
  -> Arduino Uno
  -> Pin 13 LED / GPIO action
  -> MQTT publish devices/{device_id}/state
  -> Web UI displays result
```

Later, the `PC Serial Bridge + Arduino Uno` segment can be replaced by a native WiFi device such as ESP32:

```text
MQTT Broker
  -> ESP32 / WiFi device
  -> GPIO / sensor / relay action
```

The current implementation is a static Vite dashboard. It sends structured JSON commands to a configurable API endpoint. The API layer is expected to validate the command and publish it to MQTT.

## Quick Start

Prepare the Python bridge dependencies:

```powershell
python -m pip install -r device_bridge\pc_serial_bridge\requirements.txt
python scripts\check_env.py
```

Optional local MQTT broker config is provided under `infra/`. After Docker Desktop is installed:

```powershell
cd scripts
.\start_mqtt_docker.ps1
```

If PowerShell blocks local scripts on Windows, run the same script with a one-time execution-policy bypass:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_mqtt_docker.ps1
```

If Docker Desktop is not installed yet, use the Python MQTT broker fallback only until Docker is available:

```powershell
cd scripts
.\start_mqtt_amqtt.ps1
```

Frontend dependencies require Node.js/npm:

```powershell
npm install
npm run dev
```

Open the local Vite URL, then set:

```text
API endpoint: http://127.0.0.1:8000/devices/command
Device ID: desk-led
GPIO pin: 13
```

For a real no-mock local acceptance probe with Docker Mosquitto, FastAPI, PC Serial Bridge, and Arduino on `COM3`, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_real_docker_chain.ps1 -ArduinoPort COM3
```

## Command Payload

Clicking `LED On` sends a payload like:

```json
{
  "request_id": "req-20260415000101-ab12cd34",
  "cmd": "led_set",
  "device_id": "desk-led",
  "pin": 13,
  "value": "on",
  "source": "web",
  "mqtt_topic": "devices/desk-led/cmd",
  "created_at": "2026-04-15T00:01:01.000Z"
}
```

## Roadmap Fit

This folder maps to the personal-domain and cloud-control part of the roadmap:

```text
M1: device command schema
M2: MQTT + PC Serial Bridge + Arduino Uno
M3: cloud server + personal domain + MQTT broker
M6: replace bridge with ESP32 / native WiFi device
```

The browser should not talk directly to the MQTT broker in the first MVP. Keep the browser simple, send commands to the API, and let the API handle auth, validation, audit logs, and MQTT publish.

## Future Cloud Server

The later cloud deployment target is:

```text
Cloud server + Docker
  -> Mosquitto container / EMQX container
  -> FastAPI container
  -> Web UI container / static site
  -> Caddy or Nginx reverse proxy
  -> personal domain HTTPS
```

The local Docker Mosquitto setup is intentionally aligned with this future server layout. See `docs/cloud-server-architecture.md` for the domain plan, service split, and migration path.

## Cloud API

The first real HTTP API lives in:

```text
cloud_api/app.py
```

Install and run it from the project root:

```powershell
python -m pip install -r cloud_api\requirements.txt
.\cloud_api\run_api.ps1 -HostName 127.0.0.1 -Port 8000
```

Then set the Web UI endpoint to:

```text
http://127.0.0.1:8000/devices/command
```

The API also subscribes to MQTT state messages and exposes the latest observed device state at:

```text
http://127.0.0.1:8000/devices/desk-led/state
```

The dashboard uses that endpoint after each command so the page can show the Arduino response, such as `OK LED_ON`, `STATUS OFF`, and `pin13 on/off`.

## Current Hardware Strategy

Use this as the near-term transition path:

```text
Cloud/API/MQTT
  -> PC Serial Bridge
  -> Arduino Uno over USB
  -> existing serial commands: LED_ON, LED_OFF, STATUS
```

This keeps the current Arduino Uno demo useful while the cloud and MQTT layers are being built. It also avoids forcing Arduino Uno to handle WiFi, TLS, MQTT, and JSON directly.

Use this as the later migration path:

```text
Cloud/API/MQTT
  -> ESP32 or another native WiFi microcontroller
  -> direct GPIO control and state publish
```

The command schema and MQTT topics should stay stable across both phases, so the Web UI and API do not need a major rewrite when hardware changes.

## PC Serial Bridge

The first bridge implementation lives in:

```text
device_bridge/pc_serial_bridge
```

It subscribes to `devices/{device_id}/cmd`, maps command JSON to the current Arduino serial commands, and publishes results to `devices/{device_id}/state`.

Start point:

```powershell
cd device_bridge\pc_serial_bridge
python -m pip install -r requirements.txt
.\run_bridge.ps1 -MqttHost 127.0.0.1 -MqttPort 1883 -DeviceId desk-led -ArduinoPort COM3
```

With Docker Desktop and Arduino available, use the real chain below rather than mocks.

## No-Mock Local Test

Preferred real local probe:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_real_docker_chain.ps1 -ArduinoPort COM3
```

This verifies:

```text
FastAPI POST /devices/command
  -> Docker Mosquitto on 127.0.0.1:1883
  -> PC Serial Bridge
  -> real USB serial COM3
  -> Arduino Uno
  -> MQTT state topic
```

## Offline Test Fallback

When the broker or Arduino is unavailable, the dependency-free tests can still check schema validation and command mapping:

```powershell
python -m unittest tests.smoke_chain
python tests\run_mock_chain.py
```

These tests intentionally do not prove hardware, broker, API server, or browser behavior.

Open issues and real-chain readiness are tracked in:

```text
docs/known-issues.md
docs/real-chain-readiness.md
docs/flow-audit.md
docs/cloud-server-architecture.md
```

## Real Local Chain Verified

The current Windows + Arduino transition chain has been verified with a real MQTT broker fallback, real FastAPI API, real PC Serial Bridge, and real Arduino Uno on `COM3`:

```text
FastAPI POST /devices/command
  -> MQTT devices/desk-led/cmd
  -> PC Serial Bridge
  -> COM3 Arduino Uno
  -> LED_ON / STATUS / LED_OFF
  -> MQTT devices/desk-led/state
```

You can rerun the preferred Docker local real-chain probe with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_real_docker_chain.ps1 -ArduinoPort COM3
```

After Docker Desktop was installed, the preferred local Docker broker path was also verified end-to-end:

```text
Web UI button click
  -> FastAPI POST /devices/command
  -> Docker Mosquitto on 127.0.0.1:1883
  -> PC Serial Bridge
  -> COM3 Arduino Uno
  -> LED_ON / STATUS / LED_OFF
  -> MQTT devices/desk-led/state
```

## Deploy

```powershell
npm run build
```

Deploy the generated `dist` directory to your static site host, reverse proxy, GitHub Pages, or personal-domain server.

## Git

Remote:

```text
https://github.com/1540530942/MyTest.git
```

Branch:

```text
feature/personal-domain-visual-control
```
