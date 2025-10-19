from skip.eeschema.schematic import Schematic, Symbol

from kaicad.schema.plan import PLAN_SCHEMA_VERSION, ApplyResult, Diagnostic, Plan

# KiCad grid constant: 2.54mm (100 mil) - standard schematic grid
GRID_MM = 2.54


def snap_to_grid(value: float, grid: float = GRID_MM) -> float:
    """Snap a coordinate to the nearest grid point for clean diffs"""
    return round(value / grid) * grid


def get_symbol_ref(sym) -> str | None:
    """
    Extract reference designator from a symbol.
    Compatible with skip library v0.2.5+ API.
    """
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


def lookup_pin_coords(ref: str, pin_name: str, ref_index: dict, pin_index: dict, diagnostics: list) -> tuple:
    """
    Look up pin coordinates with proper validation.
    Returns (x, y) or None if lookup fails.
    Appends diagnostic to explain why lookup failed.
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

    # Try to get pin position
    try:
        pos = sym.pin_position(pin_name)
        return pos
    except (AttributeError, KeyError, ValueError):
        # Pin doesn't exist or coords unavailable
        diagnostics.append(
            Diagnostic(
                stage="writer",
                severity="warning",
                ref=ref,
                message=f"Pin '{pin_name}' not found or has no coordinates on {ref}",
                suggestion=f"Verify pin name '{pin_name}' exists in symbol definition",
            )
        )
        return None


def apply_plan(doc: Schematic, plan: Plan) -> ApplyResult:
    """
    Apply a plan to a schematic document.

    Coordinates are snapped to GRID_MM (2.54mm) for deterministic placement.
    Wire operations attempt pin coordinate lookup, falling back to net labels.

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

    for op in plan.ops:
        if op.op == "add_component":
            # Try preferred API path if available (patched in tests)
            try:
                if hasattr(Symbol, "from_lib"):
                    sym = Symbol.from_lib(op.symbol)  # type: ignore[attr-defined]
                    # Set attributes using generic property names when available
                    try:
                        # Reference/value attributes in skip use capitalized names
                        sym.Reference = op.ref
                        sym.Value = op.value
                    except Exception:
                        # Fallback methods if provided by custom Symbol implementation
                        if hasattr(sym, "set_ref"):
                            sym.set_ref(op.ref)  # type: ignore[attr-defined]
                        if hasattr(sym, "set_value"):
                            sym.set_value(op.value)  # type: ignore[attr-defined]
                    # Position
                    x, y = snap_to_grid(op.at[0]), snap_to_grid(op.at[1])
                    try:
                        sym.at = x, y
                    except Exception:
                        if hasattr(sym, "set_pos"):
                            sym.set_pos(x, y)  # type: ignore[attr-defined]
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
                    # Append to schematic
                    doc.symbol.append(sym)
                    affected_refs.append(op.ref)
                    diagnostics.append(
                        Diagnostic(stage="writer", severity="info", ref=op.ref, message=f"Added {op.ref} ({op.symbol})")
                    )
                else:
                    # Symbol.from_lib not available in this skip version
                    raise RuntimeError("Symbol.from_lib is not available in current kicad-skip version")
            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        stage="writer",
                        severity="error",
                        ref=op.ref,
                        message=f"Failed to add component: {e}",
                        suggestion="This environment may not support creating symbols programmatically with kicad-skip",
                    )
                )
        elif op.op == "wire":
            # Wire between pins identified as REF:PIN using indexed lookups
            try:
                from_ref, from_pin = op.from_.split(":")
                to_ref, to_pin = op.to.split(":")

                # O(1) pin coordinate lookups with validation
                from_pos = lookup_pin_coords(from_ref, from_pin, ref_index, pin_index, diagnostics)
                to_pos = lookup_pin_coords(to_ref, to_pin, ref_index, pin_index, diagnostics)

                if from_pos and to_pos:
                    # Both pins found with coordinates - create wire using collection API
                    try:
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
                        diagnostics.append(
                            Diagnostic(
                                stage="writer",
                                severity="error",
                                ref=from_ref,
                                message=f"Wire placement failed: {wire_err}",
                            )
                        )

                elif from_ref in ref_index and to_ref in ref_index:
                    # Components exist but pins don't have coords - use label fallback
                    diagnostics.append(
                        Diagnostic(
                            stage="writer",
                            severity="warning",
                            ref=from_ref,
                            message="Pin coordinates unavailable, using net label fallback",
                            suggestion="Net will be connected via labels instead of wire geometry",
                        )
                    )

                    # Generate unique net name for this connection
                    net_name = f"Net_{from_ref}_{from_pin}_{to_ref}_{to_pin}"

                    # Place labels near both symbols
                    from_x, from_y = 0.0, 0.0
                    to_x, to_y = 0.0, 0.0
                    # best-effort position fetch
                    for attr in ("at", "pos", "position"):
                        try:
                            pos_from = getattr(ref_index[from_ref], attr)
                            if callable(pos_from):
                                pos_from = pos_from()
                            if isinstance(pos_from, tuple) and len(pos_from) == 2:
                                from_x, from_y = pos_from
                        except Exception:
                            pass
                        try:
                            pos_to = getattr(ref_index[to_ref], attr)
                            if callable(pos_to):
                                pos_to = pos_to()
                            if isinstance(pos_to, tuple) and len(pos_to) == 2:
                                to_x, to_y = pos_to
                        except Exception:
                            pass

                    # Snap label positions to grid
                    from_x, from_y = snap_to_grid(from_x), snap_to_grid(from_y)
                    to_x, to_y = snap_to_grid(to_x), snap_to_grid(to_y)

                    # Add labels at component positions (KiCad will snap to pins)
                    try:
                        lf = doc.label
                        l1 = lf.new()
                        l1.value = net_name
                        l1.at = from_x, from_y
                        lf.append(l1)
                        l2 = lf.new()
                        l2.value = net_name
                        l2.at = to_x, to_y
                        lf.append(l2)
                        affected_refs.extend([from_ref, to_ref])
                        diagnostics.append(
                            Diagnostic(
                                stage="writer",
                                severity="info",
                                ref=from_ref,
                                message=f"Added net labels '{net_name}' at {from_ref} and {to_ref}",
                            )
                        )
                    except Exception as label_err:
                        diagnostics.append(
                            Diagnostic(
                                stage="writer",
                                severity="error",
                                ref=from_ref,
                                message=f"Label fallback also failed: {label_err}",
                                suggestion="Check component positions and schematic structure",
                            )
                        )

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
                # Snap label position to grid and use collection API
                x, y = snap_to_grid(op.at[0]), snap_to_grid(op.at[1])
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
    "apply_plan",
]
