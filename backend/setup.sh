#!/usr/bin/env bash
# FixCampus backend setup — macOS / Linux
# Run this from inside the backend/ folder:
#   bash setup.sh
set -e

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

echo ""
echo "Setup complete. Starting the server on http://localhost:8000 ..."
echo "Press Ctrl+C to stop. Leave this terminal open while you use the app."
echo ""
uvicorn app.main:app --reload --port 8000
