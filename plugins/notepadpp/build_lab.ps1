# VP-NPP-1 build helper — configures and compiles STATghost.dll (x64 Release).
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Src = Join-Path $Here 'statghost-npp'

$CmakeCandidates = @(
    'C:\Program Files\CMake\bin\cmake.exe',
    'cmake'
)
$Cmake = $null
foreach ($c in $CmakeCandidates) {
    if ($c -eq 'cmake') {
        $cmd = Get-Command cmake -ErrorAction SilentlyContinue
        if ($cmd) { $Cmake = $cmd.Source; break }
    }
    elseif (Test-Path -LiteralPath $c) {
        $Cmake = $c
        break
    }
}
if (-not $Cmake) {
    Write-Error 'cmake not found. Install Kitware.CMake (winget) and reopen the shell.'
}

$VsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$VsPath = $null
if (Test-Path -LiteralPath $VsWhere) {
    $VsPath = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
}

$UseMingw = $false
if (-not $VsPath) {
    $W64Bin = Join-Path $Here '.tools\w64devkit\w64devkit\bin'
    if (-not (Test-Path (Join-Path $W64Bin 'g++.exe'))) {
        $tools = Join-Path $Here '.tools'
        $exe = Join-Path $tools 'w64devkit-x64-2.9.1.7z.exe'
        $out = Join-Path $tools 'w64devkit'
        if (-not (Test-Path $exe)) {
            Write-Host 'Fetching w64devkit (MinGW lab fallback, ~60 MB)...'
            New-Item -ItemType Directory -Force -Path $tools | Out-Null
            Invoke-WebRequest -Uri 'https://github.com/skeeto/w64devkit/releases/download/v2.9.1/w64devkit-x64-2.9.1.7z.exe' -OutFile $exe -UseBasicParsing
        }
        if (-not (Test-Path (Join-Path $W64Bin 'g++.exe'))) {
            Write-Host 'Extracting w64devkit...'
            Start-Process -FilePath $exe -ArgumentList "-o$out",'-y' -Wait
        }
        $W64Bin = Join-Path $Here '.tools\w64devkit\w64devkit\bin'
    }
    if (Test-Path (Join-Path $W64Bin 'g++.exe')) {
        Write-Host 'MSVC not found; using w64devkit MinGW (lab fallback).'
        $env:Path = "$W64Bin;$env:Path"
        $UseMingw = $true
    }
    else {
        Write-Error 'MSVC toolset not found. Install VS Build Tools workload VCTools or allow w64devkit download.'
    }
}

$BuildDirName = if ($UseMingw) { 'build-mingw' } else { 'build' }
$Build = Join-Path $Src $BuildDirName

if ($UseMingw) {
    Write-Host '=== cmake configure (MinGW) ==='
    & $Cmake -S $Src -B $Build -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release
}
else {
    $VcVars = Join-Path $VsPath 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path -LiteralPath $VcVars)) {
        Write-Error "vcvars64.bat not found under: $VsPath"
    }
    Write-Host '=== cmake configure (x64 MSVC) ==='
    & $Cmake -S $Src -B $Build -A x64
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '=== cmake build Release ==='
if ($UseMingw) {
    & $Cmake --build $Build
}
else {
    & $Cmake --build $Build --config Release
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$DllCandidates = @(
    (Join-Path $Build 'bin\STATghost\Release\STATghost.dll'),
    (Join-Path $Build 'bin\STATghost\STATghost.dll')
)
$Dll = $DllCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Dll) {
    Write-Error "Build finished but DLL not found under $Build\bin\STATghost"
}

Write-Host ''
Write-Host "OK: $Dll"
