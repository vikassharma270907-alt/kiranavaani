#!/usr/bin/env bash
# ==============================================================================
# KiranaVaani Build Script for Render Native Python Runtime
# ==============================================================================
set -o errexit

echo "=================================================="
echo "Starting KiranaVaani Build on Render"
echo "=================================================="

# 1. Install Python Backend Dependencies
echo "--> Installing Python backend requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Build Vite/React Frontend Cockpit
echo "--> Building Frontend Cockpit..."
if command -v npm &> /dev/null; then
    echo "Found npm $(npm -v), compiling frontend assets..."
    cd frontend
    npm install
    npm run build
    cd ..
    echo "Frontend build successfully generated in frontend/dist"
else
    echo "npm not detected in native runtime. If frontend/dist is needed,"
    echo "deploy with Docker (runtime: docker) or pre-build frontend assets."
fi

echo "=================================================="
echo "KiranaVaani Build Finished!"
echo "=================================================="
