# GitHub-Radar

> Persoenlicher Technologie-Radar fuer das Dev-Universum rund um Claude Code & AI Agents.
> Kein Link-Dump — getestete Bewertungen aus Anwender-Perspektive.

**[Website oeffnen](https://janrummel.github.io/github-radar/)** · 19 Eintraege · 4 Quadranten · Quality Score 0–10

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
| **Claude Agent SDK** | 8.4 | Trial | Anthropic-offiziell, Notable Density 10/10 |
| **Polars** | 8.1 | Adopt | Bus Factor 6, 37.6k Stars organisch |
| **Agentic Design Patterns** | 7.9 | Trial | Andrew Ng's 4 Kernmuster fuer AI Agents |
| **Context Engineering** | 7.6 | Adopt | Karpathy-Konzept, fundamentales Pattern |

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
├── docs/                    # Website (GitHub Pages, kein Build-Step)
│   ├── index.html
│   ├── radar.js             # SVG-Radar + Interaktion
│   ├── style.css            # GitHub Dark Theme
│   └── data/
│       └── entries.json     # Alle Radar-Eintraege + Scores
├── update-radar.py          # Quality-Analyse (GitHub GraphQL + REST)
├── LICENSE                  # MIT
└── .gitignore
```

## Lizenz

MIT

---

Ein [AgentField](https://github.com/janrummel/claude-orchestrator-starter) Projekt.
