#!/usr/bin/env python3
"""Accept a candidate from pending.json into the radar.

Usage:
  python3 accept-to-radar.py                    # interactive selection
  python3 accept-to-radar.py <owner/repo>       # direct pick
  python3 accept-to-radar.py --accepted         # process all accepted candidates

Workflow:
  1. Pick candidate from pending.json
  2. Run full quality analysis (Notable Stargazers, Bus Factor, etc.)
  3. Prompt for Ring, Quadrant, Description, Strengths, Weaknesses, Learned
  4. Insert into entries.json, update pending.json
"""

import json
import sys
import re
import importlib
from datetime import datetime, timezone

# Reuse analysis from update-radar.py (hyphen in filename requires importlib)
_update_radar = importlib.import_module('update-radar')
analyze_entry = _update_radar.analyze_entry
NOW = _update_radar.NOW

ENTRIES_PATH = 'docs/data/entries.json'
PENDING_PATH = 'candidates/pending.json'

QUADRANTS = [
    'AI Workflow & Orchestration',
    'Libraries & Frameworks',
    'Dev Tools & Infrastructure',
    'Patterns & Methods',
]

RINGS = ['Adopt', 'Trial', 'Scout', 'Hold']

CATEGORIES = ['radar', 'landscape']


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path}")


def make_id(name):
    """Generate entry ID from repo name: owner/repo -> repo (lowercase, hyphens)."""
    repo_name = name.split('/')[-1] if '/' in name else name
    return re.sub(r'[^a-z0-9-]', '-', repo_name.lower()).strip('-')


