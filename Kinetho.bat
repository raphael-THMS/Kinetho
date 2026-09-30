@echo off
setlocal
chcp 65001 >nul

set "LAUNCHER=%~dp0Point Annotator\Launch.bat"
if not exist "%LAUNCHER%" (
  echo Kinetho files could not be found.
  pause
  exit /b 1
)

call "%LAUNCHER%"
