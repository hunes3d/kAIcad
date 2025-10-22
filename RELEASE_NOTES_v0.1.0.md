# kAIcad v0.1.0 Release Notes

**Release Date:** October 22, 2025

This is the **initial public release** of kAIcad - an AI-powered sidecar for KiCad schematics that lets you describe schematic changes in plain English and apply them programmatically.

## 🎉 New Features

### Interactive Launcher
- **New unified launcher** - Run `kaicad` to get an interactive menu
- Choose between CLI, Desktop (Tkinter), or Web (Flask) interfaces
- Command-line options: `kaicad --cli`, `kaicad --desktop`, `kaicad --web`
- Direct commands still available: `kaicad-cli`, `kaicad-desk`, `kaicad-web`

### Core Functionality
- 🤖 **AI-powered planning** via OpenAI models (gpt-4o, gpt-4o-mini, o1-mini)
- 📝 **Natural language interface** - "Add LED and resistor" → schematic changes
- 🔌 **Multi-pin support** - Full support for ICs, connectors, and complex components
- 🔍 **Schematic inspection** - Query components, nets, and hierarchical sheets
- ✅ **KiCad integration** - Run ERC, export PDF/netlist using KiCad CLI
- 🔐 **Secure API key storage** - Uses OS keychain when available

### Three User Interfaces
1. **CLI** - Fast command-line interface for scripting
2. **Desktop** - Tkinter GUI for local desktop usage
3. **Web** - Flask-based web interface (default port 5173)

### Advanced Features
- **Symbol.from_lib()** support via kicad-skip v0.2.6 fork
- **Pin location helpers** - `get_pin_locations()`, `get_pin_by_name()`, `get_pin_by_number()`
- **Property setters** - Clean `symbol.Reference = "R1"` syntax
- **Model registry** - Support for multiple OpenAI models with aliases
- **Compatibility wrapper** - Works with both old and new kicad-skip versions

## 📦 Installation

### Quick Install (pipx recommended)
```bash
pipx install git+https://github.com/hunes3d/kAIcad.git
kaicad --help
```

### Development Install
```bash
git clone https://github.com/hunes3d/kAIcad.git
cd kAIcad
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

## 🔧 Requirements

- **Python 3.10+** (tested on 3.10-3.14)
- **KiCad 9** with CLI tools on PATH
- **OpenAI API key** for AI planning features

## 🐛 Known Issues

- Some tests may be skipped if `kicad-cli` is not found (non-blocking)
- Desktop interface requires Tkinter (usually included with Python)
- Web interface requires manual secret key configuration for production

## 📚 Documentation

- Full documentation available in `/docs` folder
- README with quick start guide
- Architecture documentation
- Known issues and troubleshooting

## 🙏 Acknowledgments

This project builds on:
- **kicad-skip** by Pat Deegan - S-expression parser for KiCad files
- **kicad-skip fork** by Gunes Yilmaz - Enhanced with Symbol.from_lib() and pin helpers
- **OpenAI** - For GPT models powering the planning engine

## 🔗 Links

- **Repository:** https://github.com/hunes3d/kAIcad
- **Issues:** https://github.com/hunes3d/kAIcad/issues
- **License:** AGPL-3.0

## 🚀 What's Next?

See our [roadmap](docs/roadmap.md) for planned features:
- Bulk operations support
- Custom component libraries
- Schematic diffing
- Integration with more AI models
- PCB layout support

---

**Enjoy building schematics with AI! 🎨⚡**
