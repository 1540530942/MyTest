# Remote Control Module Plan

This module wraps the existing `remote_server` project as a cloud module.

## Current Local System

```text
Web UI
  -> FastAPI command API
  -> MQTT
  -> PC Serial Bridge
  -> Arduino Uno over COM3
  -> MQTT state feedback
```

## Cloud Module Split

```text
remote-control-web
  -> static web dashboard

remote-control-api
  -> auth, validation, audit, MQTT publish

remote-control-mqtt
  -> Mosquitto or EMQX broker

remote-control-bridge
  -> edge-only bridge for serial devices
```

## Important Hardware Boundary

The cloud server cannot access a Windows PC USB serial port or Arduino COM3 directly.

Cloud production path:

```text
Cloud MQTT/API
  -> edge gateway or ESP32
  -> device action
  -> state publish back to cloud
```

Transition path:

```text
Cloud MQTT/API
  -> local PC bridge connected outward to MQTT
  -> Arduino Uno
```

## Platform Route

```text
control.wangyutang.com/remote/
```

