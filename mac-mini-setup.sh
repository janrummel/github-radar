#!/bin/bash
# Setup script for GitHub-Radar discovery on Mac Mini Agent.
#
# Run this ON the Mac Mini via SSH:
#   ssh macmini-agent 'bash -s' < mac-mini-setup.sh
#
# Prerequisites: gh CLI authenticated, git configured.

set -euo pipefail

REPO_DIR="$HOME/github-radar"
PLIST_NAME="com.github-radar.discovery"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_DIR="$HOME/Library/Logs/github-radar"

echo "=== GitHub-Radar Discovery Setup ==="

# 1. Clone or pull repo
if [ -d "$REPO_DIR" ]; then
  echo "  Repo exists, pulling latest..."
  cd "$REPO_DIR" && git pull --ff-only
else
  echo "  Cloning repo..."
  gh repo clone janrummel/github-radar "$REPO_DIR"
fi

# 2. Verify gh CLI works
echo "  Verifying gh CLI..."
gh auth status 2>&1 | head -3

# 3. Create log directory
mkdir -p "$LOG_DIR"

# 4. Install LaunchAgent (runs Mon + Thu at 07:00)
cat > "$PLIST_PATH" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.github-radar.discovery</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>discover-repos.py</string>
        <string>--push</string>
    </array>
    <key>WorkingDirectory</key>
    <string>REPO_DIR_PLACEHOLDER</string>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Weekday</key>
            <integer>1</integer>
            <key>Hour</key>
            <integer>7</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Weekday</key>
            <integer>4</integer>
            <key>Hour</key>
            <integer>7</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    <key>StandardOutPath</key>
    <string>LOG_DIR_PLACEHOLDER/discovery.log</string>
    <key>StandardErrorPath</key>
    <string>LOG_DIR_PLACEHOLDER/discovery-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
PLIST

# Replace placeholders with actual paths
sed -i '' "s|REPO_DIR_PLACEHOLDER|${REPO_DIR}|g" "$PLIST_PATH"
sed -i '' "s|LOG_DIR_PLACEHOLDER|${LOG_DIR}|g" "$PLIST_PATH"

# 5. Load the agent
launchctl bootout "gui/$(id -u)/${PLIST_NAME}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

echo ""
echo "=== Setup complete ==="
echo "  Repo:      $REPO_DIR"
echo "  Schedule:  Mon + Thu at 07:00"
echo "  Logs:      $LOG_DIR/"
echo "  Plist:     $PLIST_PATH"
echo ""
echo "  Manual run:  cd $REPO_DIR && python3 discover-repos.py --push"
echo "  Check logs:  tail -50 $LOG_DIR/discovery.log"
echo "  Disable:     launchctl bootout gui/$(id -u)/${PLIST_NAME}"
