@echo off
setlocal

set "PATH=C:\msys64\mingw64\bin;C:\msys64\usr\bin;%PATH%"

if not exist C:\game_build mkdir C:\game_build
cd /d C:\game_build

echo [1/2] CMake configure...
cmake.exe ^
  -G "Ninja" ^
  -DCMAKE_C_COMPILER="gcc.exe" ^
  -DCMAKE_CXX_COMPILER="g++.exe" ^
  -DCMAKE_MAKE_PROGRAM="ninja.exe" ^
  -DCMAKE_BUILD_TYPE=Debug ^
  "%~dp0."

if %ERRORLEVEL% neq 0 (
  echo CONFIGURE FAILED
  pause
  exit /b 1
)

echo [2/2] Building...
ninja.exe -j4

if %ERRORLEVEL% neq 0 (
  echo BUILD FAILED
  pause
  exit /b 1
)

echo [3/3] Copying runtime DLL dependencies...
powershell -Command "$deps = ldd.exe C:\game_build\DimensionFight.exe; foreach ($line in $deps) { if ($line -match '=> (/mingw64/bin/\S+\.dll)') { $dllName = $Matches[1].Replace('/mingw64/', 'C:\msys64\mingw64\'); $dllName = $dllName.Replace('/', '\'); if (Test-Path $dllName) { Copy-Item -Path $dllName -Destination C:\game_build -Force } } }"

echo.
echo BUILD SUCCESS: C:\game_build\DimensionFight.exe
pause
