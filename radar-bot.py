#!/usr/bin/env python3
"""GitHub-Radar Telegram Control Bot.

Listens for Telegram commands to control the discovery system.
Runs as a long-polling daemon via LaunchAgent.

Commands:
  /radar_status    — Show current config and stats
  /radar_pause     — Pause discovery
  /radar_resume    — Resume discovery
  /radar_minstars <n>  — Set minimum stars threshold
  /radar_limit <n>     — Set per-query result limit
  /radar_schedule <days> — Set schedule days (e.g. mon,wed,fri)
  /radar_run       — Trigger immediate discovery run
  /radar_help      — Show available commands
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
CANDIDATES_PATH = Path(__file__).parent / "candidates" / "pending.json"
PLIST_NAME = "com.github-radar.discovery"

VALID_DAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
DAY_MAP = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 7}


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_token(cfg):
    token_file = cfg.get("telegram", {}).get("token_file", "")
    if not token_file:
        return None
    try:
        return Path(token_file).read_text().strip()
    except (FileNotFoundError, PermissionError):
        return None


def get_chat_id(cfg):
    return str(cfg.get("telegram", {}).get("chat_id", ""))


def tg_request(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data)
    else:
        req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=35)
        return json.loads(resp.read())
    except Exception as e:
        print(f"  TG error: {e}", flush=True)
        return None


def send_reply(token, chat_id, text):
    tg_request(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    })


def get_candidate_stats():
    if not CANDIDATES_PATH.exists():
        return {"pending": 0, "accepted": 0, "rejected": 0, "total": 0, "last": "-"}
    with open(CANDIDATES_PATH) as f:
        data = json.load(f)
    return {
        "pending": data.get("total_pending", 0),
        "accepted": data.get("total_accepted", 0),
        "rejected": data.get("total_rejected", 0),
        "total": len(data.get("candidates", [])),
        "last": data.get("last_discovery", "-"),
    }


def update_launchagent_schedule(cfg):
    """Rewrite plist with new schedule and reload."""
    days = cfg.get("schedule_days", ["mon", "thu"])
    hour = cfg.get("schedule_hour", 7)

    intervals = ""
    for day in days:
        weekday = DAY_MAP.get(day, 1)
        intervals += f"""        <dict>
            <key>Weekday</key>
            <integer>{weekday}</integer>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
"""

    home = Path.home()
    repo_dir = Path(__file__).parent
    log_dir = home / "Library" / "Logs" / "github-radar"
    plist_path = home / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>discover-repos.py</string>
        <string>--push</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{repo_dir}</string>
    <key>StartCalendarInterval</key>
    <array>
{intervals}    </array>
    <key>StandardOutPath</key>
    <string>{log_dir}/discovery.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/discovery-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>"""

    plist_path.write_text(plist)

    uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{PLIST_NAME}"],
                    capture_output=True)
    subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
                    capture_output=True)


