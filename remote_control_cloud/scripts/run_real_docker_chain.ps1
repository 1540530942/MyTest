param(
  [string]$MqttHost = "127.0.0.1",
  [int]$MqttPort = 1883,
  [string]$DeviceId = "desk-led",
  [string]$ArduinoPort = "COM3",
  [int]$ApiPort = 8000
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$bridgeDir = Join-Path $root "device_bridge\pc_serial_bridge"
$logDir = Join-Path $root "runtime_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$env:PYTHONUNBUFFERED = "1"
$env:MQTT_HOST = $MqttHost
$env:MQTT_PORT = "$MqttPort"
$env:DEVICE_ID = $DeviceId
$env:ARDUINO_PORT = $ArduinoPort
$env:ARDUINO_BAUDRATE = "115200"

$watch = $null
$bridge = $null
$api = $null

function Wait-TcpPort {
  param(
    [string]$HostName,
    [int]$Port,
    [int]$Seconds = 20
  )

  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    try {
      $client = [Net.Sockets.TcpClient]::new()
      $task = $client.ConnectAsync($HostName, $Port)
      if ($task.Wait(1000) -and $client.Connected) {
        $client.Close()
        return $true
      }
      $client.Close()
    } catch {
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $deadline)

  return $false
}

function Wait-Http {
  param(
    [string]$Url,
    [int]$Seconds = 20
  )

  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
        return $true
      }
    } catch {
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $deadline)

  return $false
}

try {
  docker compose -f (Join-Path $root "infra\docker-compose.yml") up -d

  if (-not (Wait-TcpPort -HostName $MqttHost -Port $MqttPort -Seconds 30)) {
    throw "Docker MQTT broker is not reachable at ${MqttHost}:${MqttPort}"
  }

  $watch = Start-Process -FilePath "python" `
    -ArgumentList @("watch_state.py", "--host", $MqttHost, "--device-id", $DeviceId) `
    -WorkingDirectory $bridgeDir `
    -RedirectStandardOutput (Join-Path $logDir "docker_real_watch_$stamp.out.log") `
    -RedirectStandardError (Join-Path $logDir "docker_real_watch_$stamp.err.log") -PassThru

  $bridge = Start-Process -FilePath "python" -ArgumentList @("bridge.py") `
    -WorkingDirectory $bridgeDir `
    -RedirectStandardOutput (Join-Path $logDir "docker_real_bridge_$stamp.out.log") `
    -RedirectStandardError (Join-Path $logDir "docker_real_bridge_$stamp.err.log") -PassThru

  $api = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "cloud_api.app:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $root `
    -RedirectStandardOutput (Join-Path $logDir "docker_real_api_$stamp.out.log") `
    -RedirectStandardError (Join-Path $logDir "docker_real_api_$stamp.err.log") -PassThru

  if (-not (Wait-Http -Url "http://127.0.0.1:$ApiPort/health" -Seconds 30)) {
    throw "FastAPI is not reachable at http://127.0.0.1:$ApiPort/health"
  }

  Start-Sleep -Seconds 4

  $payloads = @(
    @{ request_id = "req-docker-real-$stamp-001"; cmd = "led_set"; device_id = $DeviceId; pin = 13; value = "on"; source = "docker-real-probe"; mqtt_topic = "devices/$DeviceId/cmd"; created_at = (Get-Date).ToUniversalTime().ToString("s") + "Z" },
    @{ request_id = "req-docker-real-$stamp-002"; cmd = "status_get"; device_id = $DeviceId; pin = 13; source = "docker-real-probe"; mqtt_topic = "devices/$DeviceId/cmd"; created_at = (Get-Date).ToUniversalTime().ToString("s") + "Z" },
    @{ request_id = "req-docker-real-$stamp-003"; cmd = "led_set"; device_id = $DeviceId; pin = 13; value = "off"; source = "docker-real-probe"; mqtt_topic = "devices/$DeviceId/cmd"; created_at = (Get-Date).ToUniversalTime().ToString("s") + "Z" }
  )

  foreach ($payload in $payloads) {
    $json = $payload | ConvertTo-Json -Compress
    Write-Host "POST $json"
    Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/devices/command" -Method Post -Body $json -ContentType "application/json" | ConvertTo-Json -Compress
    Start-Sleep -Seconds 2
  }

  Start-Sleep -Seconds 4

  Write-Host "`n--- Bridge log ---"
  Get-Content (Join-Path $logDir "docker_real_bridge_$stamp.out.log")
  Write-Host "`n--- State watcher log ---"
  Get-Content (Join-Path $logDir "docker_real_watch_$stamp.out.log")
}
finally {
  if ($api) { Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue }
  if ($bridge) { Stop-Process -Id $bridge.Id -Force -ErrorAction SilentlyContinue }
  if ($watch) { Stop-Process -Id $watch.Id -Force -ErrorAction SilentlyContinue }
}
