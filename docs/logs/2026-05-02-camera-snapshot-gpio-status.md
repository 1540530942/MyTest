# Camera Snapshot GPIO Status Log

Date: 2026-05-02

This log records the fixes and lessons from adding GPIO status reporting to the `camera_snapshot` module and deploying it behind `www.wangyutang.cn/camera/`.

## Goal

Add GPIO state reporting to the camera snapshot flow:

- Default queried pin: `GPIO26`, the TurboPi LED2 pin, because the stock `wifi.py` blink thread toggles LED2.
- Let the web UI dynamically choose a GPIO pin.
- When the user clicks single-frame capture, return the selected GPIO state with the frame metadata.

## Safety Decision

The implementation must be read-only.

Safe approach:

```bash
pinctrl get 16
```

Why this is safe:

- It reads pin controller state.
- It does not request a GPIO line through `gpiod`.
- It does not change direction.
- It does not write output level.
- It does not steal lines already held by `wifi.py` or `button_scan.py`.

Avoid this for occupied lines:

```python
chip = gpiod.Chip("gpiochip0")
line = chip.get_line(16)
line.get_value()
```

On the TurboPi, LED1 is already held by `/home/pi/hiwonder-toolbox/wifi.py`, so direct `gpiod` reads can fail with `Operation not permitted`.

## Confirmed TurboPi GPIO State

On the Raspberry Pi, relevant running services were:

```text
wifi.service         -> /home/pi/hiwonder-toolbox/wifi.py
button_scan.service  -> /home/pi/hiwonder-toolbox/button_scan.py
```

Confirmed active GPIO consumers:

```text
GPIO13 -> key1, monitored by button_scan.py
GPIO23 -> key2, monitored by button_scan.py
GPIO16 -> led1, controlled by wifi.py
GPIO26 -> led2, controlled by wifi.py
```

Important correction:

- Local notes may mention `gpiochip4`.
- On this Pi image, scripts use `gpiochip0`.
- For status reads, prefer `pinctrl get <gpio>` so the web feature does not depend on gpiochip numbering.

## Implemented Data Flow

Browser:

```text
POST /api/capture
body: { "mode": "single", "query_gpio": 16 }
```

Cloud server:

- Validates `query_gpio` as integer `0..53`.
- Defaults to `16`.
- Stores `query_gpio` in the task returned by `/api/control`.
- Accepts independent GPIO status updates at `POST /api/gpio`.
- Returns the latest independent GPIO status from `GET /api/gpio`.

Pi sender:

- Polls `/api/control`.
- Reads `task.query_gpio`.
- Runs:

```bash
pinctrl get <query_gpio>
```

- Uploads frame with GPIO headers:

```text
X-Gpio-Available
X-Gpio-Number
X-Gpio-Level
X-Gpio-Value
X-Gpio-Source
X-Gpio-Raw
```

- Also uploads GPIO state periodically, even when no frame is being captured:

```text
POST /api/gpio
```

This is required because GPIO state should reflect real high/low level even when no image has been uploaded.

Cloud `/api/latest` returns:

```json
"gpio": {
  "available": true,
  "gpio": 27,
  "level": "hi",
  "value": 1,
  "source": "pinctrl",
  "sampled_at": 1777675172.123,
  "raw": "27: ip pu | hi // GPIO27 = input"
}
```

Backward compatibility:

- For GPIO16, the sender also emits legacy `X-Led1-*` headers.
- The server still returns `led1` for older UI/code paths.

## Files Changed

```text
camera_snapshot/server.py
camera_snapshot/pi_camera_sender.py
camera_snapshot/static/index.html
camera_snapshot/static/app.js
camera_snapshot/README.md
control_platform/infra/caddy/Caddyfile
control_platform/modules/registry.json
```

## Web UI Changes

Added a `查询 GPIO` selector.

Default:

```text
GPIO26 LED2
```

Useful test options:

```text
GPIO16 LED1
GPIO26 LED2
GPIO13 KEY1
GPIO23 KEY2
GPIO4
GPIO5
GPIO6
GPIO12
GPIO17
GPIO22
GPIO24
GPIO25
GPIO27
```

The result field is now generic:

```text
引脚状态
采样时间
```

not only `LED1`.

If no frame has arrived yet, the UI should still show a meaningful placeholder such as:

```text
GPIO26 未采样
```

Do not clear the pin state to `-` just because `has_image=false`; that makes the GPIO result look broken.

## Path Routing Lesson

The module is served under:

```text
https://www.wangyutang.cn/camera/
```

The frontend must not call absolute paths like:

```javascript
fetch("/api/latest")
```

When mounted under `/camera/`, that calls:

