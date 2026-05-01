# Deployment Target

## Domain

```text
Registrar: Spaceship
Root domain: wangyutang.com
Recommended app domain: papers.wangyutang.com
DNS record: papers A 110.40.154.41
```

## Tencent Cloud Instance

```text
Instance ID: lhins-cfcgqi2u
Instance name: OpenCloudOS-j1XW
Region: ap-shanghai
Public IP: 110.40.154.41
Operating system: OpenCloudOS 9
Default SSH username: root
CPU / memory: 4 cores / 4 GB
System disk: 40 GB SSD
Bandwidth: 3 Mbps
Monthly traffic package: 300 GB
Creation state: successful
```

## Tencent Cloud Links

```text
Lighthouse console:
https://console.cloud.tencent.com/lighthouse/instance/index?rid=1

OrcaTerm web terminal:
https://orcaterm.cloud.tencent.com/terminal?type=lighthouse&instanceId=lhins-cfcgqi2u&region=ap-shanghai&from=lh_console_login_btn
```

## Pending Before Deployment

```text
SSH password received for this session, not stored in project files
sudo permission confirmation
Security group rules for 22, 80, 443
Spaceship DNS A record confirmation: papers.wangyutang.com should resolve to 110.40.154.41
ICP filing decision if this is a Mainland China CVM
Production API_TOKEN
Optional OpenAI-compatible API key
```
