# kAIcad Wiki

Welcome to the kAIcad Wiki. This site consolidates key docs in one place and is designed to be published to the GitHub Wiki.

Project: https://github.com/hunes3d/kAIcad  
Wiki: https://github.com/hunes3d/kAIcad/wiki

## Overview

kAIcad is an AI‑powered sidecar for KiCad schematics. Describe changes in plain English → get a plan → apply it to your `.kicad_sch` file. It can optionally run ERC and export PDF/netlist using KiCad CLI.

## Highlights

- AI planning via OpenAI models (aliases supported)
- Three UIs: CLI, Desktop (Tkinter), Web (Flask)
- **Full component creation** from KiCad libraries (via custom kicad-skip fork)
- Inspect components, nets, and hierarchical sheets
- Optional post‑apply: ERC, PDF, and netlist export
- Secure: API key stored in OS keychain when available

## Quick Start (Windows, PowerShell)

Prerequisites:
- Python 3.10+
- KiCad 9 CLI on PATH (`kicad-cli --version`)
- OpenAI API key

Install and run:

```powershell
pipx install git+https://github.com/hunes3d/kAIcad.git

"OPENAI_API_KEY=sk-your-key" | Out-File -Encoding ascii -FilePath .env
"OPENAI_MODEL=gpt-4o-mini"   | Add-Content .env
"FLASK_ENV=development"      | Add-Content .env

kaicad-desk   # Desktop GUI
# kaicad-web  # Web UI (http://127.0.0.1:5173)
# kaicad      # CLI
```

Dev install:

```powershell
git clone https://github.com/hunes3d/kAIcad.git
cd kAIcad
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
Copy-Item .env.example .env
python -m sidecar.desk   # or sidecar.web / sidecar.main
```

## VS Code Tasks

- sidecar — CLI
- desktop-gui — Desktop GUI
- web-gui — Web UI
- erc / pdf / netlist — KiCad CLI helpers
- plan:demo — Generate a demo plan
- e2e:export-pdf — Plan → apply → export PDF

## Configuration

Use `.env` or environment variables:
- `OPENAI_API_KEY` — required
- `OPENAI_MODEL` — e.g., `gpt-4o-mini` (recommended)
- `OPENAI_TEMPERATURE` — default 0.0
- `FLASK_ENV` — set `development` for local web without a custom secret
- `FLASK_SECRET_KEY` — required in production web mode
- `KAICAD_PROJECT` — default project path

## Troubleshooting

- **Component creation now works!** As of October 2025, kAIcad uses a custom kicad-skip fork with full component creation and pin coordinate support for ALL component types (including multi-pin ICs and connectors).
- Web UI exits immediately? Set `FLASK_ENV=development` or provide a secure `FLASK_SECRET_KEY`.
- KiCad tools not found? Add `C:\\Program Files\\KiCad\\9.0\\bin` to PATH and reopen your shell.
- Model errors? Try `OPENAI_MODEL=gpt-4o-mini` and ensure your API key is valid.

## Documentation Index

- **[[Known-Issues]]** — Current limitations and workarounds ⚠️
- [[Architecture]] — Core components and design
- [[Features]] — Component inspection and hierarchical sheets
- [[Roadmap]] — Development plans and vision
- [[Dev-Notes]] — Technical details, dependencies, and publishing

## License

AGPL-3.0 — see the repository `LICENSE` file.
