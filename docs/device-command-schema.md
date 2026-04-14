# Device Command Schema

This file captures the first command abstraction step from the `Arduino_interact` roadmap.

The current device path is intentionally transitional:

```text
MQTT command
  -> PC Serial Bridge
  -> USB Serial
  -> Arduino Uno
  -> LED / GPIO
```

The later device path should keep the same MQTT schema:

```text
MQTT command
  -> ESP32 / native WiFi device
  -> LED / GPIO / sensor / relay
```

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

## Bridge Responsibilities

The PC Serial Bridge should:

| Responsibility | Detail |
| --- | --- |
| Subscribe command topic | Listen to `devices/{device_id}/cmd` |
| Validate minimal payload | Reject unknown `cmd`, invalid `pin`, or unsupported `value` |
| Map to serial command | Convert `led_set/on` to `LED_ON`, `led_set/off` to `LED_OFF`, `status_get` to `STATUS` |
| Read Arduino response | Capture serial output from Arduino Uno |
| Publish state | Publish result to `devices/{device_id}/state` |
| Publish errors | Publish failures to `devices/{device_id}/errors` |
| Reconnect safely | Recover from MQTT or serial disconnects when possible |

## Migration Rule

Do not let the Web UI depend on whether the device is currently Arduino Uno behind a PC bridge or a future ESP32.

Stable contract:

```text
Web UI/API publishes command-shaped JSON.
Device side publishes state-shaped JSON.
Hardware-specific details stay behind the MQTT topic boundary.
```
