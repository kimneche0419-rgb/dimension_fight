@echo off
setlocal

set MSYS2=C:\msys64\mingw64
set BUILD_DIR=C:\game_build

if not exist %BUILD_DIR% mkdir %BUILD_DIR%

cd /d %BUILD_DIR%

echo [1/2] Configuring CMake...
%MSYS2%\bin\cmake.exe ^
  -G "Ninja" ^
  -DCMAKE_C_COMPILER="%MSYS2%\bin\gcc.exe" ^
  -DCMAKE_CXX_COMPILER="%MSYS2%\bin\g++.exe" ^
  -DCMAKE_MAKE_PROGRAM="%MSYS2%\bin\ninja.exe" ^
  -DCMAKE_BUILD_TYPE=Debug ^
  "%~dp0."

if %ERRORLEVEL% neq 0 (
  echo CMake configure FAILED
  pause
  exit /b 1
)

echo [2/2] Building...
%MSYS2%\bin\ninja.exe -j4

if %ERRORLEVEL% neq 0 (
  echo Build FAILED
  pause
  exit /b 1
)

echo [3/3] Copying runtime DLL dependencies...
powershell -Command "$deps = %MSYS2%\bin\ldd.exe %BUILD_DIR%\DimensionFight.exe; foreach ($line in $deps) { if ($line -match '=> (/mingw64/bin/\S+\.dll)') { $dllName = $Matches[1].Replace('/mingw64/', '%MSYS2%\'); $dllName = $dllName.Replace('/', '\'); if (Test-Path $dllName) { Copy-Item -Path $dllName -Destination %BUILD_DIR% -Force } } }"

echo.
echo ===========================
echo Build SUCCESS!
echo Output: %BUILD_DIR%\DimensionFight.exe
echo ===========================
pause
