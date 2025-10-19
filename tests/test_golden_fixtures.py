"""Golden fixture tests for kAIcad - test full pipeline with real KiCad files"""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from skip.eeschema import schematic as sch  # type: ignore

from sidecar.schema import PLAN_SCHEMA_VERSION, AddComponent, Label, Plan, Wire
from sidecar.writer_skip import apply_plan

# Minimal valid KiCad 9.0 schematic template
MINIMAL_SCHEMATIC_TEMPLATE = """(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "12345678-1234-1234-1234-123456789abc")
  (paper "A4")
  (lib_symbols
    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "R res resistor" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_fp_filters" "R_*" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )
    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 1.016) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LED" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "LED diode" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_fp_filters" "LED*" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )
  )
  (junction (at 100 50) (diameter 0) (color 0 0 0 0) (uuid "11111111-1111-1111-1111-111111111111"))
  (wire (pts (xy 95 50) (xy 105 50)) (stroke (width 0) (type default)) (uuid "22222222-2222-2222-2222-222222222222"))
  (symbol_instances)
  (sheet_instances
    (path "/" (page "1"))
  )
)
"""


def has_kicad_cli() -> bool:
    """Check if kicad-cli is available on PATH"""
    try:
        result = subprocess.run(["kicad-cli", "--version"], capture_output=True, timeout=3, check=False)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def can_add_components() -> bool:
    """Detect whether kicad-skip supports programmatic symbol creation from libraries."""
    try:
        from skip.eeschema import schematic as sch

        return hasattr(sch, "Symbol") and hasattr(sch.Symbol, "from_lib")
    except Exception:
        return False


@pytest.mark.skipif(not has_kicad_cli(), reason="kicad-cli not found in PATH")
@pytest.mark.skipif(
    not can_add_components(), reason="kicad-skip does not support programmatic symbol creation in this environment"
)
def test_add_led_resistor_with_erc():
    """
    Golden fixture test: Add LED + resistor, verify components exist,
    and check that ERC runs without crashing.
    """
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        sch_path.write_text(MINIMAL_SCHEMATIC_TEMPLATE, encoding="utf-8")

        # Create plan to add LED and resistor
        plan = Plan(
            plan_version=PLAN_SCHEMA_VERSION,
            ops=[
                AddComponent(op="add_component", ref="R1", symbol="Device:R", value="1k", at=(100, 60), rot=0),
                AddComponent(op="add_component", ref="D1", symbol="Device:LED", value="RED", at=(120, 60), rot=0),
                Label(op="label", net="VCC", at=(90, 60)),
            ],
        )
        # Apply plan
        doc = sch.Schematic(str(sch_path))
        result = apply_plan(doc, plan)

        # Verify success
        assert result.success, f"Apply failed: {[d.message for d in result.diagnostics if d.severity == 'error']}"
        assert "R1" in result.affected_refs
        assert "D1" in result.affected_refs

        # Write to file
        doc.to_file(str(sch_path))

        # Re-read and verify components exist
        doc = sch.Schematic(str(sch_path))
        symbols = list(getattr(doc, "symbol", []))

        refs = [s.ref() for s in symbols]
        assert "R1" in refs, f"R1 not found in schematic, found: {refs}"
        assert "D1" in refs, f"D1 not found in schematic, found: {refs}"

        # Find our symbols and verify values
        r1 = next((s for s in symbols if s.ref() == "R1"), None)
        d1 = next((s for s in symbols if s.ref() == "D1"), None)

        assert r1 is not None, "R1 symbol not found"
        assert d1 is not None, "D1 symbol not found"
        assert r1.value() == "1k", f"R1 value wrong: {r1.value()}"
        assert d1.value() == "RED", f"D1 value wrong: {d1.value()}"

        # Run ERC and verify it completes (doesn't crash)
        erc_output = sch_path.with_suffix(".erc.txt")
        result = subprocess.run(
            ["kicad-cli", "sch", "erc", str(sch_path), "-o", str(erc_output), "--format", "report"],
            capture_output=True,
            timeout=10,
            check=False,
        )

        # ERC should complete (may have warnings about unconnected pins, but shouldn't crash)
        assert result.returncode in [0, 2], f"ERC failed with code {result.returncode}: {result.stderr.decode()}"
        assert erc_output.exists(), "ERC output file not created"


