# Device Command Schema

This file captures the first command abstraction step from the `Arduino_interact` roadmap.

## Topics

```text
devices/{device_id}/cmd
devices/{device_id}/state
devices/{device_id}/telemetry
devices/{device_id}/heartbeat
devices/{device_id}/events
devices/{device_id}/errors
```

## Command

```json
{
  "request_id": "req-20260415000101-ab12cd34",
  "cmd": "led_set",
  "device_id": "desk-led",
  "pin": 13,
  "value": "on",
  "source": "web",
  "created_at": "2026-04-15T00:01:01.000Z"
}
```

## State

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

## Serial Mapping For Arduino Uno Demo

The PC bridge can map structured commands back to the existing serial protocol:

| JSON command | Serial command |
| --- | --- |
| `{ "cmd": "led_set", "value": "on" }` | `LED_ON` |
| `{ "cmd": "led_set", "value": "off" }` | `LED_OFF` |
| `{ "cmd": "status_get" }` | `STATUS` |

This lets the upper layers move to MQTT without replacing the current Arduino Uno firmware first.
