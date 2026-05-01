# www.wangyutang.cn Access Fix

Date: 2026-04-29

## Symptom

`www.wangyutang.cn` could not open in a browser.

Local checks showed:

- DNS resolves correctly: `www.wangyutang.cn A 110.40.154.41`
- HTTP reached Caddy but returned `308 Permanent Redirect` to HTTPS.
- HTTPS from outside timed out or failed during TLS connection.

## Root Cause

The running server Caddyfile did not include a site block for `www.wangyutang.cn`, so Caddy was not serving that hostname correctly at first.

After adding the hostname, Caddy successfully obtained a Let's Encrypt certificate for `www.wangyutang.cn`, but external port `443` still timed out. Server-side checks showed Docker was listening on `0.0.0.0:443` and the OS firewall was inactive, so the remaining likely blocker is the Tencent Cloud security group or upstream firewall for inbound TCP 443.

Caddy log evidence:

```text
certificate obtained successfully identifier=www.wangyutang.cn
Timeout during connect (likely firewall problem)
```

## Fix Applied

Local project config:

- Added `WWW_DOMAIN=www.wangyutang.cn` to `.env` and `.env.example`.
- Added a HTTPS Caddy site for `www.wangyutang.cn`.
- Added an explicit HTTP Caddy site for `http://www.wangyutang.cn` so HTTP can open the platform even while public 443 is blocked.

Server:

- Backed up `/root/control_platform/infra/caddy/Caddyfile`.
- Uploaded updated Caddyfile.
- Ran Caddy validation.
- Reloaded the running `control-platform-caddy` container.

## Verification

Current working URL:

```text
http://www.wangyutang.cn/
```

Verified from local machine:

```text
STATUS=200
<title>Control Platform</title>
```

HTTPS status:

```text
https://www.wangyutang.cn/
```

still times out externally on TCP 443, even though Caddy has obtained the certificate and the container listens on `0.0.0.0:443`.

## Remaining Action

Open inbound TCP `443` for `110.40.154.41` in the Tencent Cloud security group/firewall.

After that, verify:

```powershell
curl.exe -I https://www.wangyutang.cn/
```

Expected result: HTTP 200/405 from Caddy/Uvicorn instead of timeout.
