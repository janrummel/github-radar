#!/usr/bin/env python3
"""GitHub-Radar Quality Analysis.

Collects multiple signals per repo and computes a composite quality score.

Signals:
  1. Notable Density  — weighted notable stargazers / repo size
  2. Bus Factor        — how many devs account for 80% of commits
  3. Freshness         — days since last commit (lower = better)
  4. Issue Health      — ratio of closed issues to total
  5. Star Velocity     — stars per month since creation (organic growth indicator)

Composite Score: weighted average of all signals, normalized 0-10.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

NOTABLE_THRESHOLD = 500
PAGE_SIZE = 100  # GitHub GraphQL max per request

TIERS = [
    (10000, 8),
    (5000, 4),
    (1000, 2),
    (500, 1),
]

# Weights for composite score
WEIGHTS = {
    'notable_density': 0.25,
    'bus_factor': 0.25,
    'freshness': 0.20,
    'issue_health': 0.15,
    'star_velocity': 0.15,
}

NOW = datetime.now(timezone.utc)


def follower_weight(followers):
    for threshold, weight in TIERS:
        if followers >= threshold:
            return weight
    return 0


def get_repo_from_url(url):
    parsed = urlparse(url)
    if not parsed.hostname or 'github.com' not in parsed.hostname:
        return None
    parts = parsed.path.strip('/').split('/')
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None


def gh_graphql(query, **variables):
    args = ['gh', 'api', 'graphql', '-f', f'query={query}']
    for k, v in variables.items():
        if isinstance(v, int):
            args += ['-F', f'{k}={v}']
        else:
            args += ['-f', f'{k}={v}']
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def gh_rest(endpoint):
    result = subprocess.run(
        ['gh', 'api', endpoint],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# --- Signal 1: Notable Stargazers ---

def pages_for_stars(total_stars):
    """More pages for smaller repos to improve coverage.
    <5k: 5 pages/direction (up to 1000 sampled), <10k: 3, else: 1."""
    if total_stars < 5000:
        return 5
    if total_stars < 10000:
        return 3
    return 1


def get_notable_signal(owner, repo):
    notables = []
    score = 0
    total_stars = 0
    sampled = 0

    for direction in ["ASC", "DESC"]:
        cursor = None
        max_pages = 1  # default, updated after first response
        page = 0
        while page < max_pages:
            after_clause = f', after: "{cursor}"' if cursor else ''
            query = """
            query($owner: String!, $repo: String!, $first: Int!) {
              repository(owner: $owner, name: $repo) {
                stargazers(first: $first, orderBy: {field: STARRED_AT, direction: %s}%s) {
                  totalCount
                  pageInfo { hasNextPage endCursor }
                  nodes {
                    login
                    name
                    followers { totalCount }
                    company
                  }
                }
              }
            }
            """ % (direction, after_clause)
            data = gh_graphql(query, owner=owner, repo=repo, first=PAGE_SIZE)
            if not data or 'data' not in data:
                break
            repo_data = data['data'].get('repository')
            if not repo_data:
                break
            sg = repo_data['stargazers']
            total_stars = sg['totalCount']

            # After first page, decide how many pages per direction
            if page == 0:
                max_pages = pages_for_stars(total_stars)

            sampled += len(sg['nodes'])

            seen = {n['login'] for n in notables}
            for user in sg['nodes']:
                login = user['login']
                followers = user['followers']['totalCount']
                if login in seen or followers < NOTABLE_THRESHOLD:
                    continue
                seen.add(login)
                weight = follower_weight(followers)
                score += weight

                name = user.get('name') or ''
                company = user.get('company') or ''
                label = login
                if name:
                    label = f"{name} ({login})"
                if company:
                    label += f" @ {company}"
                notables.append({
                    'login': login,
                    'label': label,
                    'followers': followers,
                    'weight': weight
                })

            # Pagination
            page_info = sg.get('pageInfo', {})
            if not page_info.get('hasNextPage'):
                break
            cursor = page_info.get('endCursor')
            page += 1

    notables.sort(key=lambda x: x['followers'], reverse=True)
    density = round(score / max(total_stars / 1000, 0.1), 2)
    coverage = round(min(sampled, total_stars) / max(total_stars, 1) * 100, 1)

    return {
        'notables': notables[:10],
        'score': score,
        'density': density,
        'total_stars': total_stars,
        'coverage_pct': coverage,
    }


# --- Signal 2-5: Repo Metadata ---

def get_repo_signals(owner, repo):
    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        createdAt
        pushedAt
        issues(states: OPEN) { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
        forkCount
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 1) {
                nodes { committedDate }
              }
            }
          }
        }
      }
    }
    """
    data = gh_graphql(query, owner=owner, repo=repo)
    if not data or 'data' not in data:
        return {}
    r = data['data'].get('repository')
    if not r:
        return {}

    # Freshness: days since last commit
    last_commit = None
    try:
        last_commit_str = r['defaultBranchRef']['target']['history']['nodes'][0]['committedDate']
        last_commit = datetime.fromisoformat(last_commit_str.replace('Z', '+00:00'))
    except (KeyError, IndexError, TypeError):
        pass

    days_since_commit = (NOW - last_commit).days if last_commit else 999

    # Issue health
    open_issues = r['issues']['totalCount']
    closed_issues = r['closedIssues']['totalCount']
    total_issues = open_issues + closed_issues
    issue_ratio = round(closed_issues / total_issues, 2) if total_issues > 0 else 0

    # Repo age for velocity
    created = datetime.fromisoformat(r['createdAt'].replace('Z', '+00:00'))
    age_months = max((NOW - created).days / 30, 1)

    return {
        'days_since_commit': days_since_commit,
        'open_issues': open_issues,
        'closed_issues': closed_issues,
        'issue_ratio': issue_ratio,
        'age_months': round(age_months, 1),
        'forks': r['forkCount'],
    }


