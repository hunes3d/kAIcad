# Roadmap

Future plans and development priorities for kAIcad.

## Recent Achievements (2025)

### ✅ Component Creation & Pin Coordinates Support
- Full symbol creation from KiCad libraries via custom kicad-skip fork
- Direct property assignment (`sym.Value = "1k"`)
- **Full pin coordinate support for ALL component types**
- **Direct wiring for multi-pin ICs, connectors, and complex symbols**
- `get_pin_locations()`, `get_pin_by_name()`, `get_pin_by_number()` methods
- End-to-end AI-driven circuit creation without limitations

**Example**: "Add voltage regulator with capacitors" now works completely, with direct wiring!

See [dev-notes.md](dev-notes.md) for technical details.

## Near-Term Plans
- Increase test coverage to 95%+
- More integration tests for complex workflows
- Performance benchmarks for large schematics

### Documentation & Examples
- Example projects directory
- Tutorial videos
- CLI usage guide
- API reference documentation

## Long-Term Vision

### Local LLM Support
- Ollama integration
- llama.cpp backend
- Privacy-focused offline mode
- Fine-tuned models for EDA

### Advanced Features
- Plugin system for custom operations
- Visual diff viewer for schematic changes
- Advanced placement algorithms (minimize wire length, thermal considerations)
- PCB layout integration
- Multi-board system design

### Ecosystem Integration
- KiCad plugin/action for direct integration
- VS Code extension
- GitHub Actions for automated design validation
- Integration with simulation tools (SPICE, Verilog)

## Contributing

See development priorities and how to contribute at:
https://github.com/hunes3d/kAIcad/issues
