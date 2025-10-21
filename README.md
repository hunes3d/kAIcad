<div align="center">
  <img src="assets/kaicad.svg" alt="kAIcad Logo" width="320" />

  <h1>kAIcad</h1>
  <p><strong>AI‑powered sidecar for KiCad schematics</strong></p>

  <p>
    <a href="https://github.com/hunes3d/kAIcad/actions"><img alt="CI" src="https://github.com/hunes3d/kAIcad/workflows/CI/badge.svg"></a>
    <img alt="Python" src="https://img.shields.io/badge/python-3.10+-blue.svg">
    <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-AGPL--3.0-blue.svg"></a>
    <img alt="Version" src="https://img.shields.io/badge/version-0.2.0-green.svg">
  </p>

  <p>Describe a change in plain English → get a plan → apply it to your <code>.kicad_sch</code> file.</p>
</div>

## What it does

- “Add LED and 1k resistor between VCC and GND” → places LED + resistor and wires nets
- “Connect U1 pin 3 to R5 pin 2” → makes the connection via wire/label
- After applying, it can run ERC and export PDF/netlist with KiCad CLI

## Highlights

- 🤖 AI planning via OpenAI models (aliases supported)
- 🖥️ Three UIs: CLI, Desktop (Tkinter), Web (Flask, default port 5173)
- 🔍 Inspect components, nets, and hierarchical sheets
- ✅ Optional post‑apply: ERC, PDF, and netlist export
- � Stores API key in your OS keychain when available

## Quick start

### Windows (PowerShell)

Prerequisites:
- Python 3.10+
- KiCad 9 CLI on PATH (verify with: `kicad-cli --version`)
- OpenAI API key

#### Option A — pipx (recommended):

```powershell
pipx install git+https://github.com/hunes3d/kAIcad.git

# Create a .env file (or set env vars) next to your project
"OPENAI_API_KEY=sk-your-key" | Out-File -Encoding ascii -FilePath .env
"OPENAI_MODEL=gpt-4o-mini"   | Add-Content .env
"FLASK_ENV=development"      | Add-Content .env  # for local web UI without a custom secret

# Launch your preferred UI
kaicad-desk   # Desktop GUI
# kaicad-web  # Web UI at http://127.0.0.1:5173
# kaicad      # CLI
```

#### Option B — dev install:

```powershell
git clone https://github.com/hunes3d/kAIcad.git
cd kAIcad
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .

Copy-Item .env.example .env
# Edit .env to set OPENAI_API_KEY and (optionally) OPENAI_MODEL

python -m kaicad.ui.desktop   # Desktop GUI
# python -m kaicad.ui.web.app  # Web UI
# python -m kaicad.ui.cli      # CLI
```

### macOS / Linux (Bash/Zsh)

Prerequisites:
- Python 3.10+
- KiCad 9 CLI on PATH (verify with: `kicad-cli --version`)
  - macOS: Install KiCad.app, then add to PATH:  
    `export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"`
  - Linux: Install via package manager (e.g., `apt install kicad` on Ubuntu/Debian)
- OpenAI API key

#### Option A — pipx (recommended):

```bash
pipx install git+https://github.com/hunes3d/kAIcad.git

# Create a .env file (or set env vars) next to your project
cat > .env << EOF
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
FLASK_ENV=development
EOF

# Launch your preferred UI
kaicad-desk   # Desktop GUI
# kaicad-web  # Web UI at http://127.0.0.1:5173
# kaicad      # CLI
```

#### Option B — dev install:

```bash
git clone https://github.com/hunes3d/kAIcad.git
cd kAIcad
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# Edit .env to set OPENAI_API_KEY and (optionally) OPENAI_MODEL

python -m kaicad.ui.desktop   # Desktop GUI
# python -m kaicad.ui.web.app  # Web UI
# python -m kaicad.ui.cli      # CLI
```

## VS Code tasks

Tasks are preconfigured:
- sidecar — CLI
- desktop-gui — Desktop GUI
- web-gui — Web UI
- erc / pdf / netlist — KiCad CLI helpers
- plan:demo — Generate a demo plan
- e2e:export-pdf — Plan → apply → export PDF

Use Ctrl+Shift+B to open the task picker.

## Configuration

Use a local `.env` file or environment variables:

- OPENAI_API_KEY — required
- OPENAI_MODEL — e.g., gpt-4o-mini (recommended)
- OPENAI_TEMPERATURE — default 0.0
- FLASK_ENV — set to `development` for local web without a custom secret
- FLASK_SECRET_KEY — required in production web mode
- KAICAD_PROJECT — default project path

See `.env.example` for a ready-to-copy template.

## Reproducible installs & tests

- Dev environment:
  - Install base + dev deps: `pip install -r requirements-dev.txt`
  - Or use the lockfile: `pip install -r requirements.lock`
- Refresh the lockfile after dependency changes (requires pip-tools):
  - `pip-compile --generate-hashes --output-file=requirements.lock requirements.txt`
- Run tests with coverage locally:
  - `pytest -q --cov=kaicad --cov-report=term-missing`

## Tips & troubleshooting

### Common issues

- **Web UI exits immediately?**  
  Set `FLASK_ENV=development` or provide a secure `FLASK_SECRET_KEY`.

- **KiCad tools not found?**  
  - Windows: Add `C:\Program Files\KiCad\9.0\bin` to PATH and re-open your shell.
  - macOS: Add KiCad to PATH: `export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"`
  - Linux: Ensure `kicad-cli` is installed and on PATH (e.g., `which kicad-cli`)

- **Model errors?**  
  Try `OPENAI_MODEL=gpt-4o-mini` and ensure your API key is valid.

- **Python version issues?**  
  - Linux/macOS: Use `python3` instead of `python`
  - Verify version with: `python --version` (or `python3 --version`)

### Platform-specific notes

- **macOS**: The desktop GUI requires Tkinter (included with python.org Python, may need separate install for Homebrew Python)
- **Linux**: Install `python3-tk` package for desktop GUI support (e.g., `apt install python3-tk` on Ubuntu/Debian)
- **Windows**: Tkinter is included with standard Python installer

## Wiki

Documentation is available in the `docs/` folder:

- [Architecture](docs/architecture.md) — System design and module overview
- [Component Inspection](docs/component-inspection.md) — Querying components and nets
- [Hierarchical Sheets](docs/hierarchical-sheets.md) — Working with hierarchical designs
- [Dev Notes](docs/dev-notes.md) — Development guidelines
- [Roadmap](docs/roadmap.md) — Future plans
- [Changelog](docs/changelog.md) — Version history

Or visit the GitHub Wiki: https://github.com/hunes3d/kAIcad/wiki

## License

AGPL-3.0 — see [`LICENSE`](LICENSE).

## Acknowledgments

- kicad-skip — KiCad file manipulation
- OpenAI — language models
- KiCad — Open‑source EDA suite
