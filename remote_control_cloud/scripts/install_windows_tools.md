# Windows Tool Installation Notes

This environment currently has Python, but does not have Node.js/npm, Docker, or Mosquitto in `PATH`.

Install these manually when you are ready to run the real frontend and real MQTT broker.

## Required For Frontend

Install Node.js LTS from:

```text
https://nodejs.org/
```

After installing, open a new PowerShell window and check:

```powershell
node --version
npm --version
```

Then run:

```powershell
npm install
npm run dev
```

## Required For Local MQTT Broker

Recommended for this project: Docker Desktop.

After installing Docker Desktop, open a new PowerShell window and run:

```powershell
cd scripts
.\start_mqtt_docker.ps1
```

This starts Eclipse Mosquitto with:

```text
MQTT TCP: 127.0.0.1:1883
MQTT WebSocket: 127.0.0.1:9001
```

## Current Python Bridge Dependencies

Already reproducible with:

```powershell
python -m pip install -r device_bridge\pc_serial_bridge\requirements.txt
python scripts\check_env.py
```
