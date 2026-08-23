# STATghost VS Code/Cursor extension — autonomous build, test, package, install.
# Run from anywhere: powershell -File plugins\vscode\deploy_lab.ps1
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Here

# Node on PATH (winget OpenJS.NodeJS.LTS → C:\Program Files\nodejs\)
$NodeDir = 'C:\Program Files\nodejs'
if (Test-Path -LiteralPath $NodeDir) {
    $env:Path = "$NodeDir;$env:Path"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm not found. Install Node.js LTS or set PATH to include nodejs."
}

Write-Host '=== activity-bar icon (statghost.svg) ==='
python (Join-Path $Here 'scripts\mk_activity_icon.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '=== npm run compile ==='
npm run compile

Write-Host '=== npm run test:unit ==='
npm run test:unit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '=== npx @vscode/vsce package ==='
npx @vscode/vsce package --allow-missing-repository
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Vsix = Join-Path $Here 'statghost-vscode-0.1.0.vsix'
if (-not (Test-Path -LiteralPath $Vsix)) {
    Write-Error "VSIX not found after package: $Vsix"
}

$Cli = $null
$Candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\cursor\resources\app\bin\cursor.cmd'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\bin\code.cmd'),
    'C:\Program Files\Microsoft VS Code\bin\code.cmd'
)
foreach ($c in $Candidates) {
    if (Test-Path -LiteralPath $c) {
        $Cli = $c
        break
    }
}
if (-not $Cli) {
    $codeCmd = Get-Command code -ErrorAction SilentlyContinue
    if ($codeCmd) { $Cli = $codeCmd.Source }
}
if (-not $Cli) {
    Write-Error "No cursor.cmd or code.cmd found. Install Cursor or VS Code."
}

Write-Host "=== install extension via $Cli ==="
& $Cli --install-extension $Vsix --force
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ''
Write-Host "OK: $Vsix installed. Run restart_lab.ps1 or Reload Window if the host is already open."
