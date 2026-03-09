#!/bin/bash
# Setup script for GitHub-Radar discovery on Mac Mini Agent.
#
# Run this ON the Mac Mini via SSH:
#   ssh macmini-agent 'bash -s' < mac-mini-setup.sh
#
# Prerequisites: gh CLI authenticated, git configured.

set -euo pipefail

REPO_DIR="$HOME/github-radar"
LOG_DIR="$HOME/Library/Logs/github-radar"

DISCOVERY_PLIST_NAME="com.github-radar.discovery"
DISCOVERY_PLIST_PATH="$HOME/Library/LaunchAgents/${DISCOVERY_PLIST_NAME}.plist"

SCORES_PLIST_NAME="com.github-radar.scores"
SCORES_PLIST_PATH="$HOME/Library/LaunchAgents/${SCORES_PLIST_NAME}.plist"

echo "=== GitHub-Radar Setup ==="

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

# 4a. Install Discovery LaunchAgent (Mon + Thu at 07:00)
echo "  Installing discovery agent (Mon+Thu 07:00)..."
cat > "$DISCOVERY_PLIST_PATH" << 'PLIST'
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

# Replace placeholders
sed -i '' "s|REPO_DIR_PLACEHOLDER|${REPO_DIR}|g" "$DISCOVERY_PLIST_PATH"
sed -i '' "s|LOG_DIR_PLACEHOLDER|${LOG_DIR}|g" "$DISCOVERY_PLIST_PATH"

# 4b. Install Score-Update LaunchAgent (Sun at 08:00)
echo "  Installing score-update agent (Sun 08:00)..."
cat > "$SCORES_PLIST_PATH" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.github-radar.scores</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>update-radar.py</string>
        <string>--push</string>
    </array>
    <key>WorkingDirectory</key>
    <string>REPO_DIR_PLACEHOLDER</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>LOG_DIR_PLACEHOLDER/scores.log</string>
    <key>StandardErrorPath</key>
    <string>LOG_DIR_PLACEHOLDER/scores-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
PLIST

sed -i '' "s|REPO_DIR_PLACEHOLDER|${REPO_DIR}|g" "$SCORES_PLIST_PATH"
sed -i '' "s|LOG_DIR_PLACEHOLDER|${LOG_DIR}|g" "$SCORES_PLIST_PATH"

# 5. Load both agents
launchctl bootout "gui/$(id -u)/${DISCOVERY_PLIST_NAME}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$DISCOVERY_PLIST_PATH"

launchctl bootout "gui/$(id -u)/${SCORES_PLIST_NAME}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$SCORES_PLIST_PATH"

echo ""
echo "=== Setup complete ==="
echo "  Repo:      $REPO_DIR"
echo "  Logs:      $LOG_DIR/"
echo ""
echo "  Discovery:     Mon + Thu at 07:00"
echo "  Score Update:  Sun at 08:00"
echo ""
echo "  Manual discovery:  cd $REPO_DIR && python3 discover-repos.py --push"
echo "  Manual scores:     cd $REPO_DIR && python3 update-radar.py --push"
echo "  Check logs:        tail -50 $LOG_DIR/scores.log"
echo "  Disable discovery: launchctl bootout gui/\$(id -u)/${DISCOVERY_PLIST_NAME}"
echo "  Disable scores:    launchctl bootout gui/\$(id -u)/${SCORES_PLIST_NAME}"
