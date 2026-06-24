@echo off
title Dimension Fight Multiplayer Runner
echo =========================================
echo  Dimension Fight: Server & Client Runner
echo =========================================

cd /d "%~dp0"

echo [1/2] Launching Client 1 (Player 1)...
start "Dimension Fight - Client 1" "dimension_fight_cpp\build\DimensionFight.exe"

echo [2/2] Launching Client 2 (Player 2)...
start "Dimension Fight - Client 2" "dimension_fight_cpp\build2\DimensionFight.exe"

echo.
echo All clients launched! They will connect to the live Railway cloud server.
echo Enter 'M' in-game to access the multiplayer lobby.
echo.
pause
