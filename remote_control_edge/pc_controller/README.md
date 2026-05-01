# Arduino Remote LED PC Controller

PC-side control bridge for remotely controlling an Arduino Uno pin 13 LED.

The current flow is:

```text
Phone / Browser
  -> optional Cloudflare Tunnel public URL
  -> local FastAPI service on the PC
  -> USB serial
  -> Arduino Uno
  -> pin 13 LED
```

More architecture notes are in `docs/system-architecture.md`.

## What This Directory Contains

- `app.py`: FastAPI HTTP service. Serves the web UI and exposes LED/status APIs.
- `serial_client.py`: Thread-safe pyserial wrapper for talking to the Arduino over USB serial.
- `static/index.html`: Browser control page with token input and LED buttons.
- `run_server.ps1`: Local development/start script with configurable Arduino COM port, server port, and API token.
- `start_public_remote_control.ps1`: One-click public demo script. Starts the local server and a Cloudflare Tunnel in separate PowerShell windows.
- `start_public_remote_control.bat`: Windows double-click wrapper for `start_public_remote_control.ps1`.
- `test_api.ps1`: Simple local API smoke test for status, LED on, and LED off.
- `test_public_token.ps1`: Token behavior smoke test against local `127.0.0.1:8000`.
- `requirements.txt`: Python dependencies.
- `cloudflared.exe`: Cloudflare Tunnel binary used by the public demo script.

## Runtime Dependencies

- Windows PowerShell
- Python 3
- Arduino Uno connected over USB
- Arduino firmware that understands these line-based serial commands:
  - `LED_ON`
  - `LED_OFF`
  - `STATUS`
- Python packages from `requirements.txt`:
  - `fastapi`
  - `uvicorn[standard]`
  - `pyserial`

## Configuration

The service reads these environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ARDUINO_PORT` | `COM3` | USB serial port for the Arduino |
| `ARDUINO_BAUDRATE` | `115200` | Serial baud rate |
| `ARDUINO_API_TOKEN` | empty | Optional API token. When empty, API calls do not require auth |

When `ARDUINO_API_TOKEN` is set, protected endpoints accept the token in either:

- HTTP header: `X-API-Token: <token>`
- Query string: `?token=<token>`

The browser UI stores the token locally in `localStorage` after clicking **Save Token**.

## Start Locally

From this directory:

```powershell
.\run_server.ps1 -ArduinoPort COM3 -Port 8000 -ApiToken "change-me"
```

Then open:

```text
http://127.0.0.1:8000
```

For local-only quick testing without auth:

```powershell
.\run_server.ps1 -ArduinoPort COM3 -Port 8000
```

The script will create `.venv` if needed, install dependencies, set environment variables, and run:

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Start Public Phone Control

For a quick public demo, double-click:

```text
start_public_remote_control.bat
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_public_remote_control.ps1
```

This script:

1. Creates/activates `.venv`.
2. Installs Python dependencies.
3. Downloads `cloudflared.exe` if it is missing.
4. Starts the FastAPI service on `http://127.0.0.1:8000`.
5. Starts Cloudflare Tunnel for `http://127.0.0.1:8000`.

Copy the `https://*.trycloudflare.com` URL from the tunnel window and open it on the phone.

Important: `start_public_remote_control.ps1` currently sets `ARDUINO_API_TOKEN` to an empty string. That is useful for fast demos, but not safe for public sharing. Before stable public use, set a non-empty token in the script or start the server manually with `run_server.ps1 -ApiToken "..."`.

## HTTP API

### `GET /`

Serves `static/index.html`.

### `GET /health`

Returns service health and whether token protection is enabled.

Example response:

```json
{
  "ok": true,
  "serial_port": "COM3",
  "token_required": true
}
```

### `GET /status`

Sends `STATUS` to the Arduino.

Example response:

```json
{
  "ok": true,
  "command": "STATUS",
  "response": "STATUS ON",
  "serial_port": "COM3"
}
```

### `POST /led/on`

Sends `LED_ON` to the Arduino.

### `POST /led/off`

Sends `LED_OFF` to the Arduino.

All command endpoints return:

```json
{
  "ok": true,
  "command": "LED_ON",
  "response": "OK LED_ON",
  "serial_port": "COM3"
}
```

`ok` is true when the Arduino response starts with `OK` or `STATUS`.

## Smoke Tests

With the local server running:

```powershell
.\test_api.ps1 -BaseUrl "http://127.0.0.1:8000"
```

If token protection is enabled and the token is `demo-public-token`, test token behavior with:

```powershell
.\test_public_token.ps1
```

That script checks:

- no token
- query token
- `X-API-Token` header

## Troubleshooting

- If the server returns `Serial communication failed`, check that the Arduino is plugged in, the COM port is correct, and no other program is holding the serial port.
- If `/status` times out, confirm the Arduino firmware reads newline-terminated commands and writes a newline-terminated response.
- If phone access does not work, verify the local page works first at `http://127.0.0.1:8000`, then check the Cloudflare Tunnel window for the public URL.
- If Windows blocks script execution, run PowerShell with:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_public_remote_control.ps1
```

## Current Limitations

- The Cloudflare `trycloudflare.com` URL is temporary.
- Public demo script currently defaults to no API token.
- The PC must stay online with the Arduino connected over USB.
- The API is intentionally limited to LED pin 13 commands.
- This is a fast remote-control bridge, not yet a long-term deployment package.

