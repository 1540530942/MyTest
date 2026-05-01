# Cloud Deployment Checklist

This checklist records what is still needed after a personal domain and Tencent Cloud server are available.

The local no-mock path is already working:

```text
Web UI
  -> FastAPI
  -> Docker Mosquitto
  -> PC Serial Bridge
  -> COM3 Arduino Uno
  -> MQTT state
  -> Web UI device state
```

The remaining work is the cloud, security, DNS, and compliance layer.

## Information Needed From The Server And Domain Owner

Provide these before cloud setup starts:

```text
Domain name
Tencent Cloud CVM public IP
Server region: Mainland China, Hong Kong, or overseas
Operating system and version
SSH username
SSH key or temporary password
sudo permission status
DNS provider access, such as Tencent Cloud DNSPod
Security group edit permission
ICP filing status, if using a Mainland China server
Preferred subdomains
Whether the local Windows PC will stay online as the PC Serial Bridge
```

Recommended subdomains:

```text
iot.example.com   Web dashboard
api.example.com   FastAPI HTTPS API
mqtt.example.com  MQTT TLS or MQTT over WebSocket
```

## Compliance And Domain Requirements

For Tencent Cloud CVM in Mainland China:

```text
ICP filing must be completed before the website/API is opened to public access.
Public Security Network Filing should be completed within 30 days after the website is opened.
ICP and public security filing numbers should be displayed in the site footer after approval.
```

For Tencent Cloud Hong Kong or overseas regions:

```text
Mainland ICP filing is usually not part of the same launch path.
Latency, availability, and regulatory boundaries should still be considered.
```

Official references:

```text
Tencent Cloud ICP filing overview:
https://cloud.tencent.com/document/product/243/41513

Tencent Cloud filing cloud resource requirements:
https://cloud.tencent.com/document/product/243/18908

Tencent Cloud public security filing:
https://cloud.tencent.com/document/product/243/19142

Tencent Cloud filing number display:
https://cloud.tencent.com/document/product/243/61412
```

## DNS Requirements

Create DNS records after the server IP is known:

```text
iot.example.com   A record -> CVM public IP
api.example.com   A record -> CVM public IP
mqtt.example.com  A record -> CVM public IP
```

If Caddy is used, it can request certificates automatically after DNS points to the server and ports `80` and `443` are reachable.

## Security Group Requirements

Do not expose the local development ports directly.

Recommended initial inbound rules:

```text
22/tcp    Only the maintainer's current public IP
80/tcp    0.0.0.0/0, for HTTP redirect and certificate challenges
443/tcp   0.0.0.0/0, for HTTPS
8883/tcp  Optional MQTT TLS, preferably restricted to trusted source IPs
1883/tcp  Do not open to the public internet
9001/tcp  Do not open directly; use HTTPS/WSS reverse proxy if needed
8000/tcp  Do not open directly; expose only through reverse proxy
5173/tcp  Do not open in production
```

Official references:

```text
Tencent Cloud security group overview:
https://cloud.tencent.com/document/product/213/112610

Tencent Cloud add security group rules:
https://cloud.tencent.com/document/product/213/112614
```

## Cloud Docker Files Still Needed

The current local compose file only runs Mosquitto. Cloud deployment still needs:

```text
infra/docker-compose.cloud.yml
infra/caddy/Caddyfile
infra/api/Dockerfile
infra/web/Dockerfile
infra/mosquitto/mosquitto.cloud.conf
infra/mosquitto/acl
infra/.env.cloud.example
scripts/deploy_cloud.ps1 or scripts/deploy_cloud.sh
scripts/backup_cloud.sh
```

Target cloud compose services:

```text
caddy      HTTPS, routing, WebSocket forwarding, security headers
web        Static Vite build
api        FastAPI command and state API
mqtt       Mosquitto with authentication, ACL, persistence, and TLS/WSS path
```

## MQTT Security Requirements

The current local Mosquitto config is intentionally local-only:

```text
allow_anonymous true
```

Before public exposure, cloud Mosquitto must use:

```text
allow_anonymous false
password_file /mosquitto/config/passwords
acl_file /mosquitto/config/acl
persistence true
```

Minimum ACL shape:

