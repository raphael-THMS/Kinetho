@echo off
setlocal
chcp 65001 >nul

powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Setup.ps1"
if errorlevel 1 (
  echo.
  echo Kinetho setup could not start. Make sure Windows PowerShell is available.
  pause
)