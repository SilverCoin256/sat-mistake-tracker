#!/bin/bash

# SAT Mistake Tracker launcher
# Starts the local Flask server (if not already up), waits until it actually
# responds, then opens the UI in a chromeless Chrome window.

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$APP_DIR/.venv/bin/python"
URL="http://127.0.0.1:5001/"
LOG="$APP_DIR/launch.log"
PROFILE_DIR="$APP_DIR/.chrome-app-profile"

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
    # --user-data-dir is what makes this reliable. Without it, a Chrome that is
    # already running claims the command line ("Opening in existing browser
    # session") and DROPS --app=, so the tracker silently becomes one more tab
    # in the user's main window instead of its own chromeless window. A private
    # profile means we always get our own instance, so --app= is always honored,
    # and a repeat launch focuses the tracker window that instance already owns.
    "$CHROME" --app="$URL" \
        --user-data-dir="$PROFILE_DIR" \
        --no-first-run --no-default-browser-check \
        >/dev/null 2>&1 &
    CHROME_PID=$!
    # A process spawned from a background shell does not take focus on its own,
    # so the window can open behind whatever the user was looking at.
    sleep 2
    osascript -e "tell application \"System Events\" to set frontmost of (first process whose unix id is $CHROME_PID) to true" \
        >/dev/null 2>&1 || true
else
    echo "Chrome not found; opening default browser." >> "$LOG"
    open "$URL"
fi
