# Restart CudaText-jcf after plugin Python changes (Win11 lab).
$ErrorActionPreference = 'Stop'

$CudaRoot = $env:CUDA_ROOT
if (-not $CudaRoot) {
    $CudaRoot = Join-Path $env:USERPROFILE 'Documents\Github\CudaText-jcf\app\bin\windows-amd64'
}
$CudaExe = Join-Path $CudaRoot 'cudatext.exe'
if (-not (Test-Path -LiteralPath $CudaExe)) {
    Write-Error "CudaText-jcf not found: $CudaExe"
}

$resolved = (Resolve-Path -LiteralPath $CudaExe).Path
Get-Process -Name 'cudatext' -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        if ($_.Path -and ((Resolve-Path -LiteralPath $_.Path).Path -eq $resolved)) {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # ignore stale / exited handles
    }
}
Start-Sleep -Milliseconds 400
Start-Process -FilePath $resolved
Write-Host "Restarted: $resolved"
