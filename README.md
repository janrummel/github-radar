# GitHub-Radar

Persoenlicher Technologie-Radar fuer das Dev-Universum rund um Claude Code & AI Agents.

Kein Link-Dump. Getestete Bewertungen aus Anwender-Perspektive.

## Konzept

Inspiriert vom [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar) — aber persoenlich, fuer GitHub Repos und Developer Tools.

### Rings

| Ring | Bedeutung |
|---|---|
| **Adopt** | Aktiv im Einsatz |
| **Trial** | Angeschaut und getestet |
| **Scout** | Gefunden, sieht relevant aus |
| **Hold** | Kenne ich, will ich nicht |

### Quadranten

| Quadrant | Beispiele |
|---|---|
| **AI Workflow & Orchestration** | GSD, cc-sdd, OpenFang |
| **Libraries & Frameworks** | Polars, Scrapling, FastMCP |
| **Developer Tools & Infra** | MCP-Server, awesome-Listen, SDKs |
| **Patterns & Methods** | Spec-Driven Dev, Context Engineering |

## Website

[GitHub-Radar Live](https://janrummel.github.io/github-radar/)

## Neuen Eintrag hinzufuegen

Eintrag in `data/entries.json` ergaenzen:

```json
{
  "id": "mein-tool",
  "name": "Mein Tool",
  "quadrant": "Libraries & Frameworks",
  "ring": "Scout",
  "url": "https://github.com/...",
  "stars": 1234,
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

## Lizenz

MIT
