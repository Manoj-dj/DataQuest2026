#!/bin/bash
# Start the React frontend development server

cd "$(dirname "$0")/frontend"

echo "=== Starting Frontend Development Server ==="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠ node_modules not found. Installing dependencies..."
    npm install
fi

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "✗ ERROR: package.json not found in frontend directory"
    exit 1
fi

echo "Starting Vite dev server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the dev server
npm run dev