```text
Bridge user can read:
devices/desk-led/cmd

Bridge user can write:
devices/desk-led/state
devices/desk-led/errors
devices/desk-led/heartbeat

API user can write:
devices/desk-led/cmd

API user can read:
devices/desk-led/state
devices/desk-led/errors
devices/desk-led/heartbeat
```

Prefer one of these network exposure models:

```text
Option A: mqtts://mqtt.example.com:8883 with TLS and credentials
Option B: wss://mqtt.example.com/mqtt through Caddy/Nginx
Option C: keep MQTT private and only expose HTTPS API
```

Do not expose unauthenticated `1883/tcp` on the public internet.

## PC Serial Bridge Cloud Requirements

The current PC Serial Bridge works locally and supports MQTT username/password environment variables.

Before it connects to cloud MQTT, add TLS support:

```text
MQTT_TLS=true
MQTT_CA_CERT=...
MQTT_HOST=mqtt.example.com
MQTT_PORT=8883
MQTT_USERNAME=bridge-desk-led
MQTT_PASSWORD=...
DEVICE_ID=desk-led
ARDUINO_PORT=COM3
```

Bridge code still needs:

```text
mqtt_client.tls_set(...)
TLS env parsing
clear startup error when cloud MQTT auth/TLS fails
reconnect behavior verification against cloud MQTT
```

## API Security Requirements

The API currently validates command shape and restricts allowed `device_id`, but it does not have real user authentication.

Before public exposure, add:

```text
Authorization: Bearer <token>
API_TOKEN or JWT validation
CORS allowlist for https://iot.example.com
rate limiting
request audit log
structured error log
dangerous command confirmation policy
```

The API should never be exposed directly on port `8000`; expose it only behind HTTPS reverse proxy.

## Web UI Cloud Requirements

The local UI auto-fills:

```text
http://127.0.0.1:8000/devices/command
```

For cloud deployment, choose one of these:

```text
Same-origin route:
https://iot.example.com/api/devices/command

Separate API subdomain:
https://api.example.com/devices/command
```

The build should get the default API endpoint from configuration instead of hard-coded local assumptions.

Needed changes:

```text
Vite env var for default API endpoint
Production CORS config
Footer support for ICP/Public Security filing numbers
Clear offline/error state when API, MQTT, bridge, or Arduino is unavailable
```

## Reverse Proxy Requirements

Use Caddy first unless Nginx is specifically needed.

Caddy should handle:

```text
Automatic HTTPS certificates
HTTP -> HTTPS redirect
iot.example.com static Web UI
api.example.com reverse proxy to FastAPI
Optional mqtt.example.com WSS reverse proxy
Security headers
Compression
Access logs
```

Official SSL reference:

```text
Tencent Cloud SSL Certificates:
https://www.tencentcloud.com/product/ssl
```

## Operations Requirements

Before launch, add:

```text
docker compose restart policy
health checks
log rotation
Mosquitto data volume backup
API/Web deployment notes
rollback command
server update procedure
credential rotation procedure
```

Useful checks:

```text
docker compose ps
docker compose logs -f api
docker compose logs -f mqtt
curl https://api.example.com/health
curl https://api.example.com/devices/desk-led/state
```

## Acceptance Criteria

Cloud MVP is acceptable when all items pass:

```text
https://iot.example.com opens the dashboard over HTTPS
https://api.example.com/health returns OK
API rejects requests without a valid token
Mosquitto rejects anonymous clients
Local Windows PC Serial Bridge connects to cloud MQTT with TLS/auth
Browser command reaches cloud API
Cloud API publishes to cloud MQTT
PC Serial Bridge receives the command from cloud MQTT
Arduino LED changes on COM3
Bridge publishes state back to cloud MQTT
API state endpoint returns the latest Arduino state
Web UI shows the real Arduino response and pin13 state
No public access to raw 1883, 8000, or 5173 ports
```

## Recommended Work Order

1. Confirm server region and filing status.
2. Point DNS records to the CVM public IP.
3. Configure security group with only `22`, `80`, and `443` at first.
4. Add cloud Docker files.
5. Add API token auth and production CORS.
6. Add Mosquitto users, passwords, and ACL.
7. Add MQTT TLS support to the PC Serial Bridge.
8. Deploy Caddy, Web UI, FastAPI, and Mosquitto.
9. Connect the local PC Serial Bridge to cloud MQTT.
10. Run the full no-mock cloud acceptance test.