```text
https://www.wangyutang.cn/api/latest
```

which is wrong.

Use relative paths:

```javascript
fetch("api/latest")
```

This works both for:

```text
https://www.wangyutang.cn/camera/
http://127.0.0.1:8099/
```

## Caddy Deployment Pitfall

The server Caddy environment did not define `WWW_DOMAIN`.

This caused:

```caddy
{$WWW_DOMAIN} {
  ...
}
```

to expand to an empty site block, and Caddy failed with:

```text
server block without any key is global configuration, and if used, it must be first
```

Fix:

Use explicit site labels for production routes:

```caddy
https://www.wangyutang.cn {
  ...
}
```

After editing Caddyfile, restart:

```bash
docker restart control-platform-caddy
```

Verify:

```bash
curl -k https://www.wangyutang.cn/camera/api/health
curl -k https://www.wangyutang.cn/camera/
```

## Docker Build Pitfall

The compose file uses a prebuilt image:

```text
camera-snapshot:local
```

There is no build context in the deployed compose file, so this is not enough:

```bash
docker compose -f infra/docker-compose.platform.yml build camera-snapshot
```

Build manually from the synced source:

```bash
docker build \
  --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.12-slim \
  -t camera-snapshot:local \
  /root/camera_snapshot
```

Then recreate only the camera container:

```bash
cd /root/control_platform
docker compose -f infra/docker-compose.platform.yml up -d --pull never --no-deps --force-recreate camera-snapshot
```

Why the build arg matters:

- Direct Docker Hub access timed out from the server.
- The mirror image `docker.m.daocloud.io/library/python:3.12-slim` worked.

## Deployment Steps Used

Copy module files:

```powershell
scp camera_snapshot\server.py camera_snapshot\pi_camera_sender.py camera_snapshot\README.md tencent:/root/camera_snapshot/
scp camera_snapshot\static\app.js camera_snapshot\static\index.html tencent:/root/camera_snapshot/static/
```

Build and restart:

```bash
docker build --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.12-slim -t camera-snapshot:local /root/camera_snapshot
cd /root/control_platform
docker compose -f infra/docker-compose.platform.yml up -d --pull never --no-deps --force-recreate camera-snapshot
```

Update Pi sender:

```text
Local file:
camera_snapshot/pi_camera_sender.py

Pi target:
/home/pi/pi_camera_sender.py
```

## Verification Steps

Local syntax:

```bash
python -m py_compile server.py pi_camera_sender.py
```

Local API behavior:

- `POST /api/capture` with no `query_gpio` returns `query_gpio: 26`.
- `POST /api/capture` with `query_gpio: 27` returns `query_gpio: 27`.
- Invalid `query_gpio`, such as `99`, returns HTTP 400.
- `POST /api/frame` with `X-Gpio-*` headers updates `/api/latest.gpio`.

Production checks:

```bash
curl -k https://www.wangyutang.cn/camera/api/latest
curl -k https://www.wangyutang.cn/camera/static/app.js
curl -k https://www.wangyutang.cn/camera/
```

Expected `/api/latest` shape:

```json
{
  "has_image": false,
  "gpio": {
    "available": false,
    "gpio": 26,
    "level": "",
    "value": null,
    "source": "",
    "raw": ""
  }
}
```

## Diagnostic Upload Cleanup

During verification, a 1x1 diagnostic JPEG was uploaded to test metadata.

Clean it after testing:

```bash
docker exec camera-snapshot rm -f /app/data/latest.jpg /app/data/latest.tmp
docker restart camera-snapshot
```

## Current Remaining Real-Device Blockers

The cloud module and dynamic GPIO metadata path work.

Real single-frame capture still needs these Pi-side conditions fixed:

1. The Pi currently has no default route:

```text
192.168.149.0/24 dev wlan0 src 192.168.149.1
```

No default route means the Pi cannot reach:

```text
www.wangyutang.cn
110.40.154.41
```

2. DNS on the Pi was empty:

```text
# Generated by NetworkManager
```

3. Camera was not available:

```text
rpicam-still --list-cameras
No cameras available!
```

The code path is ready, but real capture needs network egress and camera detection restored.

## Follow-Up: GPIO Must Not Depend On Camera Frames

Later requirement:

```text
GPIO 状态不需要“随帧上传”，要能反映真实高/低电平。
```

Important lesson:

- Do not tie GPIO reporting to `/api/frame`.
- GPIO status must have an independent channel, because the camera may be unavailable and there may be no image upload.

Implemented independent endpoints:

```text
GET  /api/gpio
POST /api/gpio
```

`POST /api/gpio` accepts JSON like:

