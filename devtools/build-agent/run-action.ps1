<#
  Runs one agent action and streams every output line, timestamped, to a log file that can be
  read while the action runs. Started only by agent.ps1 with a script it chose from its whitelist.
#>
param(
    [Parameter(Mandatory)][string]$Script,
    [Parameter(Mandatory)][string]$Log,
    [string]$Parameters = '',   # base64 UTF-8 JSON object of named parameters
    [switch]$Environment,       # load toolchain/env.ps1 first (native tests)
    [switch]$Lock               # hold the workspace build lock for the whole action
)
$ErrorActionPreference = 'Continue'
$workspace = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
function Line([string]$text) {
    foreach ($part in ($text -split "`r?`n")) {
        Add-Content -LiteralPath $Log -Value ('{0:HH:mm:ss} {1}' -f (Get-Date), $part) -Encoding UTF8
    }
}
$named = @{}
if ($Parameters) {
    $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Parameters))
    $object = $json | ConvertFrom-Json
    foreach ($property in $object.PSObject.Properties) { $named[$property.Name] = $property.Value }
}
if ($Lock) {
    $buildLock = New-Object System.Threading.Mutex($false, 'Local\CausticaEnhancedBuildLock')
    $owned = $false
    try { $owned = $buildLock.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { Line 'Another workspace build holds the build lock; not starting.'; exit 75 }
}
if ($Environment) { . (Join-Path $workspace 'toolchain\env.ps1') }
Line "Running $Script"
$code = 0
try {
    & $Script @named *>&1 | ForEach-Object { Line (($_ | Out-String).TrimEnd()) }
    if ($LASTEXITCODE) { $code = $LASTEXITCODE }
} catch {
    Line "ERROR: $_"
    $code = 1
}
Line "Exit code $code"
exit $code
