# Features

kAIcad brings AI-powered intelligence to your KiCad workflow. Here's what makes it powerful.

## 🎯 Core Capabilities

### Natural Language Circuit Design

Describe what you want in plain English:

```
"Add a voltage divider with 10kΩ and 5kΩ resistors"
"Connect the LED cathode to ground through a 330Ω resistor"
"Place a decoupling capacitor near the microcontroller"
```

The AI understands context, relationships, and electronic design patterns.

### Smart Symbol Search

kAIcad automatically searches your KiCad symbol libraries:

- Fuzzy matching for component names
- Understanding of common abbreviations (LED, MCU, etc.)
- Support for specific values and packages
- Fallback to generic symbols when needed

### Intelligent Placement

Components are placed logically:

- Respects existing layout
- Maintains reasonable spacing
- Groups related components
- Avoids overlapping existing elements

### Automatic Wiring

kAIcad can connect components intelligently:

- Point-to-point connections
- Bus connections
- Net label creation
- Power and ground connections

## 🖥️ Multiple Interfaces

### Interactive Launcher

```bash
kaicad
```

Choose your interface interactively:
- ASCII banner with project info
- Numbered menu (1=CLI, 2=Desktop, 3=Web)
- Quick launch with `--cli`, `--desktop`, or `--web` flags

### Command-Line Interface (CLI)

```bash
kaicad-cli "Add an LED"
```

Features:
- Direct command execution
- Perfect for scripting
- Minimal UI overhead
- Batch processing support

### Desktop GUI

```bash
kaicad --desktop
```

Features:
- Native desktop application
- File browser for projects
- Live schematic preview
- Recent projects list
- Comfortable for extended sessions

### Web Interface

```bash
kaicad --web
```

Features:
- Browser-based (http://localhost:5000)
- Project management
- Interactive chat
- Component inspection
- Multi-session support
- Great for remote access

## 🔍 Advanced Inspection

### Component Inspection

Ask about any component:

```
"What is C2?"
"Show me U1's connections"
"List all resistors"
```

Get detailed information:
- Value and parameters
- Symbol and footprint
- Pin connections
- Net assignments
- Component properties

### Net Analysis

Understand your connections:

```
"Show me the VCC net"
"What's connected to U1 pin 3?"
"List all power nets"
```

Features:
- Net trace visualization
- Connection counts
- Pin names and numbers
- Cross-sheet connections

### Hierarchical Sheets

Full support for multi-sheet designs:

```
"Show me the hierarchical sheets"
"What's in the power supply sheet?"
```

Capabilities:
- Automatic sub-sheet discovery
- Cross-sheet net tracking
- Hierarchical label handling
- Complete design visibility

## 🛡️ Safety Features

### Pre-Apply Validation

Every change is validated before being applied:
- Symbol existence checks
- Pin name validation
- Connection feasibility
- Placement collision detection

### Plan Preview

Review what kAIcad will do before it happens:
- See all proposed changes
- Understand the reasoning
- Approve or reject
- Modify and retry

### Error Recovery

Comprehensive error handling:
- Clear error messages
- Suggestions for fixes
- Graceful degradation
- Safe fallbacks

### Version Control Friendly

Works great with Git:
- Predictable file modifications
- Easy to diff changes
- Simple rollback with `git reset`
- Atomic operations

## 🔧 Configuration Options

### AI Model Selection

Choose your preferred OpenAI model:
- `gpt-4o` - Most capable, best for complex designs
- `gpt-4o-mini` - Fast and cost-effective (default)
- `gpt-3.5-turbo` - Budget option

### Custom Prompts

Fine-tune the AI's behavior:
- System prompt customization
- Context injection
- Response format control
- Temperature and top-p settings

### Symbol Library Paths

Configure custom library locations:
- Project-specific libraries
- Personal component collections
- Company standard libraries

### Output Options

Control how kAIcad behaves:
- Verbosity levels
- JSON output for automation
- Preview before apply
- Auto-backup before changes

## 🚀 Advanced Features

### Batch Processing

Process multiple commands:

```python
from kaicad.core.planner import plan_from_prompt
from kaicad.core.writer import apply_plan

for command in commands:
    plan = plan_from_prompt(command)
    apply_plan(schematic, plan)
```

### Scripting Support

Use kAIcad in your own scripts:

```python
from kaicad import Schematic, Designer

sch = Schematic.from_file("circuit.kicad_sch")
designer = Designer(sch)

designer.add_component("LED", position=(100, 100))
designer.add_resistor("330Ω", position=(120, 100))
designer.connect("LED:A", "R1:1")

sch.save()
```

### API Access

Full programmatic access:
- Component manipulation
- Wire routing
- Net management
- Property editing

### Export Integration

Works with KiCad CLI tools:
- ERC (Electrical Rules Check)
- Netlist generation
- PDF export
- BOM creation

## 🎨 Planned Features

Coming soon:

- [ ] PCB layout support
- [ ] Component value optimization
- [ ] Schematic beautification
- [ ] Auto-routing assistance
- [ ] Design rule checking
- [ ] Bill of materials generation
- [ ] Part sourcing integration
- [ ] Simulation setup

See the [Roadmap](https://github.com/hunes3d/kAIcad/blob/main/docs/roadmap.md) for more details.

## 💡 Use Cases

### Rapid Prototyping

Quickly sketch out circuit ideas:
- "Add a 555 timer circuit"
- "Create a power supply with LM7805"
- "Add debug LEDs to all GPIO pins"

### Learning Electronics

Great for students and hobbyists:
- Natural language makes it approachable
- Learn by doing
- See best practices in action
- Understand connections

### Design Automation

Automate repetitive tasks:
- Standard circuit blocks
- Connector pinouts
- Power distribution
- Test points

### Documentation

Generate and update designs:
- Quick modifications
- Design exploration
- Alternative implementations
- Version comparisons

## 🔗 Integration

### KiCad Integration

Deep integration with KiCad:
- Uses native file formats
- Respects KiCad settings
- Works with KiCad libraries
- Compatible with KiCad versions

### Version Control

Git-friendly workflow:
- Text-based file format
- Meaningful diffs
- Easy rollback
- Collaborative design

### CI/CD

Automate your workflow:
- Automated schematic generation
- Design validation
- Documentation updates
- Test fixture creation

## 📊 Performance

kAIcad is designed to be fast and efficient:

- **Fast Symbol Search**: Indexed library access
- **Minimal Overhead**: Direct file manipulation
- **Cached Results**: Reuse AI responses when appropriate
- **Incremental Updates**: Only change what's needed

## 🔒 Security

Your designs stay private:

- API keys stored in system keychain
- Local processing where possible
- No design data sent to third parties
- OpenAI API communication encrypted

## Need Help?

- 📖 [User Guide](User-Guide) for detailed usage
- 🔧 [Configuration](Configuration) for setup options
- 🐛 [Troubleshooting](Troubleshooting) for common issues
