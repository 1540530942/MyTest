param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8000
)

python -m uvicorn cloud_api.app:app --host $HostName --port $Port
