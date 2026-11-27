# sync-skills.ps1 — 把真实技能目录同步到本仓库 skills/ 下
#
# 仓库里的 skills/ 只是副本，用于 git 同步到另一台电脑。
# 技能真正生效的位置是下面 $Sources 里列的那两处。
#
# 用法：
#   .\sync-skills.ps1           # 单向覆盖：真实 -> 仓库
#   .\sync-skills.ps1 -Check    # 只比较，不写入（看哪些技能有改动）
#
# 改完技能后跑一次，再 git add / commit / push。

param([switch]$Check)

$ErrorActionPreference = 'Stop'

$RepoSkills = Join-Path $PSScriptRoot 'skills'
$Workspace  = 'D:\openclaw\skills'
$Workshop   = Join-Path $env:USERPROFILE '.openclaw\agents\main\agent\workshop-skills'

# 技能名 -> 真实来源
$Sources = [ordered]@{
    'android-framework-tutor'           = Join-Path $Workspace 'android-framework-tutor'
    'android-source-html-analyzer'      = Join-Path $Workspace 'android-source-html-analyzer'
    'framework-learning-round'          = Join-Path $Workspace 'framework-learning-round'
    'android-article-series'            = Join-Path $Workshop  'android-article-series'
    'android-framework-learning-plan'   = Join-Path $Workshop  'android-framework-learning-plan'
    'aosp-caller-trace'                 = Join-Path $Workshop  'aosp-caller-trace'
    'aosp-progressive-code-walkthrough' = Join-Path $Workshop  'aosp-progressive-code-walkthrough'
    'html-headless-verify'              = Join-Path $Workshop  'html-headless-verify'
    'md-html-pdf-artifact-resync'       = Join-Path $Workshop  'md-html-pdf-artifact-resync'
}

function Get-TreeHash([string]$dir) {
    if (-not (Test-Path $dir)) { return $null }
    $lines = Get-ChildItem $dir -Recurse -File -Force |
        Sort-Object FullName |
        ForEach-Object { $_.FullName.Substring($dir.Length) + '|' + (Get-FileHash $_.FullName -Algorithm SHA256).Hash }
    return ($lines -join "`n")
}

$changed = @()
foreach ($name in $Sources.Keys) {
    $src = $Sources[$name]
    $dst = Join-Path $RepoSkills $name

    if (-not (Test-Path $src)) { Write-Warning "真实技能不存在，跳过：$name  ($src)"; continue }

    $hSrc = Get-TreeHash $src
    $hDst = Get-TreeHash $dst

    if ($hSrc -eq $hDst) { continue }
    $changed += $name

    if ($Check) {
        Write-Host "[有差异] $name"
    } else {
        if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
        Copy-Item $src $dst -Recurse -Force
        $n = (Get-ChildItem $dst -Recurse -File).Count
        Write-Host "[已同步] $name  ($n files)"
    }
}

if ($changed.Count -eq 0) {
    Write-Host '全部一致，无需同步。'
} elseif ($Check) {
    Write-Host ''
    Write-Host ('共 ' + $changed.Count + ' 个技能与真实目录不一致。去掉 -Check 执行同步。')
}
