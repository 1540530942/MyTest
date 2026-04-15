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

After Docker Desktop is installed:

```powershell
.\start_mqtt_docker.ps1
```

## MQTT Broker Without Docker

For local real-chain testing before Docker Desktop is installed:

```powershell
.\start_mqtt_amqtt.ps1
```

This starts a real MQTT broker on `127.0.0.1:1883` using Python `amqtt`.

## One-Command Real Local Probe

With Arduino on `COM3`:

```powershell
.\run_real_local_chain.ps1 -ArduinoPort COM3
```

This starts a temporary broker, state watcher, PC Serial Bridge, FastAPI, sends `on/status/off`, prints the state logs, and stops the temporary processes.

See `install_windows_tools.md` for Node.js and Docker installation notes.
