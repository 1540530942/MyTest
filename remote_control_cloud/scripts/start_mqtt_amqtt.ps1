python -m pip show amqtt | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing amqtt local broker dependency..."
  python -m pip install amqtt==0.11.3
}

Write-Host "Starting local amqtt broker on 127.0.0.1:1883..."
amqtt
