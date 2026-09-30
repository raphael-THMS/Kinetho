@echo off
setlocal
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -STA -ExecutionPolicy Bypass -File "%~dp0Install Kinetho.ps1"
exit /b 0
