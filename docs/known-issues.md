# Known Issues & Workarounds# Known Issues & Workarounds



This document lists current known limitations and provides practical workarounds.This document lists current known limitations and provides practical workarounds.



## ✅ Component Creation & Pin Coordinates Now Fully Supported!## ✅ Component Creation Now Supported!



**Status**: **RESOLVED** - As of October 2025, kAIcad uses a custom fork of kicad-skip with complete component creation and pin coordinate support.**Status**: **RESOLVED** - As of 22/10/2025, kAIcad uses a custom fork of kicad-skip that supports component creation.



**What Now Works**:**What Now Works**:

- ✅ `add_component` operations create symbols directly- ✅ `add_component` operations create symbols directly

- ✅ AI requests like "Add LED and resistor" work end-to-end  - ✅ AI requests like "Add LED and resistor" work end-to-end  

- ✅ Full programmatic circuit creation from scratch- ✅ Full programmatic circuit creation from scratch

- ✅ Direct property assignment (`sym.Value = "1k"`)- ✅ Direct property assignment (`sym.Value = "1k"`)

- ✅ **Full pin coordinate support for ALL component types**

- ✅ **Direct wiring for 2-pin AND multi-pin components (ICs, connectors, etc.)****Fork Details**:

- Repository: https://github.com/hunes3d/kicad-skip

**Fork Details**:- Key Features:

- Repository: https://github.com/hunes3d/kicad-skip  - `Symbol.from_lib(doc, lib_id, reference, at_x, at_y)` method

- Key Features:  - Immediate symbol addition to document collection

  - `Symbol.from_lib(doc, lib_id, reference, at_x, at_y)` method  - Direct property setters for Value, Reference, etc.

  - Immediate symbol addition to document collection

  - Direct property setters for Value, Reference, etc.**Example - Now Works**:

  - `get_pin_locations()` — Get all pin coordinates as dict```python

  - `get_pin_by_name(name)` / `get_pin_by_number(num)` — Find specific pinsfrom kaicad.core.planner import plan_from_prompt

from kaicad.core.writer import apply_plan

**Example - Now Works**:

```python# This creates components AND wires them!

from kaicad.core.planner import plan_from_promptplan = plan_from_prompt("Add LED and resistor in series")

from kaicad.core.writer import apply_planresult = apply_plan(doc, plan)

# ✅ Components created, wired, and ready for ERC

# This creates components AND wires them - even multi-pin ICs!```

plan = plan_from_prompt("Add voltage regulator with input/output capacitors")

result = apply_plan(doc, plan)## Current Limitations

# ✅ Components created, wired with direct connections, ready for ERC

```### Pin Coordinates for Multi-Pin Components



## Current Limitations**Issue**: Wire operations use standard pin offsets (pins 1 & 2 only)



### Large Schematic Performance**Affected Components**:

- ICs with >2 pins (microcontrollers, op-amps, etc.)

**Issue**: Inspection of very large schematics (1000+ components) may be slow- Connectors with many pins

- Complex symbols

**Impact**: Initial inspection takes longer than usual

**Current Support**:

**Workaround**: None needed - operations complete successfully, just slower- ✅ 2-pin components (resistors, capacitors, LEDs): Fully supported

- ⚠️ Multi-pin components: Pin coordinates unavailable

## Reporting Issues

**Workaround**:

Found a new issue? Please report it at:For multi-pin components, use net labels instead of direct wires:

https://github.com/hunes3d/kAIcad/issues```python

# Instead of: wire(from_="U1:5", to="R1:1")  # Won't work for U1

For kicad-skip fork issues:# Use: label at U1 pin 5 and R1 pin 1 with same net name

https://github.com/hunes3d/kicad-skip/issuesadd_label(text="RESET", at=[x, y])  # Near U1 pin 5

add_label(text="RESET", at=[x2, y2])  # Near R1 pin 1

Include:```

- Error message (full text)

- What you were trying to do**Future Resolution**: 

- KiCad version (`kicad-cli --version`)- Fork may add library metadata lookup for pin positions

- Python version (`python --version`)- Or extend standard offsets to cover common IC pinouts

- kAIcad version (from README)

### Large Schematic Performance

**Issue**: Inspection of very large schematics (1000+ components) may be slow

**Impact**: Initial inspection takes longer than usual

**Workaround**: None needed - operations complete successfully, just slower

## Reporting Issues

Found a new issue? Please report it at:
https://github.com/hunes3d/kAIcad/issues

For kicad-skip fork issues:
https://github.com/hunes3d/kicad-skip/issues

Include:
- Error message (full text)
- What you were trying to do
- KiCad version (`kicad-cli --version`)
- Python version (`python --version`)
- kAIcad version (from README)
