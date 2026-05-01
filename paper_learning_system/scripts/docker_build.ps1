param(
  [string]$Image = $env:PAPER_LEARNING_IMAGE,
  [string]$PythonImage = $env:PYTHON_IMAGE,
  [string]$PipIndexUrl = $env:PIP_INDEX_URL
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

if (-not $PythonImage) {
  $PythonImage = Get-DotEnvValue "PYTHON_IMAGE"
}

if (-not $PipIndexUrl) {
  $PipIndexUrl = Get-DotEnvValue "PIP_INDEX_URL"
}

if (-not $Image) {
  $Image = "paper-learning-system:local"
}

if (-not $PythonImage) {
  $PythonImage = "python:3.12-slim"
}

$argsList = @(
  "build",
  "--build-arg", "PYTHON_IMAGE=$PythonImage",
  "--build-arg", "PIP_INDEX_URL=$PipIndexUrl",
  "-t", $Image,
  "."
)

Write-Output "Building image: $Image"
Write-Output "Base image: $PythonImage"
if ($PipIndexUrl) {
  Write-Output "Pip index: $PipIndexUrl"
}

& docker @argsList
if ($LASTEXITCODE -ne 0) {
  throw "docker build failed with exit code $LASTEXITCODE"
}

& docker image inspect $Image --format "IMAGE_OK {{.RepoTags}} {{.Id}}"
if ($LASTEXITCODE -ne 0) {
  throw "docker image inspect failed with exit code $LASTEXITCODE"
}