def pick_candidate(pending, target=None):
    """Find a candidate by name or interactively select one."""
    candidates = pending['candidates']

    if target:
        # Direct match by owner/repo or just repo name
        for c in candidates:
            if c['name'] == target or c['name'].endswith(f'/{target}'):
                return c
        print(f"  Kandidat '{target}' nicht in pending.json gefunden.")
        return None

    # Interactive: show accepted first, then pending
    accepted = [c for c in candidates if c['status'] == 'accepted']
    if accepted:
        print(f"\n  {len(accepted)} akzeptierte Kandidaten:")
        for i, c in enumerate(accepted):
            print(f"    [{i+1}] {c['name']:40} {c['stars']:>8} stars  {c.get('language', '?')}")
        print()
        choice = input("  Nummer waehlen (oder Enter fuer Liste aller pending): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(accepted):
            return accepted[int(choice) - 1]

    # Show top pending by stars
    pending_list = [c for c in candidates if c['status'] == 'pending']
    print(f"\n  {len(pending_list)} pending Kandidaten (Top 20 nach Stars):")
    top = sorted(pending_list, key=lambda c: c['stars'], reverse=True)[:20]
    for i, c in enumerate(top):
        print(f"    [{i+1}] {c['name']:40} {c['stars']:>8} stars  {c.get('language', '?')}")
    print()
    choice = input("  Nummer waehlen (oder 'owner/repo' eingeben): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(top):
        return top[int(choice) - 1]
    # Try as name
    return pick_candidate(pending, target=choice)


def prompt_choice(label, options, default=None):
    """Prompt user to pick from a list."""
    print(f"\n  {label}:")
    for i, opt in enumerate(options):
        marker = ' *' if opt == default else ''
        print(f"    [{i+1}] {opt}{marker}")
    while True:
        choice = input(f"  Waehlen [1-{len(options)}]: ").strip()
        if not choice and default:
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]


def prompt_text(label, default=''):
    """Prompt for free text input."""
    suffix = f" [{default}]" if default else ''
    value = input(f"  {label}{suffix}: ").strip()
    return value if value else default


def prompt_bool(label, default=False):
    """Prompt for yes/no."""
    hint = 'Y/n' if default else 'y/N'
    value = input(f"  {label} [{hint}]: ").strip().lower()
    if not value:
        return default
    return value in ('y', 'yes', 'ja', 'j')


def print_analysis(candidate, result):
    """Print analysis results for review."""
    s = result['signals']
    print(f"\n{'=' * 60}")
    print(f"  {candidate['name']}")
    print(f"  {candidate.get('description', '')[:80]}")
    print(f"{'=' * 60}")
    print(f"  Stars: {result['stars']:,}  |  Language: {candidate.get('language', '?')}  |  License: {candidate.get('license', '?')}")
    print(f"  Age: {result.get('age_months', '?')} months  |  Forks: {result.get('forks', 0):,}")
    print(f"\n  Quality Score: {result['quality_score']}/10")
    print(f"  ┌─────────────────────────────────────────┐")
    print(f"  │ Notable Density  {s['notable_density']:>4.1f}/10  (density={result['notable_density']:.2f})")
    print(f"  │ Bus Factor       {s['bus_factor']:>4.1f}/10  (BF={result['bus_factor']})")
    print(f"  │ Freshness        {s['freshness']:>4.1f}/10  ({result['days_since_commit']}d since commit)")
    print(f"  │ Issue Health     {s['issue_health']:>4.1f}/10  (ratio={result['issue_ratio']:.2f})")
    print(f"  │ Star Velocity    {s['star_velocity']:>4.1f}/10  ({result['stars']/max(result.get('age_months',1),1):.0f} stars/mo)")
    print(f"  └─────────────────────────────────────────┘")

    if result.get('notable_stargazers'):
        print(f"\n  Notable Stargazers:")
        for ns in result['notable_stargazers'][:5]:
            print(f"    - {ns['label']} ({ns['followers']:,} followers)")

    if result.get('top_contributors'):
        print(f"\n  Top Contributors:")
        for tc in result['top_contributors'][:3]:
            print(f"    - {tc['login']}: {tc['commits']} commits ({tc['pct']}%)")


def process_candidate(candidate, entries, pending):
    """Analyze one candidate and add to radar."""
    entry_id = make_id(candidate['name'])

    # Check for duplicate
    existing_ids = {e['id'] for e in entries}
    if entry_id in existing_ids:
        print(f"\n  '{entry_id}' existiert bereits in entries.json. Ueberspringe.")
        return False

    # Run analysis
    print(f"\n  Analysiere {candidate['name']}...", flush=True)
    result = analyze_entry({
        'url': candidate['url'],
        'name': candidate['name'],
    })

    if not result:
        print("  Analyse fehlgeschlagen (kein GitHub-Repo?).")
        return False

    print_analysis(candidate, result)

    # Prompt for metadata
    ring = prompt_choice("Ring", RINGS)
    quadrant = prompt_choice("Quadrant", QUADRANTS)
    category = prompt_choice("Category", CATEGORIES, default='radar')
    description = prompt_text("Beschreibung (DE)", candidate.get('description', ''))
    strengths = prompt_text("Staerken")
    weaknesses = prompt_text("Schwaechen")
    learned = prompt_text("Learnings / Was mitgenommen")
    tested = prompt_bool("Bereits getestet?")

    # Build entry
    today = NOW.strftime('%Y-%m-%d')
    entry = {
        'id': entry_id,
        'name': candidate['name'].split('/')[-1] if '/' in candidate['name'] else candidate['name'],
        'quadrant': quadrant,
        'ring': ring,
        'url': candidate['url'],
        'stars': result['stars'],
        'language': candidate.get('language', ''),
        'license': candidate.get('license', ''),
        'description': description,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'learned': learned,
        'added': today,
        'tested': tested,
        'category': category,
        # Analysis signals
        'notable_stargazers': result['notable_stargazers'],
        'notable_score': result['notable_score'],
        'notable_density': result['notable_density'],
        'notable_coverage_pct': result['notable_coverage_pct'],
        'bus_factor': result['bus_factor'],
        'top_contributors': result['top_contributors'],
        'days_since_commit': result['days_since_commit'],
        'issue_ratio': result['issue_ratio'],
        'open_issues': result['open_issues'],
        'closed_issues': result['closed_issues'],
        'forks': result['forks'],
        'age_months': result['age_months'],
        'signals': result['signals'],
        'quality_score': result['quality_score'],
        'last_updated': today,
        'score_history': [{
            'date': today,
            'score': result['quality_score'],
            'signals': result['signals'],
        }],
    }

    # Confirm
    print(f"\n  Neuer Eintrag:")
    print(f"    {entry['name']} | {ring} | {quadrant} | Q={result['quality_score']}/10")
    if not prompt_bool("Eintrag hinzufuegen?", default=True):
        print("  Abgebrochen.")
        return False

    # Add to entries.json
    entries.append(entry)
    save_json(ENTRIES_PATH, entries)

    # Update pending.json
    for c in pending['candidates']:
        if c['name'] == candidate['name']:
            c['status'] = 'accepted'
            break
    pending['total_accepted'] = sum(1 for c in pending['candidates'] if c['status'] == 'accepted')
    pending['total_pending'] = sum(1 for c in pending['candidates'] if c['status'] == 'pending')
    save_json(PENDING_PATH, pending)

    print(f"\n  {entry['name']} ins Radar aufgenommen.")
    return True


def main():
    entries = load_json(ENTRIES_PATH)
    pending = load_json(PENDING_PATH)

    # --accepted mode: process all accepted candidates
    if len(sys.argv) > 1 and sys.argv[1] == '--accepted':
        accepted = [c for c in pending['candidates'] if c['status'] == 'accepted']
        if not accepted:
            print("  Keine akzeptierten Kandidaten in pending.json.")
            return
        print(f"\n  {len(accepted)} akzeptierte Kandidaten werden verarbeitet...")
        for c in accepted:
            existing_ids = {e['id'] for e in entries}
            if make_id(c['name']) in existing_ids:
                print(f"  {c['name']} existiert bereits, ueberspringe.")
                continue
            process_candidate(c, entries, pending)
        return

    # Direct pick or interactive
    target = sys.argv[1] if len(sys.argv) > 1 else None
    candidate = pick_candidate(pending, target)
    if not candidate:
        return

    process_candidate(candidate, entries, pending)


if __name__ == '__main__':
    main()
