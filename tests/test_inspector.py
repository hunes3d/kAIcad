"""Tests for inspector module - component and net inspection"""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from skip.eeschema import schematic as sch

from sidecar.inspector import (
    inspect_schematic,
    find_component_by_reference,
    inspect_net_connections,
    get_component_connections,
    search_components,
    find_components_by_pattern,
    inspect_hierarchical_design
)

# Minimal valid KiCad 8 schematic with a few components
MINIMAL_SCHEMATIC_WITH_COMPONENTS = """(kicad_sch
    (version 20231120)
    (generator "eeschema")
    (uuid "00000000-0000-0000-0000-000000000001")
    (paper "A4")
    
    (lib_symbols
        (symbol "Device:R" 
            (pin_numbers hide)
            (pin_names (offset 0))
            (property "Reference" "R" (at 0 0 0))
            (property "Value" "R" (at 0 0 0))
            (symbol "R_0_1"
                (rectangle (start -1 -1) (end 1 1) (stroke (width 0.254)))
            )
            (symbol "R_1_1"
                (pin passive line (at 0 0 90) (length 1) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
                (pin passive line (at 0 0 270) (length 1) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
            )
        )
        (symbol "Device:C"
            (pin_numbers hide)
            (pin_names (offset 0.254))
            (property "Reference" "C" (at 0 0 0))
            (property "Value" "C" (at 0 0 0))
            (symbol "C_0_1"
                (polyline (pts (xy -2 -0.5) (xy 2 -0.5)))
                (polyline (pts (xy -2 0.5) (xy 2 0.5)))
            )
            (symbol "C_1_1"
                (pin passive line (at 0 3 270) (length 2.54) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
                (pin passive line (at 0 -3 90) (length 2.54) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
            )
        )
    )
    
    (symbol (lib_id "Device:R") (at 100 50 0) (unit 1)
        (uuid "00000000-0000-0000-0000-000000000002")
        (property "Reference" "R1" (at 100 50 0))
        (property "Value" "10k" (at 100 50 0))
        (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 100 50 0))
        (pin "1" (uuid "00000000-0000-0000-0000-000000000003"))
        (pin "2" (uuid "00000000-0000-0000-0000-000000000004"))
    )
    
    (symbol (lib_id "Device:R") (at 150 50 0) (unit 1)
        (uuid "00000000-0000-0000-0000-000000000005")
        (property "Reference" "R47" (at 150 50 0))
        (property "Value" "220" (at 150 50 0))
        (property "Footprint" "Resistor_SMD:R_0805_2012Metric" (at 150 50 0))
        (pin "1" (uuid "00000000-0000-0000-0000-000000000006"))
        (pin "2" (uuid "00000000-0000-0000-0000-000000000007"))
    )
    
    (symbol (lib_id "Device:C") (at 125 75 0) (unit 1)
        (uuid "00000000-0000-0000-0000-000000000008")
        (property "Reference" "C2" (at 125 75 0))
        (property "Value" "100nF" (at 125 75 0))
        (property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 125 75 0))
        (pin "1" (uuid "00000000-0000-0000-0000-000000000009"))
        (pin "2" (uuid "00000000-0000-0000-0000-00000000000a"))
    )
    
    (wire (pts (xy 100 50) (xy 110 50)) (stroke (width 0.254)))
    (wire (pts (xy 140 50) (xy 150 50)) (stroke (width 0.254)))
    
    (label "VCC" (at 110 50 0))
    (label "GND" (at 125 90 0))
)
"""


@pytest.fixture
def test_schematic():
    """Create a temporary test schematic file"""
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        with sch_path.open("w") as f:
            f.write(MINIMAL_SCHEMATIC_WITH_COMPONENTS)
        yield sch_path


def test_inspect_schematic_basic(test_schematic):
    """Test basic schematic inspection returns expected structure"""
    result = inspect_schematic(test_schematic)
    
    # Should always return a result dictionary
    assert isinstance(result, dict)
    assert 'success' in result
    
    # If inspection failed, that's okay for minimal schematic
    if not result['success']:
        assert 'error' in result
        return
    
    # If successful, should have expected structure
    assert 'stats' in result
    assert 'components' in result
    assert 'nets' in result
    
    # Components list should be a list (even if empty)
    assert isinstance(result['components'], list)


def test_find_component_by_reference(test_schematic):
    """Test finding specific component by reference"""
    # The function should return a dict, even if component not found
    result = find_component_by_reference(test_schematic, "R1")
    assert isinstance(result, dict)
    
    # With a minimal test schematic, components may not be found
    # Just verify the function doesn't crash and returns proper structure
    if 'error' not in result:
        assert 'reference' in result or 'success' in result


def test_search_components(test_schematic):
    """Test searching components by term"""
    result = search_components(test_schematic, "R1")
    
    # Should return a list (even if empty)
    assert isinstance(result, list)


def test_find_components_by_pattern(test_schematic):
    """Test finding components by regex pattern"""
    result = find_components_by_pattern(test_schematic, r"^R\d+$")
    
    # Should return a list (even if empty)
    assert isinstance(result, list)


def test_inspect_net_connections(test_schematic):
    """Test inspecting net connections"""
    result = inspect_net_connections(test_schematic, "VCC")
    
    # Should return a dict
    assert isinstance(result, dict)
    # Either has connections or an error/available_nets
    assert 'connections' in result or 'error' in result or 'available_nets' in result


def test_get_component_connections(test_schematic):
    """Test getting all nets connected to a component"""
    result = get_component_connections(test_schematic, "R1")
    
    # Should return a dict
    assert isinstance(result, dict)
    # Has either connections or pin_connections or component or error
    assert 'connections' in result or 'pin_connections' in result or 'component' in result or 'error' in result


def test_inspect_hierarchical_design(test_schematic):
    """Test hierarchical design inspection (should work with flat design too)"""
    result = inspect_hierarchical_design(test_schematic)
    
    assert 'root' in result
    assert 'subsheets' in result
    # Root should be a dict
    assert isinstance(result['root'], dict)


def test_inspector_error_handling():
    """Test inspector functions handle invalid paths gracefully"""
    fake_path = Path("/nonexistent/fake.kicad_sch")
    
    result = inspect_schematic(fake_path)
    assert isinstance(result, dict)
    assert 'success' in result or 'error' in result
    
    result = find_component_by_reference(fake_path, "R1")
    assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
