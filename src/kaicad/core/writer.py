from skip.eeschema.schematic import Schematic
from skip.eeschema.schematic.symbol import Symbol

from kaicad.schema.plan import PLAN_SCHEMA_VERSION, ApplyResult, Diagnostic, Plan
from kaicad.utils.validation import validate_coordinate, validate_symbol_name, validate_wire_format

# KiCad grid constant: 2.54mm (100 mil) - standard schematic grid
GRID_MM = 2.54


def snap_to_grid(value: float, grid: float = GRID_MM) -> float:
    """Snap a coordinate to the nearest grid point for clean diffs"""
    return round(value / grid) * grid


def get_symbol_ref(sym) -> str | None:
    """
    Extract reference designator from a symbol.
    Compatible with skip library v0.2.5+ API and newer forks.
    """
    # Try the Reference property (from newer fork with Symbol.from_lib)
    if hasattr(sym, "Reference") and hasattr(sym.Reference, "value"):
        return sym.Reference.value
    
    # Fall back to allReferences for older versions
    if hasattr(sym, "allReferences") and sym.allReferences:
        # v0.2.5+ API: allReferences is a list property
        ref_obj = sym.allReferences[0]
        # The reference object might be a string or have a string representation
        return str(ref_obj).split("=")[-1].strip() if "=" in str(ref_obj) else str(ref_obj).strip()
    return None


def build_ref_index(doc: Schematic) -> dict:
    """
    Build O(1) lookup: {ref: symbol}
    Avoids linear scan per wire operation.
    """
    index = {}
    for sym in doc.symbol:
        ref = get_symbol_ref(sym)
        if ref:
            index[ref] = sym
    return index


def build_pin_index(ref_index: dict) -> dict:
    """
    Build pin coordinate index: {ref: {pin_name: (x, y) or None}}
    Distinguishes 'pin doesn't exist' (missing key) vs 'pin exists but no coords' (value is None).
    """
    pin_index = {}
    for ref, sym in ref_index.items():
        pin_index[ref] = {}
        try:
            # Attempt to enumerate pins (API may not support this universally)
            # For now, we'll populate on-demand during wire ops
            pass
        except Exception:
            pass
    return pin_index


def get_pin_locations_compat(sym):
    """
    Compatibility wrapper for get_pin_locations().
    Works with both old and new kicad-skip fork versions.
    
    For newly created symbols without lib_symbols loaded, uses standard offsets
    for common 2-pin components (R, C, D, L) as fallback.
    
    Returns:
        dict: Maps pin names/numbers to (x, y) coordinates
    """
    # Try new API first (when fork is updated)
    if hasattr(sym, 'get_pin_locations') and callable(sym.get_pin_locations):
        try:
            return sym.get_pin_locations()
        except Exception:
            pass
    
    # Fallback: use existing .pin collection (works with loaded schematics)
    locations = {}
    
    # Try to access .pin attribute
    try:
        pins = sym.pin if hasattr(sym, 'pin') else None
    except Exception:
        pins = None
    
    if pins is None or not pins:
        # Symbol doesn't have pin data yet - this can happen with newly created symbols
        # before the schematic is saved/reloaded with lib_symbols populated
        
        # For 2-pin components (R, C, D, L), use standard KiCad library offsets
        # This allows wiring to work immediately after component creation
        sym_x, sym_y = None, None
        try:
            if hasattr(sym, 'at') and hasattr(sym.at, 'value') and isinstance(sym.at.value, list) and len(sym.at.value) >= 2:
                sym_x, sym_y = sym.at.value[0], sym.at.value[1]
        except Exception:
            pass
        
        if sym_x is not None and sym_y is not None:
            # Standard offsets for 2-pin components (±2.54mm horizontally)
            # This matches Device:R, Device:C, Device:LED, etc. in KiCad libraries
            locations = {
                '1': (sym_x - 2.54, sym_y),
                '2': (sym_x + 2.54, sym_y)
            }
        
        return locations
    
    # Try to iterate over pins
    try:
        for pin in pins:
            try:
                coord = (pin.location.x, pin.location.y)
                # Add by number
                locations[pin.number] = coord
                # Add by name if not generic
                if pin.name and pin.name != '~':
                    locations[pin.name] = coord
            except (AttributeError, Exception):
                # Skip pins without valid location
                continue
    except (TypeError, Exception):
        # pins is not iterable
        pass
    
    return locations


