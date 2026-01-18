#!/bin/bash
# Run the backend server with correct Python path

cd /home/csd07/DataQuest2026
export PYTHONPATH="/home/csd07/DataQuest2026:$PYTHONPATH"

# Check if uv is available and use it, otherwise use python3 directly
if command -v uv &> /dev/null; then
    echo "Running with uv..."
    uv run python3 src/main.py
else
    echo "Running with python3..."
    python3 src/main.py
fi
