#!/bin/bash
# Run this from MSYS2 MinGW64 terminal:
#   bash /c/hangyang/dimension_fight_cpp/build_msys2.sh

set -e

MSYS2="/c/msys64/mingw64"
BUILD_DIR="/c/game_build"
SRC_DIR="$(dirname "$(readlink -f "$0")")"

echo "Source: $SRC_DIR"
echo "Build:  $BUILD_DIR"

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo "[1/2] Configuring CMake..."
cmake \
  -G "Ninja" \
  -DCMAKE_BUILD_TYPE=Debug \
  "$SRC_DIR"

echo "[2/2] Building..."
ninja -j4

echo ""
echo "==========================="
echo "Build SUCCESS!"
echo "Output: $BUILD_DIR/DimensionFight.exe"
echo "==========================="