def get_bus_factor(owner, repo):
    """Get top contributors and calculate bus factor."""
    data = gh_rest(f'repos/{owner}/{repo}/contributors?per_page=20')
    if not data or not isinstance(data, list):
        return 1, []

    total_commits = sum(c.get('contributions', 0) for c in data)
    if total_commits == 0:
        return 1, []

    # Bus factor = how many devs to reach 80% of commits
    cumulative = 0
    bus_factor = 0
    top_contributors = []
    for c in data[:10]:
        contribs = c.get('contributions', 0)
        pct = round(contribs / total_commits * 100, 1)
        cumulative += contribs
        bus_factor += 1
        top_contributors.append({
            'login': c['login'],
            'commits': contribs,
            'pct': pct,
        })
        if cumulative >= total_commits * 0.8:
            break

    return bus_factor, top_contributors[:5]


# --- Normalize & Score ---

def normalize_notable_density(density):
    """0-10 scale. density >= 1.0 = 10, 0 = 0."""
    return min(density / 1.0 * 10, 10)


def normalize_bus_factor(bf):
    """Higher bus factor = better. 1 = risky (2/10), 5+ = great (10/10)."""
    mapping = {1: 2, 2: 5, 3: 7, 4: 8, 5: 9}
    if bf >= 6:
        return 10
    return mapping.get(bf, 2)


def normalize_freshness(days):
    """Recent = good. <7 days = 10, >365 = 0."""
    if days <= 7:
        return 10
    if days <= 30:
        return 8
    if days <= 90:
        return 6
    if days <= 180:
        return 4
    if days <= 365:
        return 2
    return 0


def normalize_issue_health(ratio, total_issues):
    """Higher close ratio = better. 0.8+ = 10, 0 = 0.
    Exception: repos with <5 total issues get neutral 5 (insufficient data)."""
    if total_issues < 5:
        return 5
    return min(ratio / 0.8 * 10, 10)


def normalize_star_velocity(stars, age_months):
    """Stars/month. Moderate = good, extreme = suspicious.
    Organic range: 50-500/month = great.
    >2000/month for young repos = potential red flag (capped at 6)."""
    velocity = stars / age_months
    if velocity < 10:
        return 3
    if velocity < 50:
        return 5
    if velocity < 200:
        return 8
    if velocity < 500:
        return 10
    if velocity < 2000:
        return 7  # fast but plausible
    return 4  # suspiciously fast


def compute_composite(signals):
    total = 0
    for key, weight in WEIGHTS.items():
        total += signals.get(key, 0) * weight
    return round(total, 1)


# --- Main ---

