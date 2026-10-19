<# Adds or removes the per-user sign-in entry that starts the build agent's supervisor. No administrator rights are needed. #>
param([switch]$Remove)
$ErrorActionPreference = 'Stop'
$entry = Join-Path ([Environment]::GetFolderPath('Startup')) 'Caustica Enhanced build agent.cmd'
if ($Remove) {
    if (Test-Path -LiteralPath $entry) { Remove-Item -LiteralPath $entry -Force; Write-Host 'Autostart removed.' }
    else { Write-Host 'Autostart was not installed.' }
    exit 0
}
$supervisor = Join-Path $PSScriptRoot 'supervisor.cmd'
$content = "@echo off`r`nstart `"Caustica build agent`" /min cmd /c `"`"$supervisor`"`"`r`n"
[IO.File]::WriteAllText($entry, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Autostart installed: $entry"
