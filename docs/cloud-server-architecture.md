# Cloud Server Architecture

This is the target architecture after a cloud server and personal domain are available.

## Target Stack

```text
Cloud server + Docker
  -> Mosquitto container / EMQX container
  -> FastAPI container
  -> Web UI container / static site
  -> Caddy or Nginx reverse proxy
  -> personal domain HTTPS
```

## Service Responsibilities

| Service | Responsibility | First choice |
| --- | --- | --- |
| Reverse proxy | HTTPS, domain routing, WebSocket forwarding, security headers | Caddy first, Nginx later if needed |
| Web UI | Device dashboard and future personal pages | Static Vite build |
| FastAPI | Auth, command validation, audit logs, MQTT publish, state API | Existing `cloud_api/app.py`, later containerized |
| MQTT broker | Device command, state, heartbeat, errors | Mosquitto for MVP, EMQX if device/user scale grows |
| PC Serial Bridge | Transitional local bridge from MQTT to Arduino Uno USB serial | Runs on Windows PC first, not on cloud server |
| ESP32 firmware | Later replacement for PC Serial Bridge | Connects directly to cloud MQTT |

## Domain Plan

Use subdomains to keep public pages, APIs, and device control separated:

```text
www.example.com        personal homepage
papers.example.com     papers and notes
iot.example.com        authenticated device dashboard
api.example.com        FastAPI HTTPS API
mqtt.example.com       MQTT TLS / MQTT over WebSocket
```

For the first cloud MVP, these can be simplified:

```text
iot.example.com        Web UI
api.example.com        FastAPI
mqtt.example.com       MQTT broker
```

## Local To Cloud Migration

Current local MVP:

```text
Windows browser
  -> Windows FastAPI: 127.0.0.1:8000
  -> Docker Mosquitto: 127.0.0.1:1883
  -> Windows PC Serial Bridge
  -> Arduino Uno COM port
```

Cloud MVP:

```text
Browser
  -> https://iot.example.com
  -> https://api.example.com
  -> mqtts://mqtt.example.com or wss://mqtt.example.com
  -> local Windows PC Serial Bridge
  -> Arduino Uno COM port
```

Later native WiFi device path:

```text
Browser
  -> https://iot.example.com
  -> https://api.example.com
  -> mqtts://mqtt.example.com
  -> ESP32 / native WiFi device
  -> GPIO / sensors / relays
```

## Why Docker Helps

Docker keeps local and cloud deployment close:

```text
Local Docker Compose
  -> Mosquitto

Cloud Docker Compose
  -> reverse proxy
  -> Web UI
  -> FastAPI
  -> Mosquitto / EMQX
```

The cloud deployment should extend the local `infra/docker-compose.yml` rather than replace it.

## Mosquitto vs EMQX

| Broker | Best for | Notes |
| --- | --- | --- |
| Mosquitto | MVP, simple device command/state topics, low resource usage | Good first broker |
| EMQX | More devices, dashboard, rule engine, richer auth and observability | Good later upgrade |

Start with Mosquitto. Move to EMQX only when broker management, observability, or larger-scale device access becomes important.

## Security Requirements Before Public Exposure

Do not expose the current local config directly to the internet.

Before using a real domain, add:

```text
API authentication
MQTT username/password or stronger auth
MQTT ACL per device/user
TLS/HTTPS
rate limiting
audit logs
safe command allowlist
dangerous-action confirmation
separate public pages from device control
```

## First Cloud Deliverable

The first practical cloud deliverable should be:

```text
Cloud Docker Compose
  -> Caddy
  -> FastAPI
  -> Mosquitto
  -> static Web UI

Local Windows PC
  -> PC Serial Bridge connects to mqtt.example.com
  -> Arduino Uno over COM port
```

Acceptance criteria:

```text
https://iot.example.com opens the dashboard
https://api.example.com/health returns OK
mqtt.example.com accepts authenticated bridge connection
browser command reaches MQTT broker
PC Serial Bridge receives command from cloud MQTT
Arduino LED changes
state is published back to cloud MQTT
```

## Files To Evolve Next

```text
infra/docker-compose.yml
infra/mosquitto/mosquitto.conf
cloud_api/app.py
src/main.js
docs/real-chain-readiness.md
```

Later cloud-specific files may be added:

```text
infra/caddy/Caddyfile
infra/api/Dockerfile
infra/web/Dockerfile
infra/.env.example
```