def analyze_entry(entry):
    parsed = get_repo_from_url(entry['url'])
    if not parsed:
        return None

    owner, repo = parsed

    # Collect all signals
    notable = get_notable_signal(owner, repo)
    meta = get_repo_signals(owner, repo)
    bus_factor, top_contribs = get_bus_factor(owner, repo)

    total_stars = notable['total_stars']
    age_months = meta.get('age_months', 1)

    # Normalize each signal to 0-10
    signals = {
        'notable_density': round(normalize_notable_density(notable['density']), 1),
        'bus_factor': round(normalize_bus_factor(bus_factor), 1),
        'freshness': round(normalize_freshness(meta.get('days_since_commit', 999)), 1),
        'issue_health': round(normalize_issue_health(meta.get('issue_ratio', 0), meta.get('open_issues', 0) + meta.get('closed_issues', 0)), 1),
        'star_velocity': round(normalize_star_velocity(total_stars, age_months), 1),
    }

    composite = compute_composite(signals)

    return {
        # Notable stargazers
        'notable_stargazers': notable['notables'],
        'notable_score': notable['score'],
        'notable_density': notable['density'],
        'notable_coverage_pct': notable['coverage_pct'],
        # Repo health
        'bus_factor': bus_factor,
        'top_contributors': top_contribs,
        'days_since_commit': meta.get('days_since_commit', None),
        'issue_ratio': meta.get('issue_ratio', 0),
        'open_issues': meta.get('open_issues', 0),
        'closed_issues': meta.get('closed_issues', 0),
        'forks': meta.get('forks', 0),
        'age_months': age_months,
        # Normalized signals (0-10 each)
        'signals': signals,
        # Composite quality score
        'quality_score': composite,
        'stars': total_stars,
    }


def push_changes(path):
    """Pull, commit, and push updated scores."""
    subprocess.run(["git", "pull", "--ff-only", "origin", "main"], check=True)
    subprocess.run(["git", "add", path], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode == 0:
        print("  No changes to commit.")
        return
    msg = f"scores: {NOW.strftime('%Y-%m-%d')} — update quality scores ({path})"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("  Pushed to origin/main.")


def main():
    do_push = "--push" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else 'docs/data/entries.json'

    with open(path) as f:
        entries = json.load(f)

    print("=" * 72)
    print("  GitHub-Radar Quality Analysis")
    print("=" * 72)

    for entry in entries:
        print(f"\n  {entry['name']}...", end=' ', flush=True)
        result = analyze_entry(entry)
        if not result:
            print("SKIP (kein GitHub-Repo)")
            continue

        # Update entry with all signals
        entry['notable_stargazers'] = result['notable_stargazers']
        entry['notable_score'] = result['notable_score']
        entry['notable_density'] = result['notable_density']
        entry['notable_coverage_pct'] = result['notable_coverage_pct']
        entry['bus_factor'] = result['bus_factor']
        entry['top_contributors'] = result['top_contributors']
        entry['days_since_commit'] = result['days_since_commit']
        entry['issue_ratio'] = result['issue_ratio']
        entry['open_issues'] = result['open_issues']
        entry['closed_issues'] = result['closed_issues']
        entry['forks'] = result['forks']
        entry['age_months'] = result['age_months']
        entry['signals'] = result['signals']
        entry['quality_score'] = result['quality_score']
        entry['stars'] = result['stars']
        entry['last_updated'] = NOW.strftime('%Y-%m-%d')

        # Score-Trend-Tracking: append to score_history (dedup per day)
        today = NOW.strftime('%Y-%m-%d')
        history = entry.get('score_history', [])
        data_point = {
            'date': today,
            'score': result['quality_score'],
            'signals': result['signals'],
        }
        # Replace existing entry for today, or append
        replaced = False
        for i, h in enumerate(history):
            if h.get('date') == today:
                history[i] = data_point
                replaced = True
                break
        if not replaced:
            history.append(data_point)
        entry['score_history'] = history

        s = result['signals']
        print(f"Q={result['quality_score']}/10")
        print(f"    Notable={s['notable_density']:.0f} Bus={s['bus_factor']:.0f} "
              f"Fresh={s['freshness']:.0f} Issues={s['issue_health']:.0f} "
              f"Velocity={s['star_velocity']:.0f}  |  "
              f"BF={result['bus_factor']} Days={result['days_since_commit']} "
              f"IR={result['issue_ratio']}")

    with open(path, 'w') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 72}")
    print(f"  Done. {path} updated.")

    # Summary sorted by quality
    print(f"\n  {'Repo':40} {'Score':>6}")
    print(f"  {'─' * 48}")
    ranked = sorted(entries, key=lambda e: e.get('quality_score', 0), reverse=True)
    for e in ranked:
        qs = e.get('quality_score', '-')
        print(f"  {e['name']:40} {qs:>6}")
    print("=" * 72)

    if do_push:
        print("\n  Pushing changes...")
        push_changes(path)


if __name__ == '__main__':
    main()
