$src = 'c:\Users\jcfaria\Documents\Github\statghost-plugins\plugins\notepadpp\statghost-npp\build\bin\STATghost\Release\STATghost.dll'
$dst = 'C:\Program Files\Notepad++\plugins\STATghost\STATghost.dll'
Get-Process notepad++ -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 400
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
Copy-Item -LiteralPath $src -Destination $dst -Force
Write-Host "OK: $dst"
