@echo off
title Dimension Fight Local 3-Servers
cd /d "%~dp0"

echo [1/3] Starting Auth Server on Port 9000...
start "Auth Server" cmd /k ".venv\Scripts\python.exe railway-auth/main.py"

timeout /t 1 /nobreak >nul

echo [2/3] Starting Matchmaking Server on Port 9001...
start "Matchmaking Server" cmd /k ".venv\Scripts\python.exe railway-match/main.py"

timeout /t 1 /nobreak >nul

echo [3/3] Starting Relay Server on Port 9002...
start "Relay Server" cmd /k ".venv\Scripts\python.exe railway-relay/main.py"

echo.
echo All 3 local servers started!
echo You can run run_game.bat now to test.
pause
