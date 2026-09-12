#!/bin/bash
# Installs folder_watcher.py as a LaunchAgent: it runs in the background at
# all times (survives reboot/logout, restarts itself if it crashes), so
# dropping a screenshot into ~/Downloads/SAT Screenshots gets it saved even
# with the app/browser closed.
set -e
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$APP_DIR/.venv/bin/python"
LABEL="com.satmistaketracker.watcher"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ ! -x "$PY" ]; then
    echo "No venv found at $PY — run ./run.sh once first to set it up." >&2
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Downloads/SAT Screenshots"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>-u</string>
        <string>$APP_DIR/folder_watcher.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$APP_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$APP_DIR/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>$APP_DIR/watcher.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "Watcher installed and running in the background."
echo "Drop screenshots/PDFs into: $HOME/Downloads/SAT Screenshots"
echo "Logs: $APP_DIR/watcher.log"
echo "To stop permanently: ./uninstall_watcher.sh"
