# Welcome to kAIcad Wiki

**kAIcad** is an AI-powered assistant for KiCad electronic design automation. It allows you to create and modify KiCad schematics using natural language commands.

## Quick Links

- 🚀 [Getting Started](Getting-Started)
- 📦 [Installation Guide](Installation)
- ✨ [Features](Features)
- 🔧 [Configuration](Configuration)
- 📖 [User Guide](User-Guide)
- 🐛 [Troubleshooting](Troubleshooting)
- 🤝 [Contributing](Contributing)

## What is kAIcad?

kAIcad bridges the gap between natural language and electronic circuit design. Simply describe what you want to add to your schematic, and kAIcad will:

- Parse your natural language prompt
- Generate a structured plan
- Apply changes to your KiCad schematic
- Validate the results

## Key Features

- 🗣️ **Natural Language Interface** - Describe circuits in plain English
- 🎨 **Multiple UI Options** - CLI, Desktop GUI, and Web interface
- 🔍 **Smart Symbol Search** - Automatically finds components in KiCad libraries
- ✅ **Validation** - Checks for errors before applying changes
- 🔄 **Undo Support** - Safe experimentation with easy rollback
- 🤖 **AI-Powered** - Uses OpenAI GPT models for intelligent planning

## Getting Started

```bash
# Install kAIcad
pip install kaicad

# Launch the interactive launcher
kaicad

# Or use directly
kaicad --cli      # Command-line interface
kaicad --desktop  # Desktop GUI
kaicad --web      # Web interface
```

## Example Usage

```bash
# Using the CLI
kaicad-cli "Add an LED and current-limiting resistor to my circuit"

# The AI will:
# 1. Analyze your schematic
# 2. Find appropriate LED and resistor symbols
# 3. Place them in logical positions
# 4. Connect them with wires
# 5. Save the updated schematic
```

## Community

- 💬 [Discussions](https://github.com/hunes3d/kAIcad/discussions)
- 🐞 [Report Issues](https://github.com/hunes3d/kAIcad/issues)
- ⭐ [Star on GitHub](https://github.com/hunes3d/kAIcad)

## License

kAIcad is open source software licensed under the AGPL-3.0 License.
