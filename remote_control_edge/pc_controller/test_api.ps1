param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

Write-Host "GET $BaseUrl/status"
Invoke-RestMethod -Method Get -Uri "$BaseUrl/status"

Write-Host "POST $BaseUrl/led/on"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/led/on"

Start-Sleep -Seconds 1

Write-Host "POST $BaseUrl/led/off"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/led/off"
