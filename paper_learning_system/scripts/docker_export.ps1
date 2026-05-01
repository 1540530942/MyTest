param(
  [string]$Image = $env:PAPER_LEARNING_IMAGE,
  [string]$OutputDir = "dist"
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

& docker image inspect $Image | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "image not found: $Image"
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$safeName = $Image -replace "[/:]", "_"
$archive = Join-Path $OutputDir "$safeName.tar"

& docker save -o $archive $Image
if ($LASTEXITCODE -ne 0) {
  throw "docker save failed with exit code $LASTEXITCODE"
}

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $archive

Write-Output "IMAGE_ARCHIVE=$archive"
Write-Output "SHA256=$($hash.Hash)"
