param(
  [string]$BaseUrl = "http://127.0.0.1:8088"
)

$ErrorActionPreference = "Stop"

$health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -Method Get
$papers = Invoke-RestMethod -Uri "$BaseUrl/api/papers" -Method Get

Write-Host "health.ok=$($health.ok)"
Write-Host "papers.count=$($papers.papers.Count)"
