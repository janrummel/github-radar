# GitHub-Radar

> Persoenlicher Technologie-Radar fuer das Dev-Universum rund um Claude Code & AI Agents.
> Kein Link-Dump — getestete Bewertungen aus Anwender-Perspektive.

**[Website oeffnen (lokal)](http://localhost:8090)** · 14 Eintraege · 4 Quadranten · Quality Score 0–10

---

## Schnellstart

```bash
cd docs && python3 -m http.server 8090
open http://localhost:8090
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
| **Polars** | 8.1 | Adopt | Bus Factor 6, 37.6k Stars organisch |
| **cc-sdd** | 7.2 | Scout | Hoechste Notable Density (1.07) |
| **awesome-claude-code** | 5.5 | Scout | Gut maintained, aktive Community |
| **Scrapling** | 5.3 | Scout | Bus Factor 1, Stars-Inflation-Risiko |
| **GSD** | 4.7 | Trial | Nur 1 Notable bei 26k Stars |

## Daten aktualisieren

```bash
# Quality Score, Stars, Notable Stargazers, Bus Factor — alles in einem Lauf
python3 update-radar.py
```

## Neuen Eintrag hinzufuegen

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
  "added": "2026-03-08",
  "tested": false
}
```

Danach `python3 update-radar.py` ausfuehren — Stars, Quality Score und Notable Stargazers werden automatisch ergaenzt.

## Projektstruktur

```
github-radar/
├── docs/                    # Website (statisch, kein Build-Step)
│   ├── index.html
│   ├── radar.js             # SVG-Radar + Interaktion
│   ├── style.css            # GitHub Dark Theme
│   └── data/
│       └── entries.json     # Alle Radar-Eintraege + Scores
├── update-radar.py          # Quality-Analyse (GitHub GraphQL + REST)
├── notable-stargazers.py    # Standalone Notable-Analyse (Legacy)
└── inject-notables.py       # Standalone Inject (Legacy)
```

## Lizenz

MIT

---

Ein [AgentField](https://github.com/janrummel/claude-orchestrator-starter) Projekt.
