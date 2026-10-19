<#
.SYNOPSIS
  Offline build of the Caustica Enhanced mod using the workspace toolchain.
.PARAMETER Fast
  Skip shader compilation and the sources JAR. Use only when compiled shaders already match source.
.PARAMETER JavaHome
  JDK used to run Gradle. Defaults to the local JDK 26 installation.
.PARAMETER Tasks
  Gradle tasks to run. Defaults to "build" (or "test jar" with -Fast).
#>
param(
    [switch]$Fast,
    [string]$JavaHome = 'C:/Program Files/Java/jdk-26.0.2',
    [string[]]$Tasks
)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$mod = Join-Path $workspace 'mod'

. (Join-Path $workspace 'toolchain/env.ps1')
if (-not (Test-Path -LiteralPath (Join-Path $JavaHome 'bin/java.exe'))) {
    throw "JDK not found at $JavaHome. Pass -JavaHome <jdk-26-directory>."
}
$env:JAVA_HOME = $JavaHome
$env:Path = "$JavaHome/bin;$env:Path"

if (-not $Tasks) { $Tasks = if ($Fast) { @('test', 'jar') } else { @('build') } }
$extra = @('--offline', '--stacktrace')
if ($Fast) { $extra += @('-x', 'compileShaders', '-x', 'sourcesJar') }

# Gradle/JDK write warnings to stderr; do not let PowerShell treat them as terminating errors.
$ErrorActionPreference = 'Continue'
& (Join-Path $mod 'gradlew.bat') -p $mod @Tasks @extra 2>&1 | ForEach-Object { "$_" }
$ErrorActionPreference = 'Stop'
if ($LASTEXITCODE -ne 0) { throw "Gradle failed with exit code $LASTEXITCODE" }
Get-ChildItem -LiteralPath (Join-Path $mod 'build/libs') -Filter '*.jar' |
    Sort-Object LastWriteTime -Descending | Select-Object -First 3 |
    ForEach-Object { Write-Host ("Built: {0} ({1:N0} MB)" -f $_.FullName, ($_.Length / 1MB)) }
