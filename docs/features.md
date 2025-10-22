# Features

## Component and Net Inspection

The chat interface supports detailed inspection of components and nets from your schematic.

### Examples

- What is C2?
- Connect U1 pin 3 to R5 pin 2
- Show me net "VCC"
- Inspect hierarchical sheets

### Details

- **Component fields**: value, symbol, footprint, properties, connections
- **Net fields**: components, pin numbers/names, connection count

### Tips

- References are case-insensitive (c2, C2)
- Use quotes around net names: "VCC"
- Ask about multiple components at once

### Under the Hood

- `inspector.py` provides `inspect_schematic`, `inspect_net_connections`, `get_component_connections`, and more
- The web UI parses references and nets, enriches the prompt, and returns structured responses

## Hierarchical Sheets

Support for multi-sheet schematics with automatic sub-sheet discovery.

### How to Use (Web UI)

1. Set project path
2. Click **Detect**
3. Ask: "Show me the hierarchical sheets" or "Inspect the hierarchy"

### Data Structure

```json
{
  "root": { 
    "components": [...],
    "nets": [...],
    "hierarchy": [...],
    "stats": {...}
  },
  "subsheets": { 
    "SheetName": {
      "components": [...],
      "nets": [...],
      "stats": {...}
    }
  }
}
```

### Benefits

- Complete visibility across the design
- AI-aware hierarchy for better answers
- Automatic discovery of sheet dependencies
