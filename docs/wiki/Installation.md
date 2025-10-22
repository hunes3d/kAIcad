# Installation Guide

Complete installation instructions for all platforms.

## System Requirements

### Required

- **Python**: 3.10, 3.11, 3.12, or 3.13
- **KiCad**: Version 7.0 or higher
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **OpenAI API Key**: Required for AI functionality

### Recommended

- **Git**: For version control and development
- **Virtual Environment**: To isolate dependencies

## Installation Methods

### Method 1: PyPI (Recommended)

Install the latest stable release from PyPI:

```bash
pip install kaicad
```

To upgrade to the latest version:

```bash
pip install --upgrade kaicad
```

### Method 2: From GitHub Release

Download the latest release from [GitHub Releases](https://github.com/hunes3d/kAIcad/releases):

```bash
# Download the wheel file
pip install kaicad-0.1.0-py3-none-any.whl
```

### Method 3: From Source (Development)

For the latest development version:

```bash
# Clone the repository
git clone https://github.com/hunes3d/kAIcad.git
cd kAIcad

# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e . -r requirements-dev.txt
```

## Platform-Specific Instructions

### Windows

1. **Install Python**:
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Install kAIcad**:
   ```powershell
   pip install kaicad
   ```

3. **Verify Installation**:
   ```powershell
   kaicad --help
   ```

### macOS

1. **Install Python** (if not already installed):
   ```bash
   brew install python@3.11
   ```

2. **Install kAIcad**:
   ```bash
   pip3 install kaicad
   ```

3. **Verify Installation**:
   ```bash
   kaicad --help
   ```

### Linux (Ubuntu/Debian)

1. **Install Python** (if not already installed):
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **Install kAIcad**:
   ```bash
   pip3 install kaicad
   ```

3. **Verify Installation**:
   ```bash
   kaicad --help
   ```

## Virtual Environment Setup (Recommended)

Using a virtual environment keeps kAIcad's dependencies isolated:

### Windows

```powershell
# Create virtual environment
python -m venv kaicad-env

# Activate it
.\kaicad-env\Scripts\activate

# Install kAIcad
pip install kaicad
```

### macOS/Linux

```bash
# Create virtual environment
python3 -m venv kaicad-env

# Activate it
source kaicad-env/bin/activate

# Install kAIcad
pip install kaicad
```

## Configuring KiCad

kAIcad requires KiCad to be installed and properly configured.

### Installing KiCad

Download and install KiCad from [kicad.org](https://www.kicad.org/download/).

### Verifying KiCad Installation

Check that `kicad-cli` is available:

```bash
kicad-cli --version
```

If `kicad-cli` is not found, add KiCad's bin directory to your PATH.

### Symbol Libraries

kAIcad uses KiCad's symbol libraries. Ensure they're properly configured:

1. Open KiCad
2. Go to Preferences → Manage Symbol Libraries
3. Verify that libraries are listed and paths are correct

## Configuring OpenAI API

kAIcad requires an OpenAI API key. See [Configuration](Configuration) for detailed setup instructions.

Quick setup:

```bash
# Set environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Or let kAIcad prompt you on first run
kaicad
```

## Verifying Installation

Test that everything is working:

```bash
# Check version
kaicad --help

# Launch interactive menu
kaicad

# Test CLI
kaicad-cli --help
```

## Troubleshooting Installation

### "command not found: kaicad"

The installation directory is not in your PATH. Try:

```bash
# Find where pip installed it
pip show kaicad

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Or use python -m
python -m kaicad.ui.launcher
```

### "ModuleNotFoundError: No module named 'kaicad'"

kAIcad wasn't installed properly. Try:

```bash
pip install --force-reinstall kaicad
```

### Import Errors

Missing dependencies. Reinstall with:

```bash
pip install --upgrade --force-reinstall kaicad
```

### Permission Errors (Linux/macOS)

Use `--user` flag:

```bash
pip install --user kaicad
```

## Uninstallation

To remove kAIcad:

```bash
pip uninstall kaicad
```

## Next Steps

- ✅ [Get Started with kAIcad](Getting-Started)
- 🔧 [Configure Your Settings](Configuration)
- 📖 [Read the User Guide](User-Guide)
