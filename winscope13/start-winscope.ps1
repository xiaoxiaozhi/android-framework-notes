# start-winscope.ps1 — 启动 WSL(AOSP13) 里的 Winscope，Windows 端只用浏览器打开
#
#   服务跑在 WSL:
#     winscope-web.service    静态站  127.0.0.1:8123  (/home/book/aosp13/development/tools/winscope/dist)
#     winscope-proxy.service  ADB 代理 127.0.0.1:5544
#   Windows 侧靠 WSL 镜像网络直接访问 127.0.0.1。
param(
  [int]$WebPort   = 8123,
  [int]$ProxyPort = 5544,
  [switch]$NoBrowser
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

function Test-Port([int]$port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect('127.0.0.1', $port)
    $c.Close()
    return $true
  } catch { return $false }
}

Write-Host ''
Write-Host '=== AOSP 13 Winscope (WSL) ===' -ForegroundColor Cyan

# ---------- 1. 确保 WSL 服务在跑 ----------
$wslOk = $false
try {
  $null = & wsl -d Ubuntu -- true 2>$null
  $wslOk = ($LASTEXITCODE -eq 0)
} catch { $wslOk = $false }

if (-not $wslOk) {
  Write-Host '[x] WSL(Ubuntu) 不可用' -ForegroundColor Red
  exit 1
}

& wsl -d Ubuntu -- sudo systemctl start winscope-web winscope-proxy 2>$null | Out-Null

# ---------- 2. 等端口 ----------
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  if ((Test-Port $WebPort) -and (Test-Port $ProxyPort)) { $ok = $true; break }
  Start-Sleep -Milliseconds 500
}
if ($ok) {
  Write-Host "[+] 静态站 http://127.0.0.1:$WebPort   (WSL winscope-web)" -ForegroundColor Green
  Write-Host "[+] ADB 代理 http://127.0.0.1:$ProxyPort  (WSL winscope-proxy)" -ForegroundColor Green
} else {
  Write-Host '[!] 端口没起来，看看：' -ForegroundColor Red
  Write-Host '    wsl -d Ubuntu -- sudo systemctl status winscope-web winscope-proxy' -ForegroundColor DarkGray
  Write-Host '    wsl -d Ubuntu -- tail -20 /home/book/winscope-web.log' -ForegroundColor DarkGray
}

# ---------- 3. token（在 WSL 里） ----------
$token = ''
try {
  $token = (& wsl -d Ubuntu -- cat /home/book/.config/winscope/.token 2>$null) -join ''
  $token = $token.Trim()
} catch { }

if ($token -eq '') {
  Write-Host '[!] 读不到 token：/home/book/.config/winscope/.token' -ForegroundColor Yellow
} else {
  Write-Host "[+] token 已读取 ($($token.Length) 字符)" -ForegroundColor Green
}

# ---------- 4. 设备 + 代理校验 ----------
if ($token -ne '') {
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:$ProxyPort/devices/" `
           -Headers @{ 'Winscope-Token' = $token } -UseBasicParsing -TimeoutSec 6
    $j = $r.Content | ConvertFrom-Json
    $names = @($j.PSObject.Properties.Name)
    if ($names.Count -gt 0) {
      Write-Host "[+] 代理识别到设备: $($names -join ', ')" -ForegroundColor Green
    } else {
      Write-Host '[!] 代理起来了但没看到设备（模拟器没开？）' -ForegroundColor Yellow
    }
  } catch {
    Write-Host "[!] 代理 /devices 校验失败: $($_.Exception.Message)" -ForegroundColor Yellow
  }
}

# ---------- 5. 打开浏览器 ----------
$url = "http://127.0.0.1:$WebPort/"
if ($token -ne '') { $url = "$url`?token=$token" }
if (-not $NoBrowser) { Start-Process $url | Out-Null }

Write-Host ''
Write-Host "打开: http://127.0.0.1:$WebPort/" -ForegroundColor Cyan
if ($token -ne '') { Write-Host "直达: $url" -ForegroundColor DarkGray }
Write-Host ''
Write-Host '服务管理:' -ForegroundColor Cyan
Write-Host '  wsl -d Ubuntu -- sudo systemctl status  winscope-web winscope-proxy' -ForegroundColor DarkGray
Write-Host '  wsl -d Ubuntu -- sudo systemctl restart winscope-web winscope-proxy' -ForegroundColor DarkGray
Write-Host ''
