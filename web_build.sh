#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create build directory if not exists
mkdir -p build

# Run pygbag to build the web version
# This will generate a build/web folder
python3 -m pygbag --build .

echo "Build complete. Output in build/web"
echo "To run the server, use: python3 server.py"
