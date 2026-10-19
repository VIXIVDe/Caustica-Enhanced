<#
  Caustica Enhanced local build agent.

  Watches devtools/build-agent/requests/ for <id>.json files and runs one whitelisted action per
  request with the workspace toolchain. A request selects an action and bounded parameters only;
  it can never supply a command line, path or script.

    {"action": "build"}                        full offline build (scripts/build.ps1)
    {"action": "fast"}                         Java/UI build without shader compilation
    {"action": "release", "release": N}        build, test and package a release record under releases/
    {"action": "test", "name": "cloud_math"}   one native GPU test, mod/native/tests/<name>.ps1
    {"action": "processes"}                    report workspace build processes
    {"action": "stop-builds"}                  stop every other workspace build and its Gradle daemons
    {"action": "stop-gradle"}                  stop this workspace's Gradle daemons
    {"action": "restart-agent"}                reload this script after it has been updated

  Results:  results/<id>/status.json, output.log (timestamped, written live), summary.txt
  Cancel:   create requests/<id>.cancel while the request runs; Gradle daemons are stopped too
  Liveness: agent.json is rewritten every few seconds
  Builds and releases hold a workspace-wide lock, so a manually started build cannot run alongside.
#>
param([int]$TimeoutMinutes = 90)
$ErrorActionPreference = 'Stop'
$agentVersion = 2
$agentRoot = $PSScriptRoot
$workspace = Split-Path -Parent (Split-Path -Parent $agentRoot)
$mod = Join-Path $workspace 'mod'
$requests = Join-Path $agentRoot 'requests'
$results = Join-Path $agentRoot 'results'
$done = Join-Path $agentRoot 'done'
$runner = Join-Path $agentRoot 'run-action.ps1'
$supervisor = Join-Path $agentRoot 'supervisor.cmd'
$supervised = $env:CAUSTICA_AGENT_SUPERVISED -eq '1'
foreach ($d in @($requests, $results, $done)) { New-Item -ItemType Directory -Force $d | Out-Null }
$utf8 = New-Object System.Text.UTF8Encoding($false)

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Local\CausticaEnhancedBuildAgent', [ref]$created)
if (-not $created) { Write-Host 'The build agent is already running.'; exit 0 }

function Write-Json($path, $value) {
    $temporary = "$path.tmp"
    [IO.File]::WriteAllText($temporary, ($value | ConvertTo-Json -Depth 6), $utf8)
    Move-Item -LiteralPath $temporary -Destination $path -Force
}
function Heartbeat($state, $current) {
    Write-Json (Join-Path $agentRoot 'agent.json') ([ordered]@{
        version = $agentVersion; pid = $PID; supervised = $supervised; state = $state; current = $current
        heartbeat = (Get-Date).ToString('o'); workspace = $workspace })
}
function Log-Line($log, [string]$text) {
    Add-Content -LiteralPath $log -Value ('{0:HH:mm:ss} {1}' -f (Get-Date), $text) -Encoding UTF8
}

# The agent no longer starts with Windows. Remove any sign-in entry left over from earlier versions.
function Remove-Autostart {
    try {
        $entry = Join-Path ([Environment]::GetFolderPath('Startup')) 'Caustica Enhanced build agent.cmd'
        if (Test-Path -LiteralPath $entry) { Remove-Item -LiteralPath $entry -Force }
    } catch { Write-Host "Autostart entry not removed: $_" }
}

