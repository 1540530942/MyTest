$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host '[1/5] Checking Python virtual environment...'
if (-not (Test-Path '.venv\Scripts\Activate.ps1')) {
    Write-Host 'Creating virtual environment...'
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

Write-Host '[2/5] Installing/updating dependencies...'
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host '[3/5] Checking cloudflared.exe...'
if (-not (Test-Path '.\cloudflared.exe')) {
    Write-Host 'Downloading cloudflared.exe...'
    curl.exe -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
}

$env:ARDUINO_PORT = 'COM3'
$env:ARDUINO_BAUDRATE = '115200'
$env:ARDUINO_API_TOKEN = ''

Write-Host '[4/5] Starting local FastAPI server window...'
$serverCmd = "Set-Location '$PSScriptRoot'; . .\.venv\Scripts\Activate.ps1; `$env:ARDUINO_PORT='COM3'; `$env:ARDUINO_BAUDRATE='115200'; `$env:ARDUINO_API_TOKEN=''; uvicorn app:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-Command', $serverCmd

Start-Sleep -Seconds 3

Write-Host '[5/5] Starting Cloudflare tunnel window...'
$tunnelCmd = "Set-Location '$PSScriptRoot'; .\cloudflared.exe tunnel --url http://127.0.0.1:8000 --no-autoupdate"
Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-Command', $tunnelCmd

Write-Host ''
Write-Host 'Done.'
Write-Host '- Local page: http://127.0.0.1:8000'
Write-Host '- In the tunnel window, copy the https://*.trycloudflare.com URL'
Write-Host '- Open that URL on your phone to control the Arduino'
Write-Host ''
Write-Host 'If double-clicking .ps1 is blocked by Windows, run this once from PowerShell:'
Write-Host "powershell -ExecutionPolicy Bypass -File '$PSScriptRoot\start_public_remote_control.ps1'"
Read-Host 'Press Enter to exit'
