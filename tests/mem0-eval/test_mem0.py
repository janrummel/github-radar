"""
Mem0 Evaluation: Kann Mem0 die concept_relations-Tabelle ersetzen
und automatisch aus Arbeitssessions Wissen extrahieren?

Test-Setup:
- LLM: Anthropic Claude (Sonnet) fuer Fact-Extraction
- Vector Store: Qdrant on-disk (lokal, kein Server noetig)
- Embedder: OpenAI text-embedding-3-small (Standard)

Test-Ablauf:
1. Mem0 mit Claude konfigurieren
2. 10 repraesentative AgentField-Dialoge einspeisen
3. Recall-Qualitaet testen mit 10 Fragen
4. Ergebnis: Hit-Rate, Relevanz, Vergleich zu concept_relations
"""

import os
import json
from mem0 import Memory

# --- Config: Ollama LLM (lokal) + lokale HuggingFace Embeddings ---
# Kein API-Key noetig — alles laeuft lokal
config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.2:3b",
            "temperature": 0.1,
            "ollama_base_url": "http://localhost:11434",
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dims": 384,
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "embedding_model_dims": 384,
        }
    },
}

print("=== Mem0 Evaluation fuer AgentField ===\n")

# --- Init ---
print("1. Initialisiere Mem0 mit Claude...")
m = Memory.from_config(config)
print("   OK\n")

# --- Feed: 10 repraesentative AgentField-Dialoge ---
print("2. Speise 10 AgentField-Dialoge ein...")

sessions = [
    # Session 1: GitHub-Radar Architektur-Entscheidung
    [
        {"role": "user", "content": "Ich will einen Technology Radar bauen fuer Claude Code und AI Agent Repos. Soll ich die Daten in einer Datenbank oder in JSON speichern?"},
        {"role": "assistant", "content": "Fuer einen Tech-Radar mit 50-100 Eintraegen empfehle ich eine einzelne entries.json. Vorteile: Versionierung mit Git, kein DB-Setup, direkt von GitHub Pages ladbar. SQLite waere Overkill fuer diese Groessenordnung."}
    ],
    # Session 2: Scoring-System
    [
        {"role": "user", "content": "Wie soll ich die Quality-Scores fuer die Radar-Eintraege berechnen?"},
        {"role": "assistant", "content": "Der Quality-Score kombiniert 5 Signale: Notable Density (25%), Bus Factor (25%), Freshness (20%), Issue Health (15%), Star Velocity (15%). Notable Stargazers werden gewichtet: 500-999 Followers = 1 Punkt, 1k-5k = 2, 5k-10k = 4, 10k+ = 8 Punkte. Star Velocity bestraft extrem schnelles Wachstum als Red Flag."}
    ],
    # Session 3: Radar/Landscape Trennung
    [
        {"role": "user", "content": "LangChain hat Score 6.8 aber ich will es nicht empfehlen. AutoGPT auch nicht. Wie loesung?"},
        {"role": "assistant", "content": "Wir trennen: Radar (persoenlicher Stack-Kompass, nur evaluierte/getestete Repos) vs. Landscape (Kontext-Referenz, bekannte Repos ohne Empfehlung). Score im Radar = Empfehlung, Score in Landscape = nur Health-Referenz. LangChain und AutoGPT gehen in die Landscape."}
    ],
    # Session 4: Mac Mini Automation
    [
        {"role": "user", "content": "Ich habe einen Mac Mini. Kann der automatisch neue Repos discovern?"},
        {"role": "assistant", "content": "Ja. discover-repos.py sucht via GitHub API nach neuen Repos zu konfigurierten Topics. LaunchAgent auf dem Mac Mini laeuft Mo+Do um 07:00. Ergebnisse landen in candidates/pending.json. Telegram-Bot @github_radar_bot benachrichtigt bei neuen Funden."}
    ],
    # Session 5: Polars Evaluation
    [
        {"role": "user", "content": "Was ist deine Einschaetzung zu Polars als DataFrame Library?"},
        {"role": "assistant", "content": "Polars ist Adopt. 37.6k Stars organisch gewachsen, 665 Contributors, MIT-Lizenz. Zero-copy, lazy evaluation, multi-threaded. Klare Alternative zu Pandas fuer Performance-kritische Datenverarbeitung. Bus Factor ist hoch (14), Notable Density exzellent. Quality-Score 8.9."}
    ],
    # Session 6: AgentField Workflow
    [
        {"role": "user", "content": "Wie funktioniert unser AgentField Workflow?"},
        {"role": "assistant", "content": "Drei Phasen: Klaeren (clarity, analyze, research-pipeline), Machen (express, capture, engineering), Fertig machen (signal-check, challenge). Jede Aufgabe durchlaeuft alle drei. Neue Ideen waehrend der Arbeit in die Inbox, nicht verfolgen. Ein aktives Projekt, laufend aktualisierter State in ~/.claude/orchestrator/projects/."}
    ],
    # Session 7: Obsidian MCP Setup
    [
        {"role": "user", "content": "Wie sind die Obsidian Vaults mit Claude Code verbunden?"},
        {"role": "assistant", "content": "5 Obsidian Vaults via MCP-Server: ClaudeSystem (Port 27124), OpenClaw (27125), ELadeinfrastruktur (27126), KnowledgeFactory (27127), Curve2Charger (27128). Jeder hat einen eigenen gepatchten Binary und API-Key. Obsidian muss offen sein (REST API). Wichtig: create_vault_file nutzen, nicht update_active_file."}
    ],
    # Session 8: Memory-Problem
    [
        {"role": "user", "content": "Unser concept_relations hat nur 32 Kanten und wird nicht automatisch befuellt. Wie loesen wir das?"},
        {"role": "assistant", "content": "Drei Kandidaten aus dem Radar: Mem0 (automatisches Memory-Layer, 49k Stars, Q=7.5), Beads (Structured Context Passing), Claude-Mem (Claude-spezifisch). Test-Frage: Kann Mem0 die concept_relations-Tabelle ersetzen und automatisch aus Arbeit befuellen?"}
    ],
    # Session 9: GSD Learnings
    [
        {"role": "user", "content": "Was haben wir von GSD (Get Shit Done) gelernt?"},
        {"role": "assistant", "content": "Drei Dinge uebernommen: 1) Context Monitor Hook (WARNING bei 35%, CRITICAL bei 25% Context), 2) Analysis Paralysis Guard (5+ Reads ohne Action = Stuck-Signal), 3) Deviation Rules (Auto-fix Bugs/Security/Blocker, aber bei Architektur-Aenderungen User fragen). Achtung: GSD hat einen Crypto-Token ($GSD), Bus Factor 1."}
    ],
    # Session 10: Website Tags + Related
    [
        {"role": "user", "content": "Wie machen wir Querverbindungen zwischen Repos sichtbar?"},
        {"role": "assistant", "content": "Zwei Felder in entries.json: tags (Array von Strings wie 'mcp-server', 'claude-ecosystem') und related (Array von Entry-IDs). Tags als Filter-Buttons auf der Website. Related als 'Verwandte Eintraege' im Detail-Panel, klickbar. 5 erkannte Familien: Firecrawl, Claude SDK, Browser, Memory, Agent Frameworks."}
    ],
]

