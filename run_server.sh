#!/bin/bash
echo "Activating virtual environment..."
# Detect OS (Windows Git Bash vs Unix/Mac)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  # For Git Bash on Windows
  source venv/Scripts/activate
else
  # For Mac/Linux
  source venv/bin/activate
fi

# Check if activation worked
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo "❌ Failed to activate virtual environment. Is it created?"
  exit 1
fi

echo "✅ Virtual environment activated."
echo "🚀 Starting FastAPI Server..."

uvicorn main:app --reload --host 127.0.0.1 --port 8000
