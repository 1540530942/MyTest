param(
  [string]$Image = $env:PAPER_LEARNING_IMAGE
)

$ErrorActionPreference = "Stop"

function Get-DotEnvValue {
  param([string]$Key)
  if (-not (Test-Path -LiteralPath ".env")) {
    return ""
  }
  foreach ($line in Get-Content -LiteralPath ".env") {
    if ($line -match "^\s*$([regex]::Escape($Key))=(.*)$") {
      return $Matches[1].Trim()
    }
  }
  return ""
}

if (-not $Image) {
  $Image = Get-DotEnvValue "PAPER_LEARNING_IMAGE"
}

if (-not $Image) {
  $Image = "paper-learning-system:local"
}

$env:PAPER_LEARNING_IMAGE = $Image
& docker compose up -d --no-build
if ($LASTEXITCODE -ne 0) {
  throw "docker compose up failed with exit code $LASTEXITCODE"
}

& docker compose ps
