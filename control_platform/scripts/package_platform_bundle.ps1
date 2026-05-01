param(
  [string]$OutputDir = "dist\platform_bundle",
  [string]$ControlImage = "control-platform:local",
  [string]$PaperImageArchive = "..\paper_learning_system\dist\paper-learning-system_local.tar",
  [string]$HermesImageArchive = "..\paper_learning_system\dist\paper-hermes_local.tar",
  [string]$CameraImageArchive = "..\..\..\Harness\pi_TurboPi\camera_snapshot\dist\camera-snapshot_local.tar"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path ".").Path
$resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDir)
if (-not $resolvedOutput.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "OutputDir must stay inside the project directory: $OutputDir"
}

if (Test-Path -LiteralPath $OutputDir) {
  Remove-Item -LiteralPath $OutputDir -Recurse -Force
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $OutputDir "infra") -Force | Out-Null

& docker image inspect $ControlImage | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "image not found: $ControlImage"
}

$controlArchive = Join-Path $OutputDir "control-platform_local.tar"
& docker save -o $controlArchive $ControlImage
if ($LASTEXITCODE -ne 0) {
  throw "docker save failed for $ControlImage"
}

if (Test-Path -LiteralPath $PaperImageArchive) {
  Copy-Item -LiteralPath $PaperImageArchive -Destination (Join-Path $OutputDir "paper-learning-system_local.tar") -Force
}
if (Test-Path -LiteralPath $HermesImageArchive) {
  Copy-Item -LiteralPath $HermesImageArchive -Destination (Join-Path $OutputDir "paper-hermes_local.tar") -Force
}
if (Test-Path -LiteralPath $CameraImageArchive) {
  Copy-Item -LiteralPath $CameraImageArchive -Destination (Join-Path $OutputDir "camera-snapshot_local.tar") -Force
}

Copy-Item -LiteralPath "infra\docker-compose.platform.yml" -Destination (Join-Path $OutputDir "infra\docker-compose.platform.yml") -Force
Copy-Item -LiteralPath "infra\env.platform.example" -Destination (Join-Path $OutputDir "infra\env.platform.example") -Force
Copy-Item -Recurse -LiteralPath "infra\caddy" -Destination (Join-Path $OutputDir "infra\caddy") -Force
Copy-Item -LiteralPath "README.md" -Destination (Join-Path $OutputDir "README.md") -Force
Copy-Item -Recurse -LiteralPath "docs" -Destination (Join-Path $OutputDir "docs") -Force
Copy-Item -LiteralPath "modules\registry.json" -Destination (Join-Path $OutputDir "registry.json") -Force

$paperDocsRoot = "..\paper_learning_system\docs"
if (Test-Path -LiteralPath $paperDocsRoot) {
  $paperDocsOut = Join-Path $OutputDir "docs\paper_learning"
  New-Item -ItemType Directory -Path $paperDocsOut -Force | Out-Null
  foreach ($docName in @("api.md", "hermes-llm-gateway.md", "cloud-deployment-checklist.md", "docker-image-deployment.md")) {
    $docPath = Join-Path $paperDocsRoot $docName
    if (Test-Path -LiteralPath $docPath) {
      Copy-Item -LiteralPath $docPath -Destination (Join-Path $paperDocsOut $docName) -Force
    }
  }
}

$hashLines = @()
foreach ($archive in Get-ChildItem -LiteralPath $OutputDir -Filter "*.tar") {
  $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $archive.FullName
  $hashLines += "$($hash.Hash)  $($archive.Name)"
}
Set-Content -LiteralPath (Join-Path $OutputDir "SHA256SUMS.txt") -Value $hashLines

Write-Output "PLATFORM_BUNDLE=$OutputDir"
Write-Output ($hashLines -join "`n")
