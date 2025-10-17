# Architecture

This page summarizes the system architecture and the key improvements implemented.

## Core Modules

- `planner.py` — Converts natural language into structured plans (OpenAI)
- `schema.py` — Pydantic models for plan validation
- `writer_skip.py` — Applies plans to `.kicad_sch` using kicad-skip
- `inspector.py` — Inspection utilities (components, nets, hierarchy)
- `tasks.py` — KiCad CLI operations (ERC, PDF, netlist)
- `web.py` — Flask web UI (no Tkinter, CSRF enabled)
- `desk.py` — Tkinter desktop GUI
- `models.py` — Model registry and validation
- `settings.py` — Settings with secure key storage via keyring

## High-Level Diagram

```
User (CLI / Desktop GUI / Web)
        │
        ▼
    planner.py  →  schema.py  →  writer_skip.py  →  .kicad_sch
        │                               │
        │                               ├─ tasks.py (ERC / PDF / netlist)
        └─ inspector.py                 └─ kicad-skip (parsing)
```

## Security

- API keys stored in OS keychain where available (keyring)
- Web UI enforces `FLASK_SECRET_KEY` in production; `FLASK_ENV=development` for local ease
- CSRF protection enabled via Flask-WTF

## State Storage (Web UI)

- `.chat_history.json` — Chat conversations
- `.plan_history.json` — Plans generated
- `.current_project.json` — Active project path
- `.recent_projects.json` — Recently used projects

## Testing

- Unit tests for schema round-trip and inspector
- Integration tests for end-to-end workflows
