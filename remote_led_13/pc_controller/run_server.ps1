param(
    [string]$ArduinoPort = "COM3",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

$env:ARDUINO_PORT = $ArduinoPort
$env:ARDUINO_BAUDRATE = "115200"

Write-Host "Starting FastAPI server on http://127.0.0.1:$Port with Arduino port $ArduinoPort"
uvicorn app:app --reload --host 127.0.0.1 --port $Port
