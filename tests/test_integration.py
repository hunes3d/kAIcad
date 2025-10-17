"""Integration tests for kAIcad - golden file tests"""
import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from sidecar.schema import Plan, PLAN_SCHEMA_VERSION
from sidecar.writer_skip import apply_plan, GRID_MM, snap_to_grid
from skip.eeschema import schematic as sch


@pytest.mark.skip(reason="Requires kicad-skip API that may not be fully available in test environment")
def test_plan_wire_minimal():
    """
    Golden file test: create a tiny plan with two symbols and one wire,
    assert the schematic structure matches expectations.
    """
    plan_dict = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [100, 50]},
            {"op": "add_component", "ref": "R2", "symbol": "Device:R", "value": "2k", "at": [150, 50]},
            {"op": "wire", "from": "R1:2", "to": "R2:1"}
        ]
    }
    plan = Plan.model_validate(plan_dict)
    
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        # Create minimal valid schematic
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        doc = sch.Schematic(str(sch_path))
        doc = apply_plan(doc, plan)
        doc.to_file(str(sch_path))
        
        # Re-read and verify
        doc = sch.Schematic(str(sch_path))
        symbols = list(getattr(doc, 'symbol', []))
        
        # Assert: 2 symbols exist
        assert len(symbols) >= 2, f"Expected at least 2 symbols, got {len(symbols)}"
        
        # Find our symbols
        r1 = None
        r2 = None
        for sym in symbols:
            if sym.ref() == "R1":
                r1 = sym
            if sym.ref() == "R2":
                r2 = sym
        
        assert r1 is not None, "R1 not found in schematic"
        assert r2 is not None, "R2 not found in schematic"
        
        # Assert: coordinates are grid-snapped
        r1_x, r1_y = r1.pos()
        r2_x, r2_y = r2.pos()
        
        assert r1_x == snap_to_grid(100), f"R1 X not snapped: {r1_x}"
        assert r1_y == snap_to_grid(50), f"R1 Y not snapped: {r1_y}"
        assert r2_x == snap_to_grid(150), f"R2 X not snapped: {r2_x}"
        assert r2_y == snap_to_grid(50), f"R2 Y not snapped: {r2_y}"
        
        # Assert: values are correct
        assert r1.value() == "1k", f"R1 value wrong: {r1.value()}"
        assert r2.value() == "2k", f"R2 value wrong: {r2.value()}"
        
        # Note: Wire/net validation would require kicad-skip to expose net collections
        # For now, we verify symbols placed correctly


def test_grid_snap_determinism():
    """Test that grid snapping produces deterministic results"""
    test_cases = [
        (100.0, 99.06),   # Should snap to 99.06 (39 * 2.54)
        (99.9, 99.06),
        (102.0, 101.6),   # Should snap to 101.6 (40 * 2.54)
        (0.0, 0.0),
        (2.54, 2.54),
        (2.53, 2.54),
        (2.55, 2.54),
        (127.0, 127.0),   # Exactly 50 * 2.54
    ]
    
    for input_val, expected in test_cases:
        result = snap_to_grid(input_val)
        assert result == expected, f"snap_to_grid({input_val}) = {result}, expected {expected}"


def test_plan_schema_version_validation():
    """Test that plans require a schema version"""
    # Valid plan with version
    valid = {
        "plan_version": 1,
        "ops": [{"op": "label", "net": "VCC", "at": [10, 10]}]
    }
    plan = Plan.model_validate(valid)
    assert plan.plan_version == 1
    
    # Plan without version should use default
    no_version = {
        "ops": [{"op": "label", "net": "GND", "at": [20, 20]}]
    }
    plan2 = Plan.model_validate(no_version)
    assert plan2.plan_version == PLAN_SCHEMA_VERSION


def test_plan_serialization_includes_version():
    """Test that serialized plans include the version field"""
    from sidecar.schema import AddComponent
    plan = Plan(
        ops=[
            AddComponent(op="add_component", ref="U1", symbol="MCU:ATmega328", value="", at=(100, 100))
        ]
    )
    
    dumped = plan.model_dump(by_alias=True)
    assert "plan_version" in dumped
    assert dumped["plan_version"] == PLAN_SCHEMA_VERSION
    
    # Ensure it round-trips
    json_str = json.dumps(dumped)
    reloaded = Plan.model_validate(json.loads(json_str))
    assert reloaded.plan_version == plan.plan_version
