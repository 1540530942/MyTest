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

See `install_windows_tools.md` for Node.js and Docker installation notes.