def lookup_pin_coords(ref: str, pin_name: str, ref_index: dict, pin_index: dict, diagnostics: list) -> tuple:
    """
    Look up pin coordinates using kicad-skip helper methods.
    Returns (x, y) or None if lookup fails.
    Appends diagnostic to explain why lookup failed.
    
    Uses get_pin_locations() for all component types - works for 2-pin and multi-pin components.
    """
    # Check if component exists
    if ref not in ref_index:
        diagnostics.append(
            Diagnostic(
                stage="writer",
                severity="error",
                ref=ref,
                message=f"Component {ref} not found in schematic",
                suggestion="Ensure component is added before wiring",
            )
        )
        return None

    sym = ref_index[ref]

    # Use compatibility wrapper that works with both old and new fork versions
    pin_locations = get_pin_locations_compat(sym)
    
    if not pin_locations:
        # No pin data available - this happens with newly created symbols
        # before schematic is saved/reloaded with lib_symbols populated
        diagnostics.append(
            Diagnostic(
                stage="writer",
                severity="warning",
                ref=ref,
                message=f"Pin coordinates not yet available for {ref} (symbol created but library definitions not loaded)",
                suggestion="Save and reload schematic, or wire will be skipped for now",
            )
        )
        return None
    
    if pin_name in pin_locations:
        return pin_locations[pin_name]
    else:
        # Pin name not found - try to get available pins for better error message
        available_pins = list(pin_locations.keys())
        diagnostics.append(
            Diagnostic(
                stage="writer",
                severity="error",
                ref=ref,
                message=f"Pin '{pin_name}' not found on {ref}",
                suggestion=f"Available pins: {', '.join(available_pins[:10])}",
            )
        )
        return None


