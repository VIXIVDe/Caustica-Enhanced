<#
.SYNOPSIS
  Builds and packages a Caustica Enhanced release from the workspace.
.DESCRIPTION
  Sets mod_version in mod/gradle.properties, runs the full offline build (shaders, native
  libraries, tests, JAR) through scripts/build.ps1, then copies the JAR into
  releases/Caustica Enhanced-v<N>/ with SHA256SUMS.txt, verification.json and the build log.
  Nothing is installed into a game instance.
#>
param(
    [Parameter(Mandatory)][int]$Release,
    [string]$JavaHome = 'C:/Program Files/Java/jdk-26.0.2'
)
$ErrorActionPreference = 'Stop'
# One workspace build at a time. The lock is re-entrant, so the build agent's runner, which already
# holds it on this thread, passes straight through; a second manual or agent build is refused.
$buildLock = New-Object System.Threading.Mutex($false, 'Local\CausticaEnhancedBuildLock')
$ownsLock = $false
try { $ownsLock = $buildLock.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $ownsLock = $true }
if (-not $ownsLock) {
    Write-Host 'Another Caustica Enhanced build is already running. Wait for it to finish, then try again.' -ForegroundColor Yellow
    exit 75
}
$workspace = Split-Path -Parent $PSScriptRoot
$mod = Join-Path $workspace 'mod'
$target = Join-Path $workspace "releases\Caustica Enhanced-v$Release"
$evidence = Join-Path $target 'evidence'
New-Item -ItemType Directory -Force $evidence | Out-Null
$log = Join-Path $evidence 'build.log'
$started = Get-Date
$result = [ordered]@{ release = "0.1.1-enhanced.$Release"; started = $started.ToString('o') }

function Save-Result($status) {
    $result.status = $status
    $result.finished = (Get-Date).ToString('o')
    $result.minutes = [math]::Round(((Get-Date) - $started).TotalMinutes, 1)
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $target 'verification.json') -Encoding UTF8
}

try {
    # Version
    $properties = Join-Path $mod 'gradle.properties'
    $text = [IO.File]::ReadAllText($properties)
    $updated = [regex]::Replace($text, '(?m)^mod_version=.*$', "mod_version=0.1.1-enhanced.$Release")
    if ($updated -ne $text) { [IO.File]::WriteAllText($properties, $updated, (New-Object System.Text.UTF8Encoding($false))) }
    Write-Host "Version: 0.1.1-enhanced.$Release"

    # Build (full: shaders changed, so compileShaders must run)
    Write-Host 'Building (full offline build; shader compilation can take ~15 minutes)...'
    # Windows PowerShell turns every redirected stderr line of a native program into an error record;
    # with 'Stop' the first JVM warning from Gradle would abort the release. The exit code decides.
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $workspace 'scripts\build.ps1') -JavaHome $JavaHome *>&1 |
        ForEach-Object { "$_" } | Tee-Object -FilePath $log | Out-Host
    $buildExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $result.buildExitCode = $buildExit
    if ($buildExit -ne 0) { throw "Build failed (exit $buildExit). See $log" }

    # Unit tests
    $tests = Get-ChildItem -LiteralPath (Join-Path $mod 'build\test-results\test') -Filter '*.xml' -ErrorAction SilentlyContinue
    $count = 0; $failures = 0; $errors = 0; $skipped = 0
    foreach ($file in $tests) {
        [xml]$xml = Get-Content -LiteralPath $file.FullName -Raw
        $suite = $xml.testsuite
        $count += [int]$suite.tests; $failures += [int]$suite.failures; $errors += [int]$suite.errors; $skipped += [int]$suite.skipped
    }
    $result.unitTests = [ordered]@{ suites = @($tests).Count; tests = $count; failures = $failures; errors = $errors; skipped = $skipped }
    if ($failures + $errors -gt 0) { throw "Unit tests failed: $failures failures, $errors errors" }

    # Package
    $jarName = "Caustica Enhanced v.$Release.jar"
    $jar = Join-Path $mod "build\libs\$jarName"
    if (-not (Test-Path -LiteralPath $jar)) { throw "Expected JAR not found: $jar" }
    Copy-Item -LiteralPath $jar -Destination $target -Force
    $hash = (Get-FileHash -LiteralPath (Join-Path $target $jarName) -Algorithm SHA256).Hash.ToLower()
    Set-Content -LiteralPath (Join-Path $target 'SHA256SUMS.txt') -Value "$hash  $jarName" -Encoding ASCII
    $result.jar = $jarName
    $result.sha256 = $hash
    $result.bytes = (Get-Item -LiteralPath (Join-Path $target $jarName)).Length
    $result.installation = 'not installed into a game instance'
    $result.gameTesting = 'not run'

    # Release index
    $index = Join-Path $workspace 'releases\README.md'
    if (Test-Path -LiteralPath $index) {
        $readme = [IO.File]::ReadAllText($index)
        $readme = [regex]::Replace($readme, 'Current release: \[Caustica Enhanced v\.\d+\]\(Caustica%20Enhanced-v\d+/\)\.',
            "Current release: [Caustica Enhanced v.$Release](Caustica%20Enhanced-v$Release/).")
        [IO.File]::WriteAllText($index, $readme, (New-Object System.Text.UTF8Encoding($false)))
    }
    Save-Result 'built'
    Write-Host ''
    Write-Host "Release ready: $target\$jarName" -ForegroundColor Green
    Write-Host "SHA-256: $hash"
    exit 0
} catch {
    $result.error = "$_"
    Save-Result 'failed'
    Write-Host "FAILED: $_" -ForegroundColor Red
    Write-Host "Log: $log"
    exit 1
}
