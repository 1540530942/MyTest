# PC Serial Bridge Plan

This is the near-term transition plan before switching to native WiFi hardware.

## Goal

Keep the existing Arduino Uno useful while moving the upper architecture to MQTT:

```text
Web UI
  -> API
  -> MQTT Broker
  -> PC Serial Bridge
  -> Arduino Uno USB Serial
  -> Pin 13 LED
```

## Why This First

Arduino Uno is good at simple GPIO and serial control, but it is not a comfortable place to run WiFi, TLS, MQTT, and JSON parsing.

The bridge lets us build and test the cloud, MQTT, command schema, and Web UI first. Later, ESP32 can replace the bridge without changing the Web UI contract.

## Minimal Bridge Behavior

1. Connect to MQTT Broker.
2. Subscribe to `devices/desk-led/cmd`.
3. Open the Arduino Uno serial port.
4. Convert command JSON to the current serial commands.
5. Read Arduino response.
6. Publish state to `devices/desk-led/state`.
7. Publish errors to `devices/desk-led/errors`.

## Example Input

MQTT topic:

```text
devices/desk-led/cmd
```

Payload:

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

Serial command sent to Arduino:

```text
LED_ON
```

## Example Output

MQTT topic:

```text
devices/desk-led/state
```

Payload:

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

## Later ESP32 Migration

When ESP32 or another native WiFi device is ready, it should subscribe to the same command topic and publish the same state topic.

The replacement should look like this:

```text
Web UI/API/MQTT stays the same
PC Serial Bridge + Arduino Uno is replaced by ESP32 MQTT firmware
```
