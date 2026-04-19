@echo off
REM SCYTcheck Application Launcher
REM This batch file ensures Scoop tools are configured

setlocal enabledelayedexpansion

REM Add Scoop shims to PATH
set PATH=C:\Users\SteSt\scoop\shims;!PATH!

REM Change to project directory
cd /d "C:\Users\SteSt\source\SCYTcheck"

REM Start the application
echo Starting SCYTcheck...
.venv\Scripts\python.exe -m src.main

pause
