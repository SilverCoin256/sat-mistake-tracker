#!/bin/bash
# Stops and removes the background folder-watcher LaunchAgent.
LABEL="com.satmistaketracker.watcher"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl unload "$PLIST" >/dev/null 2>&1 || true
rm -f "$PLIST"
echo "Watcher stopped and uninstalled."
