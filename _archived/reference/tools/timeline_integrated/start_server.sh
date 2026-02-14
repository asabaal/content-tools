#!/bin/bash

# HTTP Server Launcher for Integrated Components Testing
# This script starts a local HTTP server to avoid CORS issues with ES6 modules

# Change to the correct directory first
cd "$(dirname "$0")"

echo "🚀 Starting HTTP Server for Integrated Components Testing..."
echo "📍 Directory: $(pwd)"
echo "🌐 Server will be available at: http://localhost:8080"
echo ""
echo "📋 Available test pages:"
echo "   • http://localhost:8080/comprehensive_test.html"
echo "   • http://localhost:8080/data_test.html"
echo "   • http://localhost:8080/import_test.html"
echo "   • http://localhost:8080/TimelineViewer/TimelineViewer.test.html"
echo "   • http://localhost:8080/InteractiveBoundaries/InteractiveBoundaries.test.html"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Kill any existing servers on port 8080
pkill -f "python3 -m http.server.*8080" 2>/dev/null

# Change to the correct directory
cd "$(dirname "$0")"

# Start the server
python3 -m http.server 8080