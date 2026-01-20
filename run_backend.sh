#!/bin/bash
# Run the backend server with correct Python path

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Check if uv is available and use it, otherwise use python3 directly
if command -v uv &> /dev/null; then
    echo "Running with uv..."
    uv run python3 src/main.py
else
    echo "Running with python3..."
    python3 src/main.py
fi
