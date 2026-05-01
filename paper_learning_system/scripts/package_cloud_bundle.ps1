param(
  [string]$ImageArchive = "dist\paper-learning-system_local.tar",
  [string]$HermesImageArchive = "dist\paper-hermes_local.tar",
  [string]$OutputDir = "dist\cloud_bundle"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ImageArchive)) {
  throw "image archive not found: $ImageArchive"
}

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

Copy-Item -LiteralPath $ImageArchive -Destination (Join-Path $OutputDir (Split-Path -Leaf $ImageArchive)) -Force
if (Test-Path -LiteralPath $HermesImageArchive) {
  Copy-Item -LiteralPath $HermesImageArchive -Destination (Join-Path $OutputDir (Split-Path -Leaf $HermesImageArchive)) -Force
}
Copy-Item -LiteralPath "infra\docker-compose.image.yml" -Destination (Join-Path $OutputDir "infra\docker-compose.image.yml") -Force
Copy-Item -LiteralPath "infra\docker-compose.app-only.yml" -Destination (Join-Path $OutputDir "infra\docker-compose.app-only.yml") -Force
Copy-Item -LiteralPath "infra\env.cloud.example" -Destination (Join-Path $OutputDir "infra\env.cloud.example") -Force
Copy-Item -LiteralPath "infra\load-image-and-run.sh" -Destination (Join-Path $OutputDir "infra\load-image-and-run.sh") -Force
Copy-Item -LiteralPath "infra\server-setup-opencloudos.sh" -Destination (Join-Path $OutputDir "infra\server-setup-opencloudos.sh") -Force
Copy-Item -Recurse -LiteralPath "infra\caddy" -Destination (Join-Path $OutputDir "infra\caddy") -Force
Copy-Item -LiteralPath "README.md" -Destination (Join-Path $OutputDir "README.md") -Force
Copy-Item -LiteralPath "DEPLOYMENT_README.md" -Destination (Join-Path $OutputDir "DEPLOYMENT_README.md") -Force
Copy-Item -LiteralPath "docs\cloud-deployment-checklist.md" -Destination (Join-Path $OutputDir "cloud-deployment-checklist.md") -Force
Copy-Item -LiteralPath "docs\docker-image-deployment.md" -Destination (Join-Path $OutputDir "docker-image-deployment.md") -Force
Copy-Item -LiteralPath "docs\deployment-target.md" -Destination (Join-Path $OutputDir "deployment-target.md") -Force
Copy-Item -LiteralPath "docs\orcaterm-deploy-commands.md" -Destination (Join-Path $OutputDir "orcaterm-deploy-commands.md") -Force
Copy-Item -LiteralPath "docs\api.md" -Destination (Join-Path $OutputDir "api.md") -Force
Copy-Item -LiteralPath "docs\hermes-llm-gateway.md" -Destination (Join-Path $OutputDir "hermes-llm-gateway.md") -Force

$hashLines = @()
foreach ($archive in Get-ChildItem -LiteralPath $OutputDir -Filter "*.tar") {
  $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $archive.FullName
  $hashLines += "$($hash.Hash)  $($archive.Name)"
}
Set-Content -LiteralPath (Join-Path $OutputDir "SHA256SUMS.txt") -Value $hashLines

Write-Output "CLOUD_BUNDLE=$OutputDir"
Write-Output ($hashLines -join "`n")
