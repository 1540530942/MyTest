# Personal Domain IoT Control Dashboard

This project is the web entry point for the `Arduino_interact` roadmap.

The intended long-term chain is:

```text
Web UI
  -> HTTPS API
  -> command validator
  -> MQTT publish devices/{device_id}/cmd
  -> PC serial bridge or ESP32
  -> Arduino / GPIO action
  -> MQTT publish devices/{device_id}/state
  -> Web UI displays result
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
M2: MQTT + PC serial bridge integration
M3: cloud server + personal domain + MQTT broker
```

The browser should not talk directly to the MQTT broker in the first MVP. Keep the browser simple, send commands to the API, and let the API handle auth, validation, audit logs, and MQTT publish.

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
