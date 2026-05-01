# Camera Snapshot Module

This module adds an on-demand TurboPi / Raspberry Pi camera visualization service.

## Public Route

```text
https://camera.wangyutang.cn/
```

DNS:

```text
camera.wangyutang.cn A -> 110.40.154.41
```

## Runtime Shape

```text
Browser
  -> camera.wangyutang.cn
  -> Caddy HTTPS
  -> camera-snapshot container :8099
  -> latest JPEG data volume

TurboPi / Raspberry Pi
  -> pi_camera_sender.py
  -> HTTPS polling /api/control
  -> HTTPS JPEG upload /api/frame
```

The cloud server does not need to connect back to the robot. The robot initiates outbound HTTPS requests, which works behind NAT, hotel Wi-Fi, and campus networks.

## Controls

The web page exposes two actions:

```text
Single frame
  Creates a one-shot task.
  The Raspberry Pi uploads exactly one JPEG frame.

Continuous send
  Creates a continuous task with a selected interval.
  The Raspberry Pi keeps uploading until the web page sends /api/stop.
```

## Source

```text
C:\Users\Administrator\Desktop\Workspace\Project_Codex\Harness\pi_TurboPi\camera_snapshot
```

## Image

Recommended image name:

```text
camera-snapshot:local
```

Build locally:

```powershell
cd C:\Users\Administrator\Desktop\Workspace\Project_Codex\Harness\pi_TurboPi\camera_snapshot
docker build -t camera-snapshot:local .
```

Save for cloud upload:

```powershell
docker save -o camera-snapshot_local.tar camera-snapshot:local
```

Load on Tencent Cloud:

```bash
docker load -i camera-snapshot_local.tar
```

## Server Data

The container stores the latest uploaded frame under:

```text
/app/data/latest.jpg
```

Use the named Docker volume:

```text
camera_snapshot_data
```

## Optional Upload Token

Create this file in the mounted data directory or image working directory if upload auth is required:

```text
.camera_token
```

Then start the Raspberry Pi sender with:

```bash
python3 pi_camera_sender.py --server https://camera.wangyutang.cn --token <same-token>
```

## Health

```text
GET /api/health
```

Expected:

```json
{"status":"ok","has_image":false}
```
