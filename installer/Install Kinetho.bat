@echo off
setlocal
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -STA -ExecutionPolicy Bypass -File "%~dp0setup\Install Kinetho.ps1"
exit /b 0
