# GitHub-Radar

> Persoenlicher Technologie-Radar fuer das Dev-Universum rund um Claude Code & AI Agents.
> Kein Link-Dump — getestete Bewertungen aus Anwender-Perspektive.

**[Website oeffnen](https://janrummel.github.io/github-radar/)** · 59 Eintraege · 4 Quadranten · Quality Score 0–10

---

## Schnellstart

```bash
# Lokal
cd docs && python3 -m http.server 8090
open http://localhost:8090

# Oder online
open https://janrummel.github.io/github-radar/
```

## Was ist das?

Inspiriert vom [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar) — aber persoenlich, fuer GitHub Repos und Developer Tools im AI-Agent-Oekosystem.

Jeder Eintrag wird mit einem **Composite Quality Score** bewertet, der 5 unabhaengige Signale kombiniert:

| Signal | Gewicht | Was es misst |
|--------|---------|-------------|
| Notable Density | 25% | Anteil relevanter Stargazers (500+ Followers) relativ zur Repo-Groesse |
| Bus Factor | 25% | Wie viele Core-Devs fuer 80% der Commits verantwortlich sind |
| Freshness | 20% | Tage seit dem letzten Commit |
| Issue Health | 15% | Verhaeltnis geschlossene / offene Issues |
| Star Velocity | 15% | Organisches Wachstum vs. verdaechtiger Spike |

Stichprobe dynamisch: Repos <5k Stars werden tiefer abgetastet (bis 1.000 Stargazers) fuer hoehere Coverage.

## Quadranten & Rings

```
                    AI Workflow &
                    Orchestration
                         |
     Patterns &    ------+------  Libraries &
     Methods             |        Frameworks
                         |
                    Developer Tools
                      & Infra
```

| Ring | Bedeutung |
|------|-----------|
| **Adopt** | Aktiv im Einsatz, bewaehrt |
| **Trial** | Getestet, vielversprechend |
| **Scout** | Gefunden, sieht relevant aus |
| **Hold** | Bekannt, aktuell nicht empfohlen |

## Top-Eintraege nach Quality Score

| Repo | Score | Ring | Highlights |
|------|-------|------|------------|
| **DuckDB** | 8.9 | Adopt | Bus Factor 7, Wes McKinney (Pandas) als Stargazer |
| **GitHub MCP Server** | 8.8 | Trial | Offiziell von GitHub, Bus Factor 10, Top-Notables (Google, Docker) |
| **Claude Agent SDK** | 8.4 | Trial | Anthropic-offiziell, Notable Density 10/10 |
| **Polars** | 8.1 | Adopt | Bus Factor 6, 37.6k Stars organisch |
| **Agentic Design Patterns** | 7.9 | Trial | Andrew Ng's 4 Kernmuster fuer AI Agents |

## Kandidaten-Pipeline

Neue Repos werden automatisch entdeckt (Mo + Do, 07:00 via Mac Mini) und landen in `candidates/pending.json`. Von dort werden sie kuratiert und ins Radar uebernommen.

```bash
# Kandidat aus pending.json ins Radar uebernehmen (interaktiv)
python3 accept-to-radar.py

# Direkt per Repo-Name
python3 accept-to-radar.py owner/repo

# Alle akzeptierten Kandidaten verarbeiten
python3 accept-to-radar.py --accepted
```

Der Telegram-Bot (`@github_radar_bot`) benachrichtigt ueber neue Kandidaten und bietet Steuerung:
`/radar_status`, `/radar_run`, `/radar_pause`, `/radar_resume`, `/radar_minstars N`

## Daten aktualisieren

```bash
# Quality Score, Stars, Notable Stargazers, Bus Factor — alles in einem Lauf
python3 update-radar.py
```

## Neuen Eintrag manuell hinzufuegen

Eintrag in `docs/data/entries.json` ergaenzen:

```json
{
  "id": "mein-tool",
  "name": "Mein Tool",
  "quadrant": "Libraries & Frameworks",
  "ring": "Scout",
  "url": "https://github.com/...",
  "stars": 0,
  "language": "Python",
  "license": "MIT",
  "description": "Was es macht",
  "strengths": "Was gut ist",
  "weaknesses": "Was nicht gut ist",
  "learned": "Was ich gelernt habe",
  "added": "2026-03-09",
  "tested": false,
  "category": "radar"
}
```

Danach `python3 update-radar.py` ausfuehren — Stars, Quality Score und Notable Stargazers werden automatisch ergaenzt.

## Projektstruktur

```
github-radar/
├── docs/                    # Website (GitHub Pages, kein Build-Step)
│   ├── index.html
│   ├── radar.js             # SVG-Radar + Interaktion
│   ├── style.css            # GitHub Dark Theme
│   └── data/
│       └── entries.json     # Alle Radar-Eintraege + Scores
├── candidates/
│   └── pending.json         # Kandidaten aus automatischer Discovery
├── accept-to-radar.py       # Kandidat evaluieren + ins Radar uebernehmen
├── update-radar.py          # Quality-Analyse (GitHub GraphQL + REST)
├── discover-repos.py        # Automatische Repo-Discovery (Topics + Keywords)
├── radar-bot.py             # Telegram-Bot zur Steuerung
├── mac-mini-setup.sh        # LaunchAgent Setup fuer Mac Mini
├── config.json              # Discovery-Konfiguration
├── LICENSE                  # MIT
└── .gitignore
```

## Lizenz

MIT

---

Ein [AgentField](https://github.com/janrummel/claude-orchestrator-starter) Projekt.
