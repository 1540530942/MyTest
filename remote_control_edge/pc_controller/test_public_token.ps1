$ProgressPreference = 'SilentlyContinue'

Write-Host 'LOCAL /status without token'
try {
  Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/status' | ConvertTo-Json -Depth 3
} catch {
  Write-Host ('STATUSCODE=' + $_.Exception.Response.StatusCode.value__)
  Write-Host $_.ErrorDetails.Message
}

Write-Host 'LOCAL /status with query token'
try {
  Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/status?token=demo-public-token' | ConvertTo-Json -Depth 3
} catch {
  Write-Host ('STATUSCODE=' + $_.Exception.Response.StatusCode.value__)
  Write-Host $_.ErrorDetails.Message
}

Write-Host 'LOCAL /status with X-API-Token header'
try {
  $headers = @{ 'X-API-Token' = 'demo-public-token' }
  Invoke-RestMethod -Method Get -Headers $headers -Uri 'http://127.0.0.1:8000/status' | ConvertTo-Json -Depth 3
} catch {
  Write-Host ('STATUSCODE=' + $_.Exception.Response.StatusCode.value__)
  Write-Host $_.ErrorDetails.Message
}
