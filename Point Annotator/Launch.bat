@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "PYTHONW=%SCRIPT_DIR%.venv\Scripts\pythonw.exe"
set "VENV_CONFIG=%SCRIPT_DIR%.venv\pyvenv.cfg"
set "VENV_BASE="

if exist "%VENV_CONFIG%" (
  for /f "tokens=2,* delims==" %%A in ('findstr /I /B /C:"home =" "%VENV_CONFIG%"') do (
    for /f "tokens=*" %%C in ("%%A") do set "VENV_BASE=%%C"
  )
)

if not defined VENV_BASE goto :setup_environment
if not exist "%VENV_BASE%\python.exe" goto :setup_environment
if not exist "%PYTHONW%" goto :setup_environment
goto :launch_application

:setup_environment
  echo The application environment is not installed yet.
  echo.
  echo Run Setup.bat in this folder first.
  call "%SCRIPT_DIR%Setup.bat"
  if errorlevel 1 exit /b 1
  if not exist "%PYTHONW%" exit /b 1

:launch_application
start "Kinetho" "%PYTHONW%" "%SCRIPT_DIR%studio.py"
