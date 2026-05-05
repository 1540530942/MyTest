$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Port = if ($env:PI5_ROBOT_PORT) { $env:PI5_ROBOT_PORT } else { "8093" }
python -m uvicorn services.webui.app:app --host 0.0.0.0 --port $Port
