# Smart-EMAP 開発用自己署名証明書を「信頼済み」に登録（Chrome/Edge の「保護されていない通信」を解消）
# PowerShell で実行:  .\scripts\trust-dev-lan-cert.ps1
# 先に python start.py を一度実行し backend\certs\dev-lan.crt が生成されていること

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$certPath = Join-Path $root "backend\certs\dev-lan.crt"

if (-not (Test-Path $certPath)) {
    Write-Host "証明書がありません: $certPath" -ForegroundColor Red
    Write-Host "先に python start.py を実行して dev-lan.crt を生成してください。"
    exit 1
}

$store = "Cert:\CurrentUser\Root"
$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
$existing = Get-ChildItem $store -ErrorAction SilentlyContinue | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
if ($existing) {
    Write-Host "既に信頼済みです: $($cert.Subject)" -ForegroundColor Green
    exit 0
}

Import-Certificate -FilePath $certPath -CertStoreLocation $store | Out-Null
Write-Host "信頼済みルートに追加しました: $($cert.Subject)" -ForegroundColor Green
Write-Host "ブラウザを完全終了してから https:// で再アクセスしてください。"
