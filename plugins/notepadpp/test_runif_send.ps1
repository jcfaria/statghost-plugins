# Multi-line runif: Send must put entire statement in ONE EVAL clipboard payload.
$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

& (Join-Path $Here 'install_lab.ps1') | Out-Null

$Sample = Join-Path $env:TEMP "statghost_runif_test_$PID.r"
Set-Content -LiteralPath $Sample -Value "x <- runif(n,`n           0,`n           10)`ny <- 42" -Encoding UTF8

Add-Type -AssemblyName System.Windows.Forms

# SgWin32 from test_buttons harness
$lines = Get-Content (Join-Path $Here 'test_buttons.ps1')
$start = ($lines | Select-String -Pattern '^if \(-not \(''SgWin32''').LineNumber
$end = ($lines | Select-String -Pattern '^'@$').LineNumber | Select-Object -First 1
if (-not $start -or -not $end) { throw 'Could not extract SgWin32 type from test_buttons.ps1' }
$typeDef = ($lines[($start-1)..($end-1)] -join "`n") -replace '^if \(-not \(''SgWin32'' -as \[type\]\)\) \{', '' -replace '\}$', ''
Invoke-Expression $typeDef

$NppRoot = Join-Path $Here '.lab'
$NppExe = Join-Path $NppRoot 'notepad++.exe'

Get-Process notepad++ -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 400

Start-Process -FilePath $NppExe -WorkingDirectory (Split-Path $NppExe) -ArgumentList @('-nosession', $Sample) | Out-Null
Start-Sleep -Seconds 4

$proc = Get-Process -Name 'notepad++' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $proc) { throw 'NPP not started' }
$hwnd = $proc.MainWindowHandle

[SgWin32]::SetForegroundWindow($hwnd) | Out-Null
[SgWin32]::RunMenuPath($hwnd, @('Show STATghost panel')) | Out-Null
Start-Sleep -Seconds 2
[SgWin32]::FocusScintilla($hwnd)
Start-Sleep -Milliseconds 400
[System.Windows.Forms.Clipboard]::Clear()
[SgWin32]::ClickGridCaption($hwnd, 'Send') | Out-Null
Start-Sleep -Milliseconds 2500

$clip = ''
try { if ([System.Windows.Forms.Clipboard]::ContainsText()) { $clip = [System.Windows.Forms.Clipboard]::GetText() } } catch {}

$hasEval = $clip -match '#\.\s*STATGHOST:\s*EVAL'
$hasRunif = $clip -match 'runif\s*\('
$hasClose = $clip -match '10\)'
$noY = $clip -notmatch 'y\s*<-\s*42'

Write-Host "CLIP: $($clip.Substring(0, [Math]::Min(240, $clip.Length)))"

if ($hasEval -and $hasRunif -and $hasClose -and $noY) {
    Write-Host 'PASS: runif multi-line block in single EVAL' -ForegroundColor Green
    Get-Process notepad++ -ErrorAction SilentlyContinue | Stop-Process -Force
    exit 0
}
Write-Host 'FAIL: expected runif(n,...10) as one EVAL without y<-42' -ForegroundColor Red
Get-Process notepad++ -ErrorAction SilentlyContinue | Stop-Process -Force
exit 1
