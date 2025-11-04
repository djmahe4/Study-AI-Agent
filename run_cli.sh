#!/bin/bash
# Startup script for AI Learning Engine CLI

echo "🧠 AI Learning Engine - CLI Mode"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import pydantic" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Python CLI ready!"
echo ""
echo "Example commands:"
echo "  python cli.py help"
echo "  python cli.py list-topics"
echo "  python cli.py load-syllabus data/syllabus/example.json"
echo ""
echo "Run 'python cli.py --help' for more options"
