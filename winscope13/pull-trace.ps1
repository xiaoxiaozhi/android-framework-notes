# pull-trace.ps1 — 只负责把设备上已有的 Winscope trace 文件拉到 Windows
#   * 不启动/不停止 tracing（抓取请在 Winscope 网页里点 Start trace / Stop trace）
#   * 输出: D:\winscope-traces\<yyyy-MM-dd_HH-mm-ss>[_标签]\
#   * 拉完把 .winscope 拖进 http://127.0.0.1:8123 页面即可回放
param(
  [string]$OutRoot = 'D:\winscope-traces',
  [string]$Device  = '',
  [string]$Label   = '',
  [switch]$NoOpen
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

$adb = 'D:\AndroidSdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { $adb = 'adb' }
$script:dev = ''
$script:buf = New-Object System.Collections.Generic.List[string]

function Log([string]$text, [string]$color = 'Gray') {
  Write-Host $text -ForegroundColor $color
  $script:buf.Add($text)
}

function Adb([string]$cmd) {
  return @(& $adb -s $script:dev shell $cmd 2>&1 | ForEach-Object { "$_" })
}

# ---------- 选设备 ----------
$devices = @(
  (& $adb devices) 2>$null |
    Select-Object -Skip 1 |
    Where-Object { $_ -match '\sdevice$' } |
    ForEach-Object { ($_ -split '\s+')[0] }
)

if ($Device -ne '') {
  $script:dev = $Device
} elseif ($devices.Count -eq 1) {
  $script:dev = $devices[0]
} elseif ($devices.Count -gt 1) {
  Write-Host "[!] 多台设备: $($devices -join ', ')" -ForegroundColor Yellow
  $script:dev = Read-Host '    输入要拉的设备序列号'
} else {
  Write-Host '[x] 没有已连接设备。先启动模拟器（emu13.bat）。' -ForegroundColor Red
  exit 1
}

Write-Host ''
Log "=== 拉取 Winscope 文件  ($($script:dev)) ===" 'Cyan'

# ---------- 设备上有什么 ----------
$remoteDir = '/data/misc/wmtrace'
$listing = Adb "ls -l $remoteDir"
if (($listing -join ' ') -match 'No such file|Permission denied|not found') {
  Log "[x] 设备上 $remoteDir 不能读：$($listing -join ' ')" 'Red'
  exit 1
}

# 解析 "ls -l" 行 -> 名字 + 大小 + 时间
$entries = @()
foreach ($line in $listing) {
  if ($line -match '^\S+\s+\d+\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)$') {
    $entries += [pscustomobject]@{
      Name = $Matches[6].Trim()
      Size = [int64]$Matches[3]
      Time = "$($Matches[4]) $($Matches[5])"
    }
  }
}

if ($entries.Count -eq 0) {
  Log '[x] 设备上没有任何 trace 文件。' 'Red'
  Log "    先到 http://127.0.0.1:8123 里点 Start trace，操作后再 Stop trace。" 'Yellow'
  exit 1
}

Log "设备上找到 $($entries.Count) 个文件:" 'DarkGray'
foreach ($e in $entries) {
  $kb = [math]::Round($e.Size / 1KB, 1)
  Log ("      {0,-34} {1,9} KB   {2}" -f $e.Name, $kb, $e.Time) 'DarkGray'
}

# ---------- 输出目录 ----------
$stamp   = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$dirName = if ($Label -ne '') { "$stamp`_$Label" } else { $stamp }
$outDir  = Join-Path $OutRoot $dirName
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

# ---------- 拉取 ----------
Write-Host ''
$got = 0
$fail = 0
foreach ($e in $entries) {
  $remote = "$remoteDir/$($e.Name)"
  $local  = Join-Path $outDir $e.Name
  & $adb -s $script:dev pull $remote $local 2>&1 | Out-Null
  if ((Test-Path $local) -and ((Get-Item $local).Length -gt 0)) {
    $kb = [math]::Round((Get-Item $local).Length / 1KB, 1)
    Log "      + $($e.Name)  (${kb} KB)" 'Green'
    $got++
  } else {
    Log "      ! $($e.Name) 拉取失败" 'Red'
    $fail++
  }
}

# ---------- meta ----------
$focus = ((Adb 'dumpsys window') | Select-String 'mCurrentFocus' | Select-Object -First 1)
$rel   = (Adb 'getprop ro.build.version.release') -join ''
$meta = @(
  "time        : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  "device      : $($script:dev)",
  "fingerprint : $((Adb 'getprop ro.build.fingerprint') -join '')",
  "release     : $($rel.Trim())",
  "wm size     : $((Adb 'wm size') -join ' ')",
  "wm density  : $((Adb 'wm density') -join ' ')",
  "focus       : $focus",
  "label       : $Label",
  "source dir  : $remoteDir",
  "files       : $($entries.Name -join ', ')"
)
$meta | Set-Content (Join-Path $outDir 'meta.txt') -Encoding UTF8

Write-Host ''
if ($got -eq 0) {
  Log '[x] 一个都没拉到。' 'Red'
  exit 1
}
Log "[+] 完成：$got 个文件" 'Green'
Log "    $outDir" 'Green'
Log '    把这些 .winscope 拖进 http://127.0.0.1:8123 的页面即可。' 'Cyan'
$script:buf | Set-Content (Join-Path $outDir 'pull.log') -Encoding UTF8

if (-not $NoOpen) { Start-Process explorer.exe $outDir | Out-Null }
