# Re-apply STATghost VS Code extension after source changes (Win11 lab).
# Full pipeline: deploy_lab.ps1 (compile, test:unit, vsce package, install).
# Cursor has no headless Reload Window CLI — reinstall picks up on next host start.
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Here 'deploy_lab.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Optional extension-host smoke (downloads VS Code test binary on first run).
$NodeDir = 'C:\Program Files\nodejs'
if (Test-Path -LiteralPath $NodeDir) {
    $env:Path = "$NodeDir;$env:Path"
}
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host '=== npm test (extension host) ==='
    Set-Location -LiteralPath $Here
    npm test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host 'Extension updated. If the panel looks stale: Ctrl+Shift+P -> Developer: Reload Window.'
