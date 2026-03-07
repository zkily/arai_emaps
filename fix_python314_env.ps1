# Fix Python 3.14 env (no admin): HKCU registry + User PATH
$ErrorActionPreference = 'Stop'
$regPath = 'HKCU:\SOFTWARE\Python\PythonCore\3.14\InstallPath'
$installDir = 'C:\Program Files\Python314\'

if (-not (Test-Path -LiteralPath $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
    Write-Host '[OK] Created registry path (HKCU)' -ForegroundColor Green
}
Set-ItemProperty -LiteralPath $regPath -Name '(default)' -Value $installDir -Type String
Set-ItemProperty -LiteralPath $regPath -Name 'ExecutablePath' -Value ($installDir + 'python.exe') -Type String
Set-ItemProperty -LiteralPath $regPath -Name 'WindowedExecutablePath' -Value ($installDir + 'pythonw.exe') -Type String
Write-Host '[OK] Registry updated' -ForegroundColor Green

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$bad = @('C:\Python314\Scripts\;', 'C:\Python314\Scripts', 'C:\Python314\;', 'C:\Python314')
$entries = $userPath -split ';' | Where-Object { $_.Trim() -ne '' }
$good = $entries | Where-Object { $_ -notin $bad }
$pythonPaths = 'C:\Program Files\Python314', 'C:\Program Files\Python314\Scripts'
$newUserPath = ($pythonPaths + $good) | Select-Object -Unique
$newUserPath = $newUserPath -join ';'
[Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
Write-Host '[OK] User PATH updated' -ForegroundColor Green

Write-Host "`nDone. Restart terminal, then run: py -3.14 --version  or  python --version" -ForegroundColor Cyan
