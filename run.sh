#!/bin/bash
# Portable launcher: sets up a venv on first run, starts the server, opens the UI.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "First run: creating virtual environment..."
    python3 -m venv .venv
    ./.venv/bin/pip install --quiet --upgrade pip
    ./.venv/bin/pip install --quiet -r requirements.txt
fi

URL="http://127.0.0.1:5001/"
# wait for the server, then open the browser
( for i in $(seq 1 40); do
      if curl -s -o /dev/null "$URL"; then break; fi
      sleep 0.5
  done
  if [ -d "/Applications/Google Chrome.app" ]; then
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --app="$URL" >/dev/null 2>&1 &
  else
      python3 -m webbrowser "$URL" >/dev/null 2>&1 &
  fi ) &

exec ./.venv/bin/python app.py
