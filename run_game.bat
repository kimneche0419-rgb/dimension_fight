@echo off
title Dimension Fight Multiplayer Runner
echo =========================================
echo  Dimension Fight: Server & Client Runner
echo =========================================

cd /d "%~dp0"

echo [1/3] Killing any existing proxy processes...
taskkill /F /IM local_proxy.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/3] Starting Local TCP-to-WebSocket Proxy...
start "Local Proxy Server" cmd /k "local_proxy.exe"

timeout /t 2 /nobreak >nul

echo [2/3] Copying latest build...
copy /Y "C:\game_build\DimensionFight.exe" "dimension_fight_cpp\build\DimensionFight.exe" >nul 2>&1
copy /Y "C:\game_build\DimensionFight.exe" "dimension_fight_cpp\build2\DimensionFight.exe" >nul 2>&1

echo [3/3] Launching Client 1 (Player 1)...
start "Dimension Fight - Client 1" "dimension_fight_cpp\build\DimensionFight.exe"

echo [4/4] Launching Client 2 (Player 2)...
start "Dimension Fight - Client 2" "dimension_fight_cpp\build2\DimensionFight.exe"

echo.
echo All components launched! They will connect to the live Render WebSocket server via the local proxy.
echo Enter 'M' in-game to access the multiplayer lobby.
echo.
pause

