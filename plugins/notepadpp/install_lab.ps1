# Lab install (Windows): deploy STATghost.dll into Notepad++ plugins\STATghost.
# Builds first unless $env:STATGHOST_NPP_SKIP_BUILD = '1'.
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $Here '..\..')

if ($env:STATGHOST_NPP_SKIP_BUILD -ne '1') {
    & (Join-Path $Here 'build_lab.ps1')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$Build = Join-Path $Here 'statghost-npp\build'
$DllCandidates = @(
    (Join-Path $Build 'bin\STATghost\Release\STATghost.dll'),
    (Join-Path $Build 'bin\STATghost\STATghost.dll'),
    (Join-Path $Here 'statghost-npp\build-mingw\bin\STATghost\STATghost.dll'),
    (Join-Path $Here 'statghost-npp\build-mingw\bin\STATghost\libSTATghost.dll')
)
$Dll = $DllCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Dll) {
    Write-Error 'STATghost.dll not found. Run build_lab.ps1 first.'
}

$NppRoot = $env:NPP_ROOT
if (-not $NppRoot) {
    $ProgNpp = 'C:\Program Files\Notepad++'
    $LabNpp = Join-Path $Here '.lab'
    if (Test-Path (Join-Path $ProgNpp 'notepad++.exe')) {
        $NppRoot = $ProgNpp
    }
    elseif (Test-Path (Join-Path $LabNpp 'notepad++.exe')) {
        $NppRoot = $LabNpp
    }
    else {
        $NppRoot = $ProgNpp
    }
}
$NppRoot = [System.IO.Path]::GetFullPath($NppRoot)
$NppExe = Join-Path $NppRoot 'notepad++.exe'
if (-not (Test-Path -LiteralPath $NppExe)) {
    Write-Error "Notepad++ not found: $NppExe (set NPP_ROOT, winget install Notepad++.Notepad++, or run build_lab once to fetch portable .lab)"
}

$PluginDir = Join-Path $NppRoot 'plugins\STATghost'
$ResDir = Join-Path $PluginDir 'res'
try {
    New-Item -ItemType Directory -Force -Path $PluginDir, $ResDir | Out-Null
}
catch {
    if ($NppRoot -like '*Program Files*') {
        $LabNpp = Join-Path $Here '.lab'
        if (-not (Test-Path (Join-Path $LabNpp 'notepad++.exe'))) {
            Write-Error "Cannot write to $PluginDir (need admin). Set NPP_ROOT to a writable tree or approve UAC for Program Files."
        }
        Write-Warning "Program Files not writable; falling back to portable lab: $LabNpp"
        $NppRoot = $LabNpp
        $NppExe = Join-Path $NppRoot 'notepad++.exe'
        $PluginDir = Join-Path $NppRoot 'plugins\STATghost'
        $ResDir = Join-Path $PluginDir 'res'
        New-Item -ItemType Directory -Force -Path $PluginDir, $ResDir | Out-Null
    }
    else {
        throw
    }
}

# Release DLL lock if N++ is still running (copy fails otherwise).
Get-Process -Name 'notepad++' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 400

$destDll = Join-Path $PluginDir 'STATghost.dll'
try {
    Copy-Item -LiteralPath $Dll -Destination $destDll -Force
}
catch {
    if ($NppRoot -like '*Program Files*') {
        $LabNpp = Join-Path $Here '.lab'
        if (-not (Test-Path (Join-Path $LabNpp 'notepad++.exe'))) {
            Write-Error "Cannot copy to $destDll (need admin). Set NPP_ROOT or run elevated."
        }
        Write-Warning "Program Files copy denied; falling back to portable lab: $LabNpp"
        $NppRoot = $LabNpp
        $NppExe = Join-Path $NppRoot 'notepad++.exe'
        $PluginDir = Join-Path $NppRoot 'plugins\STATghost'
        $ResDir = Join-Path $PluginDir 'res'
        New-Item -ItemType Directory -Force -Path $PluginDir, $ResDir | Out-Null
        $destDll = Join-Path $PluginDir 'STATghost.dll'
        Copy-Item -LiteralPath $Dll -Destination $destDll -Force
    }
    else {
        throw
    }
}

$SharedRes = Join-Path $RepoRoot 'shared\res'
$ResLink = Join-Path $ResDir 'shared'
if (Test-Path -LiteralPath $ResLink) {
    Remove-Item -LiteralPath $ResLink -Recurse -Force -ErrorAction SilentlyContinue
}
try {
    New-Item -ItemType Junction -Path $ResLink -Target $SharedRes | Out-Null
    Write-Host "res junction: $ResLink -> $SharedRes"
}
catch {
    Write-Warning "Junction failed ($($_.Exception.Message)); copying statghost icons only."
    $IconSets = @('24px', '32px')
    foreach ($set in $IconSets) {
        $src = Join-Path $SharedRes $set
        $dst = Join-Path $ResDir $set
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Copy-Item (Join-Path $src 'statghost.png') -Destination $dst -Force -ErrorAction SilentlyContinue
        Copy-Item (Join-Path $src 'statghost_24.png') -Destination $dst -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ''
Write-Host "Plugin deployed: $PluginDir\STATghost.dll"
Write-Host "Restart: $NppExe"
Write-Host 'Menu: Plugins -> STATghost'
