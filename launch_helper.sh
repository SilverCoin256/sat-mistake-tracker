#!/bin/bash

# SAT Mistake Tracker launcher
# Starts the local Flask server (if not already up), waits until it actually
# responds, then opens the UI in a chromeless Chrome window.

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$APP_DIR/.venv/bin/python"
URL="http://127.0.0.1:5001/"
LOG="$APP_DIR/launch.log"

cd "$APP_DIR" || exit 1

echo "----- launch $(date) -----" >> "$LOG"

if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Server already running on port 5001." >> "$LOG"
else
    echo "Starting Flask server..." >> "$LOG"
    nohup "$PY" "$APP_DIR/app.py" >> "$LOG" 2>&1 &
fi

for i in $(seq 1 40); do
    if curl -s -o /dev/null "$URL" ; then
        echo "Server responded after ${i} tries." >> "$LOG"
        break
    fi
    sleep 0.5
done

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ -x "$CHROME" ]; then
    echo "Opening Chrome app window..." >> "$LOG"
    "$CHROME" --app="$URL" >/dev/null 2>&1 &
else
    echo "Chrome not found; opening default browser." >> "$LOG"
    open "$URL"
fi
