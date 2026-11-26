param(
  [int]$WebPort = 8123,
  [int]$ProxyPort = 5544,
  [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir
$logDir = Join-Path $dir 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

function Test-Port([int]$port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect('127.0.0.1', $port)
    $c.Close()
    return $true
  } catch { return $false }
}

function Wait-Port([int]$port, [int]$seconds = 10) {
  for ($i = 0; $i -lt $seconds * 2; $i++) {
    if (Test-Port $port) { return $true }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

# 1. 静态服务
if (-not (Test-Port $WebPort)) {
  Start-Process -FilePath 'python' -ArgumentList @('-m','http.server',"$WebPort",'--bind','127.0.0.1') `
    -WorkingDirectory $dir -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logDir 'web.log') -RedirectStandardError (Join-Path $logDir 'web.err')
  if (Wait-Port $WebPort) {
    Write-Host "[+] 静态服务: http://127.0.0.1:$WebPort/" -ForegroundColor Green
  } else {
    Write-Host "[!] 静态服务未起来，看 logs\web.err" -ForegroundColor Red
  }
} else {
  Write-Host "[=] 端口 $WebPort 已在监听，跳过静态服务" -ForegroundColor DarkGray
}

# 2. ADB 代理（端口偶发被 TIME_WAIT 占住，失败重试一次）
if (-not (Test-Port $ProxyPort)) {
  $ok = $false
  for ($attempt = 1; $attempt -le 3 -and -not $ok; $attempt++) {
    Start-Process -FilePath 'python' -ArgumentList ('"' + (Join-Path $dir 'winscope_proxy.py') + '"') `
      -WorkingDirectory $dir -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $logDir 'proxy.log') -RedirectStandardError (Join-Path $logDir 'proxy.err')
    $ok = Wait-Port $ProxyPort 6
    if (-not $ok) { Start-Sleep -Seconds 2 }
  }
  if ($ok) {
    Write-Host "[+] ADB 代理: http://localhost:$ProxyPort/ (v0.8)" -ForegroundColor Green
  } else {
    Write-Host "[!] ADB 代理未起来，看 logs\proxy.err；不影响手工 ADD FILE" -ForegroundColor Yellow
  }
} else {
  Write-Host "[=] 端口 $ProxyPort 已在监听，跳过 ADB 代理" -ForegroundColor DarkGray
}

# 3. 带 token 打开
$tokenFile = Join-Path $env:USERPROFILE '.config\winscope\.token'
$url = "http://127.0.0.1:$WebPort/"
if (Test-Path $tokenFile) {
  $token = (Get-Content $tokenFile -Raw).Trim()
  $url = "http://127.0.0.1:$WebPort/?token=$token"
}
if (-not $NoBrowser) { Start-Process $url }

Write-Host ""
Write-Host "打开: http://127.0.0.1:$WebPort/  （带 token 可直连设备；不带则手工粘 token）" -ForegroundColor Cyan
Write-Host "token: $tokenFile" -ForegroundColor DarkGray
Write-Host ""
Write-Host "抓 trace:" -ForegroundColor Cyan
Write-Host "  adb shell wm tracing start / stop        -> wm_trace.pb"
Write-Host "  adb shell su root service call SurfaceFlinger 1025 i32 1 / 0  -> layers_trace.pb"