```json
{
  "available": true,
  "gpio": 26,
  "level": "hi",
  "value": 1,
  "source": "pinctrl",
  "sampled_at": 1777681170.78,
  "device_id": "turbopi-01",
  "raw": "26: op dh pd | hi // GPIO26 = output"
}
```

The web UI polls both:

```text
GET /api/latest
GET /api/gpio
```

and displays the independent GPIO state even when:

```json
"has_image": false
```

## Follow-Up: Why The Page Still Did Not Move

Observed `/api/gpio` stayed at:

```json
{
  "available": false,
  "gpio": 26,
  "level": "",
  "sampled_at": 0.0
}
```

Root causes:

1. `pi_camera_sender.py` was not running.
2. The old sender initialized the camera before entering the loop.
3. The camera was unavailable, so the process exited before it could upload GPIO.
4. The Pi also had no default route, so it could not reach the public cloud directly.

Old failure log:

```text
[WARN] picamera2 unavailable: list index out of range
VIDEOIO(V4L2:/dev/video0): can't open camera by index
RuntimeError: could not open camera index 0
```

Fix:

- Make camera initialization lazy.
- Start the main loop first.
- Upload GPIO status every second even if no camera is available.
- Only call `build_camera()` when an actual capture task needs a frame.

Key pattern:

```python
camera: CameraBackend | None = None

while running:
    upload_gpio_status(...)
    if capture_task:
        if camera is None:
            camera = build_camera(args)
        jpeg = camera.capture_jpeg()
```

## Follow-Up: PC SSH Bridge Workaround

Because the Pi currently has no external route:

```text
ip route
192.168.149.0/24 dev wlan0 src 192.168.149.1
```

the Pi cannot post directly to:

```text
https://www.wangyutang.cn/camera/api/gpio
```

Temporary workaround:

- The Windows PC is connected to the Pi AP.
- The Windows PC also has internet through another interface.
- A local bridge script reads GPIO over SSH and posts it to the cloud.

Script:

```text
camera_snapshot/gpio_ssh_bridge.py
```

Run:

```powershell
python camera_snapshot\gpio_ssh_bridge.py --gpio 26 --interval 1
```

What it does:

```text
Windows -> SSH -> Pi -> pinctrl get 26
Windows -> HTTPS -> cloud -> POST /camera/api/gpio
```

Observed bridge log:

```text
[OK] GPIO26 lo 26: op dl pd | lo // GPIO26 = output
[OK] GPIO26 hi 26: op dh pd | hi // GPIO26 = output
[OK] GPIO26 lo 26: op dl pd | lo // GPIO26 = output
```

Cloud verification:

```bash
curl -k https://www.wangyutang.cn/camera/api/gpio
```

Expected shape:

```json
{
  "available": true,
  "gpio": 26,
  "level": "lo",
  "value": 0,
  "source": "pc-ssh-bridge",
  "device_id": "turbopi-01-via-pc"
}
```

## Follow-Up: Stale SSH Connections Can Break Diagnosis

If SSH suddenly appears unreachable, check for old stuck interactive SSH processes.

Symptom:

```text
Get-NetTCPConnection -RemoteAddress 192.168.149.1
State: Established
CommandLine: ssh.exe pi@192.168.149.1
```

This can be a leftover process waiting for password input from a non-interactive terminal.

Fix:

```powershell
Get-CimInstance Win32_Process -Filter "name = 'ssh.exe'" |
  Select-Object ProcessId,CommandLine

Stop-Process -Id <pid> -Force
```

After killing stale SSH, verify:

```powershell
ping 192.168.149.1
ssh -o ConnectTimeout=8 -o PreferredAuthentications=password -o PubkeyAuthentication=no -o NumberOfPasswordPrompts=0 pi@192.168.149.1
```

`Permission denied (publickey,password)` is acceptable for this test: it means TCP and SSH handshake worked, but interactive password input was disabled.

## Future Checklist

Before debugging the web UI, check:

```bash
curl -k https://www.wangyutang.cn/camera/api/health
curl -k https://www.wangyutang.cn/camera/api/latest
curl -k https://www.wangyutang.cn/camera/api/gpio
```

Before debugging Pi upload, check on Pi:

```bash
ip route
cat /etc/resolv.conf
python3 -c "import requests; print(requests.get('http://110.40.154.41/camera/api/health', timeout=5).text)"
rpicam-still --list-cameras
pinctrl get 26
```

If the Pi has no external route, use the PC bridge:

```powershell
python camera_snapshot\gpio_ssh_bridge.py --gpio 26 --interval 1
```

Before rebuilding camera-snapshot on server:

```bash
docker exec camera-snapshot grep -n "query_gpio" /app/server.py
```

If the grep does not find `query_gpio`, the running container is still old.
