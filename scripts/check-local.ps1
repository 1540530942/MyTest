$ErrorActionPreference = "Continue"

$checks = @(
  @{ Name = "platform"; Url = "http://127.0.0.1:8098/api/health" },
  @{ Name = "paper-learning"; Url = "http://127.0.0.1:8088/api/health" },
  @{ Name = "paper-hermes"; Url = "http://127.0.0.1:8091/api/health" },
  @{ Name = "remote-api"; Url = "http://127.0.0.1:8000/api/health" },
  @{ Name = "remote-sensing"; Url = "http://127.0.0.1:8090/api/health" },
  @{ Name = "camera-snapshot"; Url = "http://127.0.0.1:8099/api/health" },
  @{ Name = "web-manager"; Url = "http://127.0.0.1:8092/api/health" },
  @{ Name = "gateway"; Url = "http://127.0.0.1/api/health" }
)

$failed = 0
foreach ($check in $checks) {
  try {
    $response = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 5
    Write-Output ("OK   {0,-16} {1} {2}" -f $check.Name, [int]$response.StatusCode, $check.Url)
  } catch {
    $failed += 1
    Write-Output ("FAIL {0,-16} {1} ({2})" -f $check.Name, $check.Url, $_.Exception.Message)
  }
}

if ($failed -gt 0) {
  exit 1
}