# Processes that belong to a build of this workspace. A game instance never matches: only Gradle,
# build scripts and native compilers are recognised.
$buildMarkers = 'GradleDaemon|GradleWrapperMain|gradlew|build-release\.ps1|scripts\\build\.ps1|BUILD-v\d+\.cmd|run-action\.ps1|cmake|nmake|slangc|spirv-val|\\cl\.exe|\\link\.exe'
function Workspace-BuildProcesses {
    $self = @($PID)
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine.IndexOf($workspace, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        $_.CommandLine -match $buildMarkers -and $_.CommandLine -notmatch 'build-agent\\agent\.ps1|supervisor\.cmd' -and
        $self -notcontains $_.ProcessId
    }
}
function Describe($p) {
    [ordered]@{ pid = $p.ProcessId; parent = $p.ParentProcessId; name = $p.Name
        started = if ($p.CreationDate) { $p.CreationDate.ToString('o') } else { $null }
        command = if ($p.CommandLine.Length -gt 400) { $p.CommandLine.Substring(0, 400) + '...' } else { $p.CommandLine } }
}
function Stop-Tree($processId) { & taskkill.exe /T /F /PID $processId 2>&1 | Out-Null }
function Stop-GradleDaemons($log) {
    $saved = @{ JAVA_HOME = $env:JAVA_HOME; GRADLE_USER_HOME = $env:GRADLE_USER_HOME }
    try {
        if (Test-Path 'C:\Program Files\Java\jdk-26.0.2') { $env:JAVA_HOME = 'C:\Program Files\Java\jdk-26.0.2' }
        $env:GRADLE_USER_HOME = Join-Path $workspace 'toolchain\gradle-home'
        $output = & (Join-Path $mod 'gradlew.bat') -p $mod --stop 2>&1 | Out-String
        if ($log) { Log-Line $log ("gradle --stop: " + $output.Trim()) }
    } catch { if ($log) { Log-Line $log "gradle --stop failed: $_" } }
    finally { $env:JAVA_HOME = $saved.JAVA_HOME; $env:GRADLE_USER_HOME = $saved.GRADLE_USER_HOME }
}

# Each action maps to a fixed script and typed parameters inside the workspace.
function Resolve-Action($request) {
    $action = [string]$request.action
    switch ($action) {
        'build' { return @{ script = (Join-Path $workspace 'scripts\build.ps1'); parameters = @{}; lock = $true } }
        'fast' { return @{ script = (Join-Path $workspace 'scripts\build.ps1'); parameters = @{ Fast = $true }; lock = $true } }
        'release' {
            $release = 0
            if (-not [int]::TryParse([string]$request.release, [ref]$release) -or $release -lt 1 -or $release -gt 999) {
                throw 'release must be an integer between 1 and 999'
            }
            return @{ script = (Join-Path $workspace 'devtools\build-release.ps1'); parameters = @{ Release = $release }; lock = $true }
        }
        'test' {
            $name = [string]$request.name
            if ($name -notmatch '^[a-z0-9_]{1,40}$') { throw 'test name must match [a-z0-9_]' }
            $script = Join-Path $mod "native\tests\$name.ps1"
            if (-not (Test-Path -LiteralPath $script)) { throw "unknown native test: $name" }
            return @{ script = $script; parameters = @{}; environment = $true }
        }
        default { throw "unknown action: $action" }
    }
}

function Summarize($log) {
    if (-not (Test-Path -LiteralPath $log)) { return '' }
    $patterns = 'error|FAILED|BUILD SUCCESSFUL|BUILD FAILED|Exception|warning: |e: |Release ready|SHA-256|Exit code|build lock'
    (Select-String -LiteralPath $log -Pattern $patterns -CaseSensitive:$false | Select-Object -Last 200 |
        ForEach-Object { "$($_.LineNumber): $($_.Line)" }) -join "`r`n"
}

function Finish($file, $statusPath, $status) {
    $status.finished = (Get-Date).ToString('o')
    Write-Json $statusPath $status
    Move-Item -LiteralPath $file.FullName -Destination (Join-Path $done $file.Name) -Force
}

