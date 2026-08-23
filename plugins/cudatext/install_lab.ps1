# Lab install (Windows): junction cuda_statghost into CudaText-jcf portable tree.
# Default target: ~/Documents/Github/CudaText-jcf/app/bin/windows-amd64/py/
# Override: $env:CUDA_ROOT = 'D:\path\to\portable\cuda\root'  (must contain py\)
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginSrc = Join-Path $Here 'cuda_statghost'
if (-not (Test-Path -LiteralPath $PluginSrc)) {
    Write-Error "Plugin source not found: $PluginSrc"
}

$CudaRoot = $env:CUDA_ROOT
if (-not $CudaRoot) {
    $CudaRoot = Join-Path $env:USERPROFILE 'Documents\Github\CudaText-jcf\app\bin\windows-amd64'
}
$CudaRoot = [System.IO.Path]::GetFullPath($CudaRoot)
$PyDir = Join-Path $CudaRoot 'py'
if (-not (Test-Path -LiteralPath $PyDir)) {
    Write-Error "CudaText py/ not found under CUDA_ROOT: $PyDir"
}

$Target = Join-Path $PyDir 'cuda_statghost'
$PluginSrc = [System.IO.Path]::GetFullPath($PluginSrc)

if (Test-Path -LiteralPath $Target) {
    Remove-Item -LiteralPath $Target -Recurse -Force
}

New-Item -ItemType Junction -Path $Target -Target $PluginSrc | Out-Null
Write-Host "Plugin: $Target -> $PluginSrc"
Write-Host ""
Write-Host "Restart CudaText-jcf: $CudaRoot\cudatext.exe"
Write-Host "Menu: Plugins -> STATghost"
