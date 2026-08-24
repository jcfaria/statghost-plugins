# Restart Notepad++ after plugin deploy (Win11 lab).
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

& (Join-Path $Here 'install_lab.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$NppRoot = $env:NPP_ROOT
if (-not $NppRoot) {
    $ProgNpp = 'C:\Program Files\Notepad++'
    $LabNpp = Join-Path $Here '.lab'
    if (Test-Path (Join-Path $LabNpp 'notepad++.exe')) {
        $NppRoot = $LabNpp
    }
    else {
        $NppRoot = $ProgNpp
    }
}
$NppExe = Join-Path ([System.IO.Path]::GetFullPath($NppRoot)) 'notepad++.exe'

Get-Process -Name 'notepad++' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 400
Start-Process -FilePath $NppExe
Write-Host "Started: $NppExe"
