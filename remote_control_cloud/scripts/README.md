# Local Setup Scripts

## Python Bridge Setup

From this `scripts` directory:

```powershell
.\setup_python_bridge.ps1
```

Or from the project root:

```powershell
python -m pip install -r device_bridge\pc_serial_bridge\requirements.txt
python scripts\check_env.py
```

## Environment

Copy `.env.example` to `.env` when you want local defaults:

```powershell
Copy-Item .env.example .env
```

The current bridge reads environment variables directly. PowerShell launch example:

```powershell
$env:MQTT_HOST="127.0.0.1"
$env:MQTT_PORT="1883"
$env:DEVICE_ID="desk-led"
$env:ARDUINO_PORT="COM3"
.\device_bridge\pc_serial_bridge\run_bridge.ps1
```

## MQTT Broker With Docker

This is the preferred local path. It uses the same Mosquitto container shape as the later cloud server.

```powershell
.\start_mqtt_docker.ps1
```

If PowerShell blocks local scripts, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_mqtt_docker.ps1
```

## One-Command Docker No-Mock Probe

With Docker Desktop running and Arduino on `COM3`:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_real_docker_chain.ps1 -ArduinoPort COM3
```

This uses the real Docker Mosquitto broker, real FastAPI service, real PC Serial Bridge, and real Arduino serial port. It sends `on/status/off`, prints state logs, and stops only the temporary watcher/API/bridge processes.

## MQTT Broker Without Docker

Use this only when Docker Desktop is unavailable. It is still a real MQTT broker, but it is not the preferred path:

```powershell
.\start_mqtt_amqtt.ps1
```

This starts a real MQTT broker on `127.0.0.1:1883` using Python `amqtt`.

## One-Command Real Local Probe

This older probe starts a temporary Python MQTT broker. Prefer `run_real_docker_chain.ps1` when Docker Desktop is available.

```powershell
.\run_real_local_chain.ps1 -ArduinoPort COM3
```

This starts a temporary broker, state watcher, PC Serial Bridge, FastAPI, sends `on/status/off`, prints the state logs, and stops the temporary processes.

See `install_windows_tools.md` for Node.js and Docker installation notes.
