#!/usr/bin/env python3
"""GitHub-Radar Repo Discovery.

Searches GitHub for new repos matching configured topics and keywords.
Filters out already-tracked entries, writes candidates to candidates/pending.json.

Usage:
  python3 discover-repos.py                  # search and write candidates
  python3 discover-repos.py --push           # also commit and push to origin
  python3 discover-repos.py --dry-run        # print candidates, don't write
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---

TOPIC_SEARCHES = [
    "topic:claude-code",
    "topic:mcp",
    "topic:mcp-server",
    "topic:ai-agent",
    "topic:ai-agents",
    "topic:llm-tools",
    "topic:claude",
]

KEYWORD_SEARCHES = [
    "claude code skills",
    "mcp server framework",
    "ai agent orchestration",
    "claude agent sdk",
    "llm developer tools",
]

# Minimum stars to consider
MIN_STARS = 50

# Maximum results per query
PER_QUERY_LIMIT = 30

ENTRIES_PATH = Path(__file__).parent / "docs" / "data" / "entries.json"
CANDIDATES_DIR = Path(__file__).parent / "candidates"
CANDIDATES_PATH = CANDIDATES_DIR / "pending.json"

NOW = datetime.now(timezone.utc)


def gh_search(query, limit=PER_QUERY_LIMIT):
    """Search GitHub repos via gh CLI."""
    cmd = [
        "gh", "search", "repos", query,
        "--sort", "stars",
        "--order", "desc",
        "--limit", str(limit),
        "--json", "fullName,url,stargazersCount,description,language,license,updatedAt,createdAt",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARN: search failed for '{query}': {result.stderr.strip()}")
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def load_existing_urls():
    """Load URLs of already-tracked entries."""
    if not ENTRIES_PATH.exists():
        return set()
    with open(ENTRIES_PATH) as f:
        entries = json.load(f)
    return {e["url"].rstrip("/").lower() for e in entries}


def load_existing_candidates():
    """Load previously discovered candidates to avoid re-adding."""
    if not CANDIDATES_PATH.exists():
        return {}, set()
    with open(CANDIDATES_PATH) as f:
        data = json.load(f)
    candidates = data.get("candidates", [])
    urls = {c["url"].rstrip("/").lower() for c in candidates}
    return data, urls


def normalize_url(url):
    return url.rstrip("/").lower()


def discover():
    """Run all searches, return deduplicated candidates."""
    existing_urls = load_existing_urls()
    prev_data, prev_candidate_urls = load_existing_candidates()
    seen = set()
    raw_results = []

    # Topic searches
    for topic in TOPIC_SEARCHES:
        print(f"  Searching: {topic}...", end=" ", flush=True)
        results = gh_search(topic)
        print(f"{len(results)} results")
        raw_results.extend(results)

    # Keyword searches
    for kw in KEYWORD_SEARCHES:
        print(f"  Searching: \"{kw}\"...", end=" ", flush=True)
        results = gh_search(kw)
        print(f"{len(results)} results")
        raw_results.extend(results)

    # Deduplicate and filter
    candidates = []
    for repo in raw_results:
        url = normalize_url(repo.get("url", ""))
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)

        # Skip already tracked
        if url in existing_urls:
            continue

        # Skip already in candidates
        if url in prev_candidate_urls:
            continue

        stars = repo.get("stargazersCount", 0)
        if stars < MIN_STARS:
            continue

        license_info = repo.get("license", {})
        license_name = ""
        if isinstance(license_info, dict):
            license_name = license_info.get("key", "") or license_info.get("name", "")
        elif isinstance(license_info, str):
            license_name = license_info

        candidates.append({
            "name": repo.get("fullName", ""),
            "url": repo.get("url", ""),
            "stars": stars,
            "description": (repo.get("description") or "")[:200],
            "language": repo.get("language") or "Unknown",
            "license": license_name,
            "discovered": NOW.strftime("%Y-%m-%d"),
            "status": "pending",  # pending | accepted | rejected
        })

    # Sort by stars descending
    candidates.sort(key=lambda c: c["stars"], reverse=True)

    return candidates, prev_data


def write_candidates(new_candidates, prev_data):
    """Merge new candidates with existing and write."""
    CANDIDATES_DIR.mkdir(exist_ok=True)

    prev_candidates = prev_data.get("candidates", []) if prev_data else []
    merged = prev_candidates + new_candidates

    output = {
        "last_discovery": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_pending": len([c for c in merged if c["status"] == "pending"]),
        "total_accepted": len([c for c in merged if c["status"] == "accepted"]),
        "total_rejected": len([c for c in merged if c["status"] == "rejected"]),
        "candidates": merged,
    }

    with open(CANDIDATES_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return len(new_candidates), len(merged)


def push_changes():
    """Commit and push candidates."""
    subprocess.run(["git", "add", "candidates/pending.json"], check=True)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
    )
    if result.returncode == 0:
        print("  No changes to commit.")
        return

    msg = f"discovery: {NOW.strftime('%Y-%m-%d')} — new repo candidates"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("  Pushed to origin/main.")


def main():
    dry_run = "--dry-run" in sys.argv
    do_push = "--push" in sys.argv

    print("=" * 60)
    print("  GitHub-Radar Repo Discovery")
    print("=" * 60)

    candidates, prev_data = discover()

    if not candidates:
        print(f"\n  No new candidates found.")
        print("=" * 60)
        return

    print(f"\n  {'Name':45} {'Stars':>8}  Language")
    print(f"  {'─' * 70}")
    for c in candidates[:30]:  # Show top 30
        print(f"  {c['name']:45} {c['stars']:>8}  {c['language']}")

    if len(candidates) > 30:
        print(f"  ... and {len(candidates) - 30} more")

    print(f"\n  Total new candidates: {len(candidates)}")

    if dry_run:
        print("  (dry-run — not writing)")
    else:
        new_count, total = write_candidates(candidates, prev_data)
        print(f"  Written to {CANDIDATES_PATH} ({new_count} new, {total} total)")

        if do_push:
            push_changes()

    print("=" * 60)


if __name__ == "__main__":
    main()