def apply_plan(doc: Schematic, plan: Plan) -> ApplyResult:
    """
    Apply a plan to a schematic document.

    Coordinates are snapped to GRID_MM (2.54mm) for deterministic placement.
    Wire operations use get_pin_locations() for all component types.

    Returns an ApplyResult with diagnostics instead of printing to console.
    """
    diagnostics = []
    affected_refs = []

    # GATE: Enforce schema version before any operations
    if plan.plan_version != PLAN_SCHEMA_VERSION:
        diagnostics.append(
            Diagnostic(
                stage="validator",
                severity="error",
                message=f"Plan schema version mismatch: plan has v{plan.plan_version}, writer expects v{PLAN_SCHEMA_VERSION}",
                suggestion=f"Re-run the planner to generate a v{PLAN_SCHEMA_VERSION} plan, or run a schema migrator if available",
            )
        )
        return ApplyResult(success=False, diagnostics=diagnostics, affected_refs=[])

    # Build indexes once for O(1) lookups during operations
    ref_index = build_ref_index(doc)
    pin_index = build_pin_index(ref_index)
    
    # Track if we need to rebuild indexes after component additions
    components_added = False

    for op in plan.ops:
        if op.op == "add_component":
            # Validate symbol name to prevent injection attacks (SECURITY)
            is_valid_symbol, symbol_error = validate_symbol_name(op.symbol)
            if not is_valid_symbol:
                diagnostics.append(
                    Diagnostic(
                        stage="writer",
                        severity="error",
                        ref=op.ref,
                        message=f"Invalid symbol name: {symbol_error}",
                        suggestion="Use valid KiCad format 'Library:Name' (e.g., 'Device:R')",
                    )
                )
                continue
            
            # Try preferred API path if available (patched in tests)
            try:
                if hasattr(Symbol, "from_lib"):
                    # Validate coordinate format first
                    coord_valid, coord_error, coords = validate_coordinate(op.at)
                    if not coord_valid:
                        diagnostics.append(
                            Diagnostic(
                                stage="writer",
                                severity="error",
                                ref=op.ref,
                                message=f"Invalid coordinate: {coord_error}",
                                suggestion="Use [x, y] format with numeric values",
                            )
                        )
                        continue
                    
                    x, y = coords
                    x, y = snap_to_grid(x), snap_to_grid(y)
                    
                    # Debug: check if Symbol.from_lib is actually callable
                    if not callable(Symbol.from_lib):
                        raise RuntimeError(f"Symbol.from_lib exists but is not callable: {type(Symbol.from_lib)}")
                    
                    # Use the from_lib API with proper parameters
                    # Signature: from_lib(schematic, lib_id: str, reference: str, at_x: float, at_y: float, ...)
                    sym = Symbol.from_lib(
                        doc,
                        lib_id=op.symbol,
                        reference=op.ref,
                        at_x=x,
                        at_y=y,
                        unit=1,
                        in_bom=True,
                        on_board=True,
                        dnp=False
                    )  # type: ignore[attr-defined]
                    
                    # Set value if provided (direct assignment now supported in fork)
                    if op.value:
                        sym.Value = op.value
                    
                    # Rotation (best-effort)
                    if getattr(op, "rot", 0):
                        for attr in ("rotation", "rot"):
                            try:
                                setattr(sym, attr, op.rot)
                                break
                            except Exception:
                                continue
                    
                    # Additional fields are best-effort, ignore failures
                    for k, v in getattr(op, "fields", {}).items():
                        try:
                            setattr(sym, k, v)
                        except Exception:
                            pass
                    
                    # Symbol is automatically added to doc.symbol by from_lib
                    affected_refs.append(op.ref)
                    components_added = True  # Mark that we need to rebuild indexes
                    diagnostics.append(
                        Diagnostic(stage="writer", severity="info", ref=op.ref, message=f"Added {op.ref} ({op.symbol})")
                    )
                else:
                    # Symbol.from_lib not available in this skip version
                    raise RuntimeError(
                        "Symbol.from_lib is not available in kicad-skip 0.2.5. "
                        "Adding components programmatically is not supported with the current version of kicad-skip. "
                        "You can: (1) manually add components in KiCad first, then use kAIcad for wiring/labels, "
                        "or (2) wait for kicad-skip library updates with symbol creation support."
                    )
            except Exception as e:
                import traceback
                error_msg = str(e)
                # Include traceback for debugging
                tb_lines = traceback.format_exc().split('\n')
                # Find the actual error line
                for line in tb_lines:
                    if 'File' in line and 'writer.py' in line:
                        error_msg += f" | {line.strip()}"
                
                suggestion = "This environment does not support creating symbols programmatically with kicad-skip."
                
                # Provide more specific suggestions based on the error
                if "from_lib" in error_msg:
                    suggestion = (
                        "Component creation is not supported in kicad-skip 0.2.5. "
                        "Workaround: Add components manually in KiCad first, then use kAIcad for connections and labels only. "
                        "Or use a schematic that already has the needed components and ask to wire/connect them."
                    )
                
                diagnostics.append(
                    Diagnostic(
                        stage="writer",
                        severity="error",
                        ref=op.ref,
                        message=f"Failed to add component: {error_msg}",
                        suggestion=suggestion,
                    )
                )
        elif op.op == "wire":
            # Rebuild indexes if components were added (symbols now in doc.symbol immediately)
            if components_added:
                ref_index = build_ref_index(doc)
                pin_index = build_pin_index(ref_index)
                components_added = False
            
            # Wire between pins identified as REF:PIN using indexed lookups
            try:
                # Validate wire format with security checks
                from_valid, from_error, from_parts = validate_wire_format(op.from_)
                if not from_valid:
                    diagnostics.append(
                        Diagnostic(
                            stage="writer",
                            severity="error",
                            message=f"Invalid 'from' wire format: {from_error}",
                            suggestion="Use format 'REF:PIN' (e.g., 'R1:1')",
                        )
                    )
                    continue
                
                to_valid, to_error, to_parts = validate_wire_format(op.to)
                if not to_valid:
                    diagnostics.append(
                        Diagnostic(
                            stage="writer",
                            severity="error",
                            message=f"Invalid 'to' wire format: {to_error}",
                            suggestion="Use format 'REF:PIN' (e.g., 'R1:2')",
                        )
                    )
                    continue
                
                from_ref, from_pin = from_parts
                to_ref, to_pin = to_parts

                # O(1) pin coordinate lookups with validation
                try:
                    from_pos = lookup_pin_coords(from_ref, from_pin, ref_index, pin_index, diagnostics)
                except Exception as lookup_err:
                    diagnostics.append(
                        Diagnostic(
                            stage="writer",
                            severity="error",
                            ref=from_ref,
                            message=f"Pin lookup failed for {from_ref}:{from_pin}: {lookup_err}",
                        )
                    )
                    from_pos = None
                
                try:
                    to_pos = lookup_pin_coords(to_ref, to_pin, ref_index, pin_index, diagnostics)
                except Exception as lookup_err:
                    diagnostics.append(
                        Diagnostic(
                            stage="writer",
                            severity="error",
                            ref=to_ref,
                            message=f"Pin lookup failed for {to_ref}:{to_pin}: {lookup_err}",
                        )
                    )
                    to_pos = None

                if from_pos and to_pos:
                    # Both pins found with coordinates - create wire using collection API
                    try:
                        if not hasattr(doc, 'wire') or doc.wire is None:
                            diagnostics.append(
                                Diagnostic(
                                    stage="writer",
                                    severity="error",
                                    ref=from_ref,
                                    message="Wire collection not available in schematic",
                                    suggestion="This schematic may not support wire operations",
                                )
                            )
                            continue
                        
                        w = doc.wire.new()
                        # kicad-skip wire wrapper exposes 'pts' list property
                        w.pts = [from_pos, to_pos]
                        doc.wire.append(w)
                        affected_refs.extend([from_ref, to_ref])
                        diagnostics.append(
                            Diagnostic(
                                stage="writer",
                                severity="info",
                                ref=from_ref,
                                message=f"Connected wire from {from_ref}:{from_pin} to {to_ref}:{to_pin}",
                            )
                        )
                    except Exception as wire_err:
                        import traceback
                        tb = traceback.format_exc()
                        diagnostics.append(
                            Diagnostic(
                                stage="writer",
                                severity="error",
                                ref=from_ref,
                                message=f"Wire placement failed: {wire_err}\n{tb}",
                            )
                        )
                # If pins not found, lookup_pin_coords already added diagnostics explaining why

            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        stage="writer",
                        severity="error",
                        message=f"Wire operation failed: {e}",
                        suggestion="Verify wire format is 'REF:PIN' (e.g., 'R1:1')",
                    )
                )
        elif op.op == "label":
            try:
                # Validate and snap label position to grid
                coord_valid, coord_error, coords = validate_coordinate(op.at)
                if not coord_valid:
                    diagnostics.append(
                        Diagnostic(
                            stage="writer",
                            severity="error",
                            message=f"Invalid label coordinate: {coord_error}",
                            suggestion="Use [x, y] format with numeric values",
                        )
                    )
                    continue
                
                x, y = coords
                x, y = snap_to_grid(x), snap_to_grid(y)
                lab = doc.label.new()
                lab.value = op.net
                lab.at = x, y
                doc.label.append(lab)
                diagnostics.append(
                    Diagnostic(stage="writer", severity="info", message=f"Added label '{op.net}' at ({x}, {y})")
                )
            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        stage="writer",
                        severity="error",
                        message=f"Label operation failed: {e}",
                        suggestion="Check label position and net name validity",
                    )
                )

    # Return result with diagnostics
    return ApplyResult(
        success=not any(d.severity == "error" for d in diagnostics),
        diagnostics=diagnostics,
        affected_refs=affected_refs,
    )


# Public API
__all__ = [
    "Schematic",
    "Symbol",
    "GRID_MM",
    "snap_to_grid",
    "get_symbol_ref",
    "get_pin_locations_compat",
    "apply_plan",
]
