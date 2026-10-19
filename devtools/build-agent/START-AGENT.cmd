@echo off
rem Starts the supervised Caustica build agent by hand. It does not start with Windows.
start "Caustica build agent" /min cmd /c ""%~dp0supervisor.cmd""
echo The build agent is running in a minimized window. Run this file again after each Windows sign-in.
timeout /t 5 >nul
