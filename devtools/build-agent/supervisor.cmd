@echo off
rem Keeps the Caustica build agent running. Exit code 0 means stop (for example, another agent
rem is already running); 3 means reload now; anything else restarts after five seconds.
title Caustica build agent
set CAUSTICA_AGENT_SUPERVISED=1
:loop
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0agent.ps1"
set code=%errorlevel%
if "%code%"=="0" goto end
if "%code%"=="3" goto loop
echo Agent exited with code %code%; restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
:end
