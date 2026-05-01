# MQTT Serial Bridge

This bridge is the transition layer for the current Arduino Uno demo.

It subscribes to MQTT commands, maps them to the existing USB serial protocol, sends them to Arduino Uno, then publishes state back to MQTT.

## Chain

```text
Web UI / API
  -> MQTT Broker
  -> devices/desk-led/cmd
  -> mqtt_serial_bridge
  -> USB Serial
  -> Arduino Uno
  -> devices/desk-led/state
```

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

Start a local MQTT broker first, then run:

```powershell
.\run_bridge.ps1 -MqttHost 127.0.0.1 -MqttPort 1883 -DeviceId desk-led -ArduinoPort COM3
```

Environment variables are also supported:

| Variable | Default | Meaning |
| --- | --- | --- |
| `MQTT_HOST` | `127.0.0.1` | MQTT broker host |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | empty | Optional MQTT username |
| `MQTT_PASSWORD` | empty | Optional MQTT password |
| `DEVICE_ID` | `desk-led` | Device ID used in topics |
| `ARDUINO_PORT` | `COM3` | Arduino USB serial port |
| `ARDUINO_BAUDRATE` | `115200` | Arduino serial baud rate |

## Publish Test Command

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
