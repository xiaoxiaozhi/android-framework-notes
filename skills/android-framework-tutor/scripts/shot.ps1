# shot.ps1 — 用 Edge headless 给本地/远程 HTML 截图，验收排版（白底/溢出/错位）。
# 用法:
#   powershell -ExecutionPolicy Bypass -File shot.ps1 -Uri "file:///D:/path/a.html" -Out "_build\shot.png"
# 可选: -Width 1400 -Height 2400
param(
    [Parameter(Mandatory = $true)][string]$Uri,
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$Width = 1400,
    [int]$Height = 2400
)

$ErrorActionPreference = 'Stop'

$candidates = @(
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:LocalAppData\Microsoft\Edge\Application\msedge.exe"
)
$edge = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw "找不到 msedge.exe" }

if ([System.IO.Path]::IsPathRooted($Out)) {
    $outAbs = [System.IO.Path]::GetFullPath($Out)
} else {
    $outAbs = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Out))
}
$outDir = Split-Path -Parent $outAbs
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

# 独立临时 profile，避免污染默认浏览器配置；截完即删
$prof = Join-Path $env:TEMP ("awt-shot-" + [guid]::NewGuid().ToString('N'))
$edgeArgs = @(
    '--headless=new', '--disable-gpu', '--hide-scrollbars',
    "--window-size=$Width,$Height",
    "--user-data-dir=$prof",
    "--screenshot=$outAbs",
    $Uri
)
try {
    $p = Start-Process -FilePath $edge -ArgumentList $edgeArgs -NoNewWindow -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Edge 退出码 $($p.ExitCode)" }
    if (-not (Test-Path $outAbs)) { throw "截图未生成: $outAbs" }
    Write-Output ("OK 截图: {0} ({1:N0} bytes)" -f $outAbs, (Get-Item $outAbs).Length)
}
finally {
    if (Test-Path $prof) { Remove-Item $prof -Recurse -Force -ErrorAction SilentlyContinue }
}
