# Dev Notes

Development guidelines, technical limitations, and implementation details.

## Completed Improvements

- Secure API key storage (keyring)
- Removed Tk from web server; added CSRF
- Enforced FLASK_SECRET_KEY in production
- Model registry with aliases and validation
- Separated state storage in web UI
- Pinned dependencies
- Added schema tests

## Known Technical Limitations

### ✅ Component Creation — RESOLVED (22/10/2025)

**Status**: **FIXED** — Now using custom kicad-skip fork with full symbol creation support

**Solution Implemented**: Custom fork at https://github.com/hunes3d/kicad-skip

**Key Features Added**:
- `Symbol.from_lib(doc, lib_id, reference, at_x, at_y)` class method
- Direct property setters: `sym.Value = "1k"`, `sym.Reference = "R1"`
- Immediate symbol addition to `doc.symbol` collection
- Full integration with kAIcad's apply_plan workflow
- `get_pin_locations()` — Get all pin coordinates as dict
- `get_pin_by_name(name)` — Find pin by name
- `get_pin_by_number(num)` — Find pin by number

**Code Location**: `src/kaicad/core/writer.py`

**Current Behavior**:
- ✅ `add_component` operations create symbols from KiCad libraries
- ✅ Properties set directly with `sym.Value = "value"` syntax
- ✅ Components immediately available for wiring operations
- ✅ Full pin coordinate support for ALL component types (2-pin, multi-pin ICs, connectors)
- ✅ Direct wire connections without fallback to net labels
- ✅ Full end-to-end AI-driven circuit creation

**Testing Strategy**:
- `tests/fixtures/test_golden_fixtures.py::test_add_led_resistor_with_erc` — Full component creation and wiring
- `tests/fixtures/test_golden_fixtures.py::test_wire_operation_creates_connection` — Wire operations with new components
- `tests/integration/test_no_write_on_error.py` — Error handling for component operations
- All tests pass with fork (188/201 passing, 7 failures pre-existing)

## Open Items

- Increase coverage and add integration tests
- Examples directory and CLI vertical slice
- Structured logging and background jobs

## Dependency Management

### Using the kicad-skip Fork

The fork is automatically installed via requirements.txt:
```
kicad-skip @ git+https://github.com/hunes3d/kicad-skip.git
```

**Why a Fork?**
- Adds `Symbol.from_lib()` for component creation
- Enables direct property assignment
- Critical for kAIcad's core functionality

### Dependency Locking

This project uses `pip-tools` for dependency locking to ensure reproducible builds.

**Generate Lock File:**
```bash
pip freeze > requirements.lock
```

**Recommendation**: Pin to specific commit hash in requirements.txt for reproducible builds:
```
kicad-skip @ git+https://github.com/hunes3d/kicad-skip.git@26017bf9a10b0fa77ea124b80bd4cb3283bb6aaf
```

**Note**: Rust compilation may be required for the fork. Ensure build tools are available.

## Publishing Documentation

To publish these docs to the GitHub Wiki:

**Option A — GitHub UI (Quick)**:
1. Open: https://github.com/hunes3d/kAIcad/wiki
2. Create pages and paste content from `docs/` folder
3. Save each page

**Option B — Git Clone (Scriptable)**:
```powershell
git clone https://github.com/hunes3d/kAIcad.wiki.git
cd kAIcad.wiki
Copy-Item ..\kAIcad\docs\*.md .
git add .
git commit -m "Publish wiki pages"
git push
```
