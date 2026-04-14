# API Contract

The web dashboard sends commands to the cloud API. The API validates and audits the request, then publishes a clean command to MQTT.

## Request

```http
POST /devices/command
Content-Type: application/json
Authorization: Bearer <token>
```

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

## Validation Rules

The backend should enforce these rules before publishing to MQTT:

| Field | Rule |
| --- | --- |
| `request_id` | Required, unique per command |
| `cmd` | Must be in the command allowlist |
| `device_id` | Must belong to the authenticated user |
| `pin` | Must be an allowed pin for the device |
| `value` | Must match the command schema |
| `source` | Must be one of `web`, `agent`, `worker`, or `test` |

## Command Allowlist

| Command | MQTT topic | Payload meaning |
| --- | --- | --- |
| `led_set` | `devices/{device_id}/cmd` | Set an LED pin to `on` or `off` |
| `status_get` | `devices/{device_id}/cmd` | Ask the device bridge to report state |

Future commands such as `device_reboot` must stay disabled until the bridge and hardware firmware implement a safe confirmation policy.

## MQTT State Payload

The bridge or ESP32 should publish state to:

```text
devices/{device_id}/state
```

Example:

```json
{
  "request_id": "req-20260415000101-ab12cd34",
  "device_id": "desk-led",
  "ok": true,
  "state": {
    "pin13": "on"
  },
  "updated_at": "2026-04-15T00:01:02.000Z"
}
```
