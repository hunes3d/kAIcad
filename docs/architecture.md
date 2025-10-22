# Architecture

This page summarizes the system architecture and the key improvements implemented.

## Package Structure

kAIcad follows a modern **src-layout** with clear separation of concerns:

### Core Logic (`kaicad.core`)
- `planner.py` — Converts natural language into structured plans (OpenAI)
- `writer.py` — Applies plans to `.kicad_sch` using kicad-skip (formerly writer_skip.py)
- `inspector.py` — Inspection utilities (components, nets, hierarchy)
- `models.py` — Model registry and validation

### Data Models (`kaicad.schema`)
- `plan.py` — Pydantic models for plan validation (formerly schema.py)
- `schematic.py` — Schematic data models (formerly sch_model.py)

### KiCad Integration (`kaicad.kicad`)
- `tasks.py` — KiCad CLI operations (ERC, PDF, netlist)
- `watcher.py` — File system watching
- `symtab.py` — Symbol table management

### User Interfaces (`kaicad.ui`)
- `cli.py` — Command-line interface (formerly main.py)
- `desktop.py` — Tkinter desktop GUI (formerly desk.py)
- `web/app.py` — Flask web UI with CSRF protection (formerly web.py)
- `web/templates/` — Web UI templates

### Configuration (`kaicad.config`)
- `settings.py` — Settings with secure key storage via keyring

## High-Level Diagram

```
User (CLI / Desktop GUI / Web)
        │
        ▼
  kaicad.core.planner  →  kaicad.schema.plan  →  kaicad.core.writer  →  .kicad_sch
        │                                              │
        │                                              ├─ kaicad.kicad.tasks (ERC/PDF/netlist)
        └─ kaicad.core.inspector                       └─ kicad-skip fork (parsing + symbol creation)
```

## Dependencies

### kicad-skip Fork

kAIcad uses a custom fork of kicad-skip with enhanced symbol creation capabilities:

- **Repository**: https://github.com/hunes3d/kicad-skip
- **Key Additions**:
  - `Symbol.from_lib(doc, lib_id, reference, at_x, at_y)` — Create symbols from library
  - Direct property setters — `sym.Value = "x"`, `sym.Reference = "x"`
  - Immediate collection updates — Symbols appear in `doc.symbol` immediately
  - PropertyString objects — Access via `.value` attribute (e.g., `sym.Value.value`)

**Why a Fork?**

The upstream kicad-skip (v0.2.5) provides excellent KiCad file parsing but lacks APIs for programmatic symbol creation. Our fork adds this critical functionality while maintaining full compatibility with the upstream API.

**Integration Points**:
- `writer.py::apply_plan()` — Uses `Symbol.from_lib()` for component creation
- `writer.py::lookup_pin_coords()` — Calculates pin positions using standard offsets
- `inspector.py` — Uses standard kicad-skip read APIs (unchanged)

**Future**: Changes may be contributed upstream if the maintainer is interested in merging symbol creation features.

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

The test suite is organized by type:

- `tests/unit/` — Unit tests for models, planner, schemas, settings
- `tests/integration/` — Integration tests for inspector, tasks, writer
- `tests/ui/` — UI tests for CLI, web, and desktop interfaces
- `tests/fixtures/` — Test fixtures, golden files, and smoke tests

Run tests with: `pytest -v` or `pytest --cov=kaicad --cov-report=term-missing`
