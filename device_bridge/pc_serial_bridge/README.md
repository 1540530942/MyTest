# PC Serial Bridge

This bridge keeps the current Arduino Uno demo useful while the cloud API and MQTT layers are being built.

## Chain

```text
Web UI / API
  -> MQTT Broker
  -> devices/desk-led/cmd
  -> PC Serial Bridge
  -> USB Serial
  -> Arduino Uno
  -> devices/desk-led/state
```

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
.\run_bridge.ps1 -MqttHost 127.0.0.1 -MqttPort 1883 -DeviceId desk-led -ArduinoPort COM3
```

## Publish Test Command

In one terminal, watch returned state:

```powershell
python .\watch_state.py --host 127.0.0.1 --device-id desk-led
```

In another terminal, publish commands:

```powershell
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd led_set --value on
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd led_set --value off
python .\publish_test.py --host 127.0.0.1 --device-id desk-led --cmd status_get
```

## Command Mapping

| MQTT command | Serial command |
| --- | --- |
| `{ "cmd": "led_set", "value": "on" }` | `LED_ON` |
| `{ "cmd": "led_set", "value": "off" }` | `LED_OFF` |
| `{ "cmd": "status_get" }` | `STATUS` |

## Topics

| Topic | Purpose |
| --- | --- |
| `devices/{device_id}/cmd` | Commands consumed by the bridge |
| `devices/{device_id}/state` | State published after serial response |
| `devices/{device_id}/errors` | Bridge or serial errors |
| `devices/{device_id}/heartbeat` | Retained bridge online/offline heartbeat |
