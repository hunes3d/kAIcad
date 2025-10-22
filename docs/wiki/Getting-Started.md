# Getting Started with kAIcad

This guide will help you get kAIcad up and running in minutes.

## Prerequisites

Before installing kAIcad, ensure you have:

- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
- **KiCad 7.0 or higher** - [Download KiCad](https://www.kicad.org/download/)
- **OpenAI API Key** - [Get an API Key](https://platform.openai.com/api-keys)

## Installation

### Quick Install (Recommended)

```bash
pip install kaicad
```

### From Source

```bash
git clone https://github.com/hunes3d/kAIcad.git
cd kAIcad
pip install -e .
```

## Configuration

### 1. Set Up Your API Key

kAIcad needs an OpenAI API key to function. You can configure it in several ways:

#### Option A: Environment Variable (Recommended)

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-your-api-key-here"

# macOS/Linux
export OPENAI_API_KEY="sk-your-api-key-here"
```

#### Option B: Configuration File

Create a `.env` file in your project directory:

```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

#### Option C: System Keychain (Most Secure)

The first time you run kAIcad, it will prompt you for your API key and store it securely in your system keychain.

### 2. Choose Your Interface

kAIcad offers three interfaces:

#### Interactive Launcher

```bash
kaicad
```

This launches an interactive menu where you can choose your preferred interface.

#### Command-Line Interface (CLI)

```bash
kaicad-cli
```

Best for scripting and automation.

#### Desktop GUI

```bash
kaicad --desktop
```

Rich graphical interface with file browser and live preview.

#### Web Interface

```bash
kaicad --web
```

Browser-based interface, accessible at `http://localhost:5000`.

## First Steps

### 1. Open a KiCad Project

Launch kAIcad with your preferred interface and open an existing `.kicad_sch` file.

### 2. Try a Simple Command

Start with something basic:

```
Add an LED
```

kAIcad will:
- Search for LED symbols in your KiCad libraries
- Place the LED in your schematic
- Show you what it plans to do before applying changes

### 3. Review and Apply

- Review the proposed changes
- Confirm to apply them
- Your schematic is updated!

## Next Steps

- 📖 Read the [User Guide](User-Guide) for detailed usage instructions
- ✨ Explore [Features](Features) to see what kAIcad can do
- 🔧 Configure [Advanced Settings](Configuration)
- 🐛 Check [Troubleshooting](Troubleshooting) if you run into issues

## Quick Tips

- 🎯 **Be Specific**: "Add a 10kΩ resistor" works better than just "Add resistor"
- 🔍 **Check Libraries**: Make sure KiCad's symbol libraries are properly configured
- 💾 **Save Often**: kAIcad modifies your schematic files directly
- 🔄 **Use Git**: Version control is your friend when experimenting

## Common Issues

### "Module 'kaicad' not found"

Make sure you installed kAIcad:
```bash
pip install kaicad
```

### "No OpenAI API key found"

Set your API key using one of the methods above.

### "Symbol not found"

Ensure KiCad's symbol libraries are properly configured. Check KiCad's Preferences → Manage Symbol Libraries.

## Need Help?

- 💬 [Ask in Discussions](https://github.com/hunes3d/kAIcad/discussions)
- 🐞 [Report a Bug](https://github.com/hunes3d/kAIcad/issues)
- 📖 [Read the Full Documentation](https://github.com/hunes3d/kAIcad/tree/main/docs)
