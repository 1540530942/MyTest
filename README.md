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

```powershell
npm install
npm run dev
```

Open the local Vite URL, then set:

```text
API endpoint: https://api.your-domain.com/devices/command
Device ID: desk-led
GPIO pin: 13
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

## Local Smoke Test

When a real MQTT broker or Arduino is not available, run the dependency-free mock chain:

```powershell
python -m unittest tests.smoke_chain
```

To print a readable mock run:

```powershell
python tests\run_mock_chain.py
```

This verifies:

```text
mock Web/API command
  -> API validation
  -> in-memory MQTT command topic
  -> PC bridge core mapping
  -> mock serial LED response
  -> in-memory MQTT state topic
```

Open issues and mocks are tracked in `docs/known-issues.md`.

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