def handle_command(token, chat_id, text):
    """Process a command and send reply."""
    cfg = load_config()
    parts = text.strip().split()
    cmd = parts[0].lower().split("@")[0]  # strip @botname
    args = parts[1:]

    if cmd == "/radar_status":
        stats = get_candidate_stats()
        days = ", ".join(cfg.get("schedule_days", ["mon", "thu"]))
        status = "AKTIV" if cfg.get("enabled", True) else "PAUSIERT"
        msg = (
            f"*GitHub-Radar Status*\n\n"
            f"Status: {status}\n"
            f"Schedule: {days} um {cfg.get('schedule_hour', 7)}:00\n"
            f"Min Stars: {cfg.get('min_stars', 50)}\n"
            f"Results/Query: {cfg.get('per_query_limit', 30)}\n\n"
            f"Kandidaten: {stats['total']} total\n"
            f"  Pending: {stats['pending']}\n"
            f"  Accepted: {stats['accepted']}\n"
            f"  Rejected: {stats['rejected']}\n"
            f"Letzter Lauf: {stats['last']}"
        )
        send_reply(token, chat_id, msg)

    elif cmd == "/radar_pause":
        cfg["enabled"] = False
        save_config(cfg)
        send_reply(token, chat_id, "Discovery *pausiert*. `/radar_resume` zum Fortsetzen.")

    elif cmd == "/radar_resume":
        cfg["enabled"] = True
        save_config(cfg)
        send_reply(token, chat_id, "Discovery *wieder aktiv*.")

    elif cmd == "/radar_minstars":
        if not args or not args[0].isdigit():
            send_reply(token, chat_id, "Usage: `/radar_minstars 100`")
            return
        val = int(args[0])
        cfg["min_stars"] = val
        save_config(cfg)
        send_reply(token, chat_id, f"Min Stars auf *{val}* gesetzt.")

    elif cmd == "/radar_limit":
        if not args or not args[0].isdigit():
            send_reply(token, chat_id, "Usage: `/radar_limit 20`")
            return
        val = min(int(args[0]), 100)
        cfg["per_query_limit"] = val
        save_config(cfg)
        send_reply(token, chat_id, f"Results pro Query auf *{val}* gesetzt.")

    elif cmd == "/radar_schedule":
        if not args:
            send_reply(token, chat_id, "Usage: `/radar_schedule mon,wed,fri`")
            return
        days = [d.strip().lower() for d in args[0].split(",")]
        invalid = [d for d in days if d not in VALID_DAYS]
        if invalid:
            send_reply(token, chat_id, f"Unbekannte Tage: {', '.join(invalid)}\nErlaubt: mon,tue,wed,thu,fri,sat,sun")
            return
        cfg["schedule_days"] = days
        save_config(cfg)
        update_launchagent_schedule(cfg)
        send_reply(token, chat_id, f"Schedule auf *{', '.join(days)}* um {cfg.get('schedule_hour', 7)}:00 gesetzt.")

    elif cmd == "/radar_run":
        send_reply(token, chat_id, "Starte Discovery (kann 2-3 Min dauern)...")
        repo_dir = Path(__file__).parent
        try:
            result = subprocess.run(
                ["python3", "discover-repos.py", "--push"],
                cwd=repo_dir,
                capture_output=True, text=True, timeout=600,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "unbekannter Fehler")[-400:]
                send_reply(token, chat_id, f"Discovery fehlgeschlagen:\n```\n{err}\n```")
            elif "No new candidates" in result.stdout:
                send_reply(token, chat_id, "Keine neuen Kandidaten gefunden.")
        except subprocess.TimeoutExpired:
            send_reply(token, chat_id, "Discovery Timeout (>10 Min). Prüfe Logs.")

    elif cmd == "/radar_help":
        msg = (
            "*GitHub-Radar Commands*\n\n"
            "`/radar_status` — Config & Stats\n"
            "`/radar_pause` — Discovery pausieren\n"
            "`/radar_resume` — Discovery fortsetzen\n"
            "`/radar_minstars 100` — Min Stars\n"
            "`/radar_limit 20` — Results pro Query\n"
            "`/radar_schedule mon,wed,fri` — Tage\n"
            "`/radar_run` — Sofort ausfuehren\n"
            "`/radar_help` — Diese Hilfe"
        )
        send_reply(token, chat_id, msg)

    else:
        # Unknown command — ignore (don't reply to non-radar commands)
        pass


def main():
    cfg = load_config()
    token = get_token(cfg)
    allowed_chat_id = get_chat_id(cfg)

    if not token:
        print("ERROR: No Telegram token found. Check config.json telegram.token_file")
        sys.exit(1)

    print(f"GitHub-Radar Bot started. Listening for /radar_* commands...", flush=True)

    offset = 0
    while True:
        try:
            result = tg_request(token, "getUpdates", {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": "message",
            })

            if not result or not result.get("ok"):
                time.sleep(5)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = str(msg.get("chat", {}).get("id", ""))

                # Only respond to allowed chat
                if allowed_chat_id and chat_id != allowed_chat_id:
                    continue

                # Only process /radar_* commands
                if text.startswith("/radar_"):
                    print(f"  CMD: {text} from {chat_id}", flush=True)
                    handle_command(token, chat_id, text)

        except KeyboardInterrupt:
            print("\nShutting down.")
            break
        except Exception as e:
            print(f"  Error: {e}", flush=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