for i, session in enumerate(sessions):
    result = m.add(session, user_id="jan", metadata={"session": f"agentfield-{i+1}"})
    mem_count = len(result.get("results", []))
    print(f"   Session {i+1}: {mem_count} Memories extrahiert")

print()

# --- Recall: 10 Test-Fragen ---
print("3. Teste Recall mit 10 Fragen...\n")

questions = [
    ("Wie berechnet sich der Quality-Score im Radar?", "5 Signale: Notable Density, Bus Factor, Freshness, Issue Health, Star Velocity"),
    ("Welche Obsidian Vaults gibt es und auf welchen Ports?", "5 Vaults: ClaudeSystem 27124, OpenClaw 27125, ELadeinfrastruktur 27126, KnowledgeFactory 27127, Curve2Charger 27128"),
    ("Was ist der Unterschied zwischen Radar und Landscape?", "Radar = persoenlicher Stack, Landscape = Kontext-Referenz ohne Empfehlung"),
    ("Wann laeuft die automatische Repo-Discovery?", "Mo+Do 07:00 auf Mac Mini, Telegram-Bot benachrichtigt"),
    ("Welche drei Dinge haben wir von GSD uebernommen?", "Context Monitor, Analysis Paralysis Guard, Deviation Rules"),
    ("Wie ist der AgentField Workflow aufgebaut?", "3 Phasen: Klaeren, Machen, Fertig machen"),
    ("Was ist Polars und wie gut ist es?", "DataFrame Library, Adopt, Score 8.9, 37.6k Stars"),
    ("Welche Memory-Kandidaten gibt es im Radar?", "Mem0, Beads, Claude-Mem"),
    ("Wie werden Querverbindungen im Radar dargestellt?", "tags + related Felder, Filter-Buttons, Verwandte Eintraege im Detail-Panel"),
    ("Warum ist entries.json besser als eine Datenbank fuer den Radar?", "Git-Versionierung, kein DB-Setup, direkt von GitHub Pages ladbar"),
]

hits = 0
for q, expected in questions:
    results = m.search(q, user_id="jan", limit=3)
    top_memories = results.get("results", []) if isinstance(results, dict) else results

    # Check if any returned memory contains key terms from expected answer
    found = False
    top_text = ""
    for mem in top_memories[:3]:
        text = mem.get("memory", "") if isinstance(mem, dict) else str(mem)
        top_text += text + " "

    # Simple keyword overlap check
    expected_keywords = [w.lower() for w in expected.split() if len(w) > 4]
    matched_keywords = [k for k in expected_keywords if k in top_text.lower()]
    hit_rate = len(matched_keywords) / max(len(expected_keywords), 1)

    if hit_rate >= 0.3:
        found = True
        hits += 1

    status = "HIT" if found else "MISS"
    print(f"   [{status}] {q}")
    if top_memories:
        first = top_memories[0]
        mem_text = first.get("memory", str(first)) if isinstance(first, dict) else str(first)
        print(f"         → {mem_text[:120]}...")
    print()

print(f"\n=== ERGEBNIS ===")
print(f"Recall: {hits}/10 ({hits*10}%)")
print(f"Memories gespeichert: {len(m.get_all(user_id='jan'))}")

# Show all stored memories
print(f"\n=== ALLE GESPEICHERTEN MEMORIES ===")
all_mems = m.get_all(user_id="jan")
if isinstance(all_mems, dict):
    all_mems = all_mems.get("results", [])
for i, mem in enumerate(all_mems):
    text = mem.get("memory", str(mem)) if isinstance(mem, dict) else str(mem)
    print(f"   {i+1}. {text}")