@pytest.mark.skipif(not has_kicad_cli(), reason="kicad-cli not found in PATH")
@pytest.mark.skipif(
    not can_add_components(), reason="kicad-skip does not support programmatic symbol creation in this environment"
)
def test_wire_operation_creates_connection():
    """
    Test that wire operations create valid connections.
    This test verifies the wire implementation is not a no-op.
    """
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test_wire.kicad_sch"
        sch_path.write_text(MINIMAL_SCHEMATIC_TEMPLATE, encoding="utf-8")

        # Create plan with components and wire
        plan = Plan(
            plan_version=PLAN_SCHEMA_VERSION,
            ops=[
                AddComponent(op="add_component", ref="R1", symbol="Device:R", value="1k", at=(100, 60), rot=0),
                AddComponent(op="add_component", ref="R2", symbol="Device:R", value="2k", at=(120, 60), rot=0),
                Wire(op="wire", from_="R1:2", to="R2:1"),
            ],
        )

        # Apply plan
        doc = sch.Schematic(str(sch_path))
        result = apply_plan(doc, plan)

        # Verify application succeeded
        assert result.success, (
            f"Wire operation failed: {[d.message for d in result.diagnostics if d.severity == 'error']}"
        )

        # Check that wire operation did SOMETHING (not a no-op)
        wire_diagnostics = [
            d for d in result.diagnostics if "wire" in d.message.lower() or "label" in d.message.lower()
        ]
        assert len(wire_diagnostics) > 0, "Wire operation produced no diagnostics (possible no-op)"

        # Write and verify file is valid
        doc.to_file(str(sch_path))

        # Verify KiCad can read the file
        result = subprocess.run(
            ["kicad-cli", "sch", "export", "pdf", str(sch_path), "-o", str(sch_path.with_suffix(".pdf"))],
            capture_output=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0, f"KiCad failed to process schematic: {result.stderr.decode()}"


def test_label_operation_failure_surfaces():
    """
    Test that label failures are surfaced in diagnostics, not swallowed.
    """
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test_label.kicad_sch"
        sch_path.write_text(MINIMAL_SCHEMATIC_TEMPLATE, encoding="utf-8")

        # Create plan with label at potentially invalid position
        plan = Plan(plan_version=PLAN_SCHEMA_VERSION, ops=[Label(op="label", net="TEST_NET", at=(100, 60))])

        # Apply plan
        doc = sch.Schematic(str(sch_path))
        result = apply_plan(doc, plan)

        # Label should either succeed with info diagnostic, or fail with error diagnostic
        label_diagnostics = [d for d in result.diagnostics if "label" in d.message.lower()]
        assert len(label_diagnostics) > 0, "Label operation produced no diagnostics"

        # Verify diagnostic is explicit (not silently swallowed)
        for d in label_diagnostics:
            assert d.severity in ["info", "error", "warning"], f"Unexpected severity: {d.severity}"
            assert len(d.message) > 0, "Empty diagnostic message"


def test_schema_version_mismatch_prevents_apply():
    """
    Test that schema version mismatch is caught early and prevents application.
    """
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test_version.kicad_sch"
        sch_path.write_text(MINIMAL_SCHEMATIC_TEMPLATE, encoding="utf-8")

        # Create plan with wrong version
        plan = Plan(
            plan_version=999,  # Invalid version
            ops=[Label(op="label", net="TEST", at=(100, 100))],
        )

        doc = sch.Schematic(str(sch_path))
        result = apply_plan(doc, plan)

        # Should fail with schema version error
        assert result.success is False
        assert result.has_errors()

        errors = [d for d in result.diagnostics if d.severity == "error"]
        assert len(errors) > 0
        assert any("schema version" in e.message.lower() for e in errors)


def test_apply_result_structure():
    """
    Test that ApplyResult has expected structure and methods.
    """
    from sidecar.schema import ApplyResult, Diagnostic

    # Test success case
    success_result = ApplyResult(
        success=True,
        diagnostics=[Diagnostic(stage="writer", severity="info", message="Test info")],
        affected_refs=["R1", "R2"],
    )

    assert success_result.success is True
    assert success_result.has_errors() is False
    assert success_result.has_warnings() is False
    assert len(success_result.affected_refs) == 2

    # Test failure case
    fail_result = ApplyResult(
        success=False,
        diagnostics=[
            Diagnostic(stage="writer", severity="error", message="Test error"),
            Diagnostic(stage="writer", severity="warning", message="Test warning"),
        ],
        affected_refs=[],
    )

    assert fail_result.success is False
    assert fail_result.has_errors() is True
    assert fail_result.has_warnings() is True
    assert len(fail_result.affected_refs) == 0


@pytest.mark.skipif(not has_kicad_cli(), reason="kicad-cli not found in PATH")
@pytest.mark.skipif(
    not can_add_components(), reason="kicad-skip does not support programmatic symbol creation in this environment"
)
def test_netlist_export_after_apply():
    """
    Test that netlist export works after applying a plan.
    """
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test_netlist.kicad_sch"
        sch_path.write_text(MINIMAL_SCHEMATIC_TEMPLATE, encoding="utf-8")

        plan = Plan(
            plan_version=PLAN_SCHEMA_VERSION,
            ops=[AddComponent(op="add_component", ref="R1", symbol="Device:R", value="10k", at=(100, 60))],
        )

        doc = sch.Schematic(str(sch_path))
        result = apply_plan(doc, plan)
        assert result.success

        doc.to_file(str(sch_path))

        # Export netlist
        netlist_path = sch_path.with_suffix(".net")
        result = subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", str(sch_path), "-o", str(netlist_path)],
            capture_output=True,
            timeout=10,
            check=False,
        )

        assert result.returncode == 0, f"Netlist export failed: {result.stderr.decode()}"
        assert netlist_path.exists(), "Netlist file not created"

        # Verify netlist contains our component
    netlist_content = netlist_path.read_text(encoding="utf-8")
    assert "R1" in netlist_content, "R1 not found in netlist"
