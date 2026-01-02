#!/bin/bash
# Startup script for React Terminal CLI

echo "🧠 AI Learning Engine - React Terminal CLI"
echo "==========================================="
echo ""

cd frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "✅ Starting React Terminal CLI..."
echo "🌐 Open http://localhost:3000 in your browser"
echo ""

npm run dev
