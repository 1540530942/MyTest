param(
  [string]$MqttHost = "127.0.0.1",
  [int]$MqttPort = 1883,
  [string]$DeviceId = "desk-led",
  [string]$ArduinoPort = "COM3"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$bridgeDir = Join-Path $root "device_bridge\pc_serial_bridge"
$logDir = Join-Path $root "runtime_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Get-ChildItem -LiteralPath $logDir -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force

$env:PYTHONUNBUFFERED = "1"
$env:MQTT_HOST = $MqttHost
$env:MQTT_PORT = "$MqttPort"
$env:DEVICE_ID = $DeviceId
$env:ARDUINO_PORT = $ArduinoPort
$env:ARDUINO_BAUDRATE = "115200"

$broker = $null
$watch = $null
$bridge = $null
$api = $null

try {
  python -m pip show amqtt | Out-Null
  if ($LASTEXITCODE -ne 0) {
    python -m pip install amqtt==0.11.3
  }

  $broker = Start-Process -FilePath "amqtt" -WorkingDirectory $root `
    -RedirectStandardOutput (Join-Path $logDir "broker.out.log") `
    -RedirectStandardError (Join-Path $logDir "broker.err.log") -PassThru

  Start-Sleep -Seconds 4
  $tcp = Test-NetConnection -ComputerName $MqttHost -Port $MqttPort
  if (-not $tcp.TcpTestSucceeded) {
    throw "MQTT broker is not reachable at ${MqttHost}:${MqttPort}"
  }

  $watch = Start-Process -FilePath "python" `
    -ArgumentList @("watch_state.py", "--host", $MqttHost, "--device-id", $DeviceId) `
    -WorkingDirectory $bridgeDir `
    -RedirectStandardOutput (Join-Path $logDir "watch.out.log") `
    -RedirectStandardError (Join-Path $logDir "watch.err.log") -PassThru

  $bridge = Start-Process -FilePath "python" -ArgumentList @("bridge.py") `
    -WorkingDirectory $bridgeDir `
    -RedirectStandardOutput (Join-Path $logDir "bridge.out.log") `
    -RedirectStandardError (Join-Path $logDir "bridge.err.log") -PassThru

  $api = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "cloud_api.app:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $root `
    -RedirectStandardOutput (Join-Path $logDir "api.out.log") `
    -RedirectStandardError (Join-Path $logDir "api.err.log") -PassThru

  Start-Sleep -Seconds 7

  $payloads = @(
    @{ request_id = "req-api-real-001"; cmd = "led_set"; device_id = $DeviceId; pin = 13; value = "on"; source = "api-real-test"; mqtt_topic = "devices/$DeviceId/cmd"; created_at = "2026-04-15T17:20:00Z" },
    @{ request_id = "req-api-real-002"; cmd = "status_get"; device_id = $DeviceId; pin = 13; source = "api-real-test"; mqtt_topic = "devices/$DeviceId/cmd"; created_at = "2026-04-15T17:20:01Z" },
    @{ request_id = "req-api-real-003"; cmd = "led_set"; device_id = $DeviceId; pin = 13; value = "off"; source = "api-real-test"; mqtt_topic = "devices/$DeviceId/cmd"; created_at = "2026-04-15T17:20:02Z" }
  )

  foreach ($payload in $payloads) {
    $json = $payload | ConvertTo-Json -Compress
    Write-Host "POST $json"
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/devices/command" -Method Post -Body $json -ContentType "application/json" | ConvertTo-Json -Compress
    Start-Sleep -Seconds 2
  }

  Start-Sleep -Seconds 4

  Write-Host "`n--- Bridge log ---"
  Get-Content (Join-Path $logDir "bridge.out.log")
  Write-Host "`n--- State watcher log ---"
  Get-Content (Join-Path $logDir "watch.out.log")
}
finally {
  if ($api) { Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue }
  if ($bridge) { Stop-Process -Id $bridge.Id -Force -ErrorAction SilentlyContinue }
  if ($watch) { Stop-Process -Id $watch.Id -Force -ErrorAction SilentlyContinue }
  if ($broker) { Stop-Process -Id $broker.Id -Force -ErrorAction SilentlyContinue }
}
