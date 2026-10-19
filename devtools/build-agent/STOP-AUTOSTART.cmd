@echo off
rem Removes the sign-in autostart entry. A running agent keeps running until its window is closed.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Remove
pause