function Run-Request($file) {
    $id = [IO.Path]::GetFileNameWithoutExtension($file.Name)
    $out = Join-Path $results $id
    $status = [ordered]@{ id = $id; state = 'running'; agentVersion = $agentVersion; received = (Get-Date).ToString('o') }
    try {
        if ($id -notmatch '^[A-Za-z0-9_-]{1,64}$') { throw 'request id must match [A-Za-z0-9_-]' }
        New-Item -ItemType Directory -Force $out | Out-Null
    } catch {
        Move-Item -LiteralPath $file.FullName -Destination (Join-Path $done ($file.Name + '.rejected')) -Force
        return
    }
    $statusPath = Join-Path $out 'status.json'
    $log = Join-Path $out 'output.log'
    try {
        $request = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $status.action = [string]$request.action
        Write-Json $statusPath $status
        Heartbeat 'running' $id

        switch ($status.action) {
            'restart-agent' {
                $status.state = 'succeeded'; Finish $file $statusPath $status
                $mutex.ReleaseMutex()
                if ($supervised) { exit 3 }
                Start-Process cmd.exe -ArgumentList @('/c', "start `"Caustica build agent`" /min cmd /c `"`"$supervisor`"`"") -WindowStyle Hidden
                exit 0
            }
            'processes' {
                $list = @(Workspace-BuildProcesses | ForEach-Object { Describe $_ })
                Write-Json (Join-Path $out 'processes.json') $list
                $status.processes = $list.Count; $status.state = 'succeeded'; Finish $file $statusPath $status; return
            }
            'stop-builds' {
                $list = @(Workspace-BuildProcesses)
                $ids = @($list | ForEach-Object { $_.ProcessId })
                # Stop only the roots; taskkill /T removes their children.
                foreach ($p in $list | Where-Object { $ids -notcontains $_.ParentProcessId }) {
                    Log-Line $log "Stopping $($p.ProcessId) $($p.Name)"; Stop-Tree $p.ProcessId
                }
                Stop-GradleDaemons $log
                Start-Sleep -Seconds 2
                $left = @(Workspace-BuildProcesses | ForEach-Object { Describe $_ })
                Write-Json (Join-Path $out 'processes.json') $left
                $status.stopped = $list.Count; $status.remaining = $left.Count
                $status.state = if ($left.Count -eq 0) { 'succeeded' } else { 'failed' }
                Finish $file $statusPath $status; return
            }
            'stop-gradle' {
                Stop-GradleDaemons $log
                $status.state = 'succeeded'; Finish $file $statusPath $status; return
            }
        }

        $plan = Resolve-Action $request
        $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($plan.parameters | ConvertTo-Json -Compress)))
        $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$runner`"",
            '-Script', "`"$($plan.script)`"", '-Log', "`"$log`"", '-Parameters', $encoded)
        if ($plan.environment) { $arguments += '-Environment' }
        if ($plan.lock) { $arguments += '-Lock' }
        $process = Start-Process powershell -ArgumentList $arguments -WorkingDirectory $workspace -WindowStyle Hidden -PassThru
        $null = $process.Handle
        $deadline = (Get-Date).AddMinutes($TimeoutMinutes)
        $cancel = Join-Path $requests "$id.cancel"
        while (-not $process.WaitForExit(5000)) {
            Heartbeat 'running' $id
            if (Test-Path -LiteralPath $cancel) { $status.cancelled = $true; break }
            if ((Get-Date) -gt $deadline) { $status.timedOut = $true; break }
        }
        if ($status.cancelled -or $status.timedOut) {
            Log-Line $log ($(if ($status.cancelled) { 'Cancel requested' } else { 'Timed out' }))
            Stop-Tree $process.Id
            Stop-GradleDaemons $log
        }
        $process.WaitForExit()
        $status.exitCode = $process.ExitCode
        $status.state = if ($status.cancelled) { 'cancelled' } elseif ($status.timedOut) { 'timed-out' }
                        elseif ($process.ExitCode -eq 75) { 'blocked' }
                        elseif ($process.ExitCode -eq 0) { 'succeeded' } else { 'failed' }
        [IO.File]::WriteAllText((Join-Path $out 'summary.txt'), (Summarize $log), $utf8)
        if (Test-Path -LiteralPath $cancel) { Remove-Item -LiteralPath $cancel -Force }
    } catch {
        $status.state = 'rejected'
        $status.error = "$_"
    }
    Finish $file $statusPath $status
}

Remove-Autostart
Write-Host "Caustica build agent v$agentVersion watching $requests"
Write-Host 'Close this window to stop the agent.'
while ($true) {
    Heartbeat 'idle' $null
    $next = Get-ChildItem -LiteralPath $requests -Filter '*.json' -File | Sort-Object LastWriteTime | Select-Object -First 1
    if ($next) {
        Write-Host ("[{0:HH:mm:ss}] {1}" -f (Get-Date), $next.Name)
        Run-Request $next
        Write-Host ("[{0:HH:mm:ss}] done" -f (Get-Date))
    } else {
        Start-Sleep -Seconds 5
    }
}
