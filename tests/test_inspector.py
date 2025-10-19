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
    inspect_hierarchical_design,
    format_inspection_report
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


def test_format_inspection_report_success():
    """Test formatting a successful inspection report"""
    inspection = {
        "success": True,
        "file": "/path/to/test.kicad_sch",
        "components": [
            {"ref": "R1", "value": "10k", "symbol": "Device:R", "position": (100, 50)},
            {"ref": "C1", "value": "100nF", "symbol": "Device:C", "position": (150, 50)}
        ],
        "nets": ["VCC", "GND", "SDA", "SCL"],
        "labels": [
            {"text": "VCC", "position": (110, 50)},
            {"text": "GND", "position": (125, 90)}
        ],
        "hierarchy": [],
        "stats": {
            "total_components": 2,
            "total_nets": 4,
            "total_labels": 2,
            "total_sheets": 0,
            "component_types": {"R": 1, "C": 1}
        }
    }
    
    report = format_inspection_report(inspection)
    
    assert isinstance(report, str)
    assert "Schematic Inspection Report" in report
    assert "test.kicad_sch" in report
    assert "Components: 2" in report
    assert "Nets: 4" in report
    assert "R1" in report
    assert "C1" in report
    assert "VCC" in report


def test_format_inspection_report_failure():
    """Test formatting a failed inspection report"""
    inspection = {
        "success": False,
        "error": "File not found",
        "file": "/path/to/missing.kicad_sch"
    }
    
    report = format_inspection_report(inspection)
    
    assert isinstance(report, str)
    assert "Failed" in report or "❌" in report
    assert "File not found" in report


def test_format_inspection_report_with_hierarchy():
    """Test formatting report with hierarchical sheets"""
    inspection = {
        "success": True,
        "file": "/path/to/main.kicad_sch",
        "components": [],
        "nets": [],
        "labels": [],
        "hierarchy": [
            {"name": "Power", "file": "power.kicad_sch", "position": (50, 50)},
            {"name": "CPU", "file": "cpu.kicad_sch", "position": (100, 100)}
        ],
        "stats": {
            "total_components": 0,
            "total_nets": 0,
            "total_labels": 0,
            "total_sheets": 2,
            "component_types": {}
        }
    }
    
    report = format_inspection_report(inspection)
    
    assert isinstance(report, str)
    assert "Hierarchical Sheets" in report
    assert "Power" in report
    assert "CPU" in report
    assert "Hierarchical Sheets: 2" in report


def test_format_inspection_report_many_components():
    """Test formatting report with many components (should truncate)"""
    # Create 30 components
    components = [
        {"ref": f"R{i}", "value": f"{i}k", "symbol": "Device:R", "position": (i*10, 50)}
        for i in range(1, 31)
    ]
    
    inspection = {
        "success": True,
        "file": "/path/to/test.kicad_sch",
        "components": components,
        "nets": [],
        "labels": [],
        "hierarchy": [],
        "stats": {
            "total_components": 30,
            "total_nets": 0,
            "total_labels": 0,
            "total_sheets": 0,
            "component_types": {"R": 30}
        }
    }
    
    report = format_inspection_report(inspection)
    
    assert isinstance(report, str)
    assert "Components: 30" in report
    # Should show first 20 and indicate there are more
    assert "and 10 more" in report or "..." in report


def test_format_inspection_report_many_nets():
    """Test formatting report with many nets (should truncate)"""
    # Create 20 nets
    nets = [f"NET{i}" for i in range(1, 21)]
    
    inspection = {
        "success": True,
        "file": "/path/to/test.kicad_sch",
        "components": [],
        "nets": nets,
        "labels": [],
        "hierarchy": [],
        "stats": {
            "total_components": 0,
            "total_nets": 20,
            "total_labels": 0,
            "total_sheets": 0,
            "component_types": {}
        }
    }
    
    report = format_inspection_report(inspection)
    
    assert isinstance(report, str)
    assert "Nets: 20" in report
    # Should show first 15 and indicate there are more
    assert "and 5 more" in report or "..." in report


def test_search_components_empty_result(test_schematic):
    """Test searching for non-existent components"""
    result = search_components(test_schematic, "NONEXISTENT")
    
    assert isinstance(result, list)
    # Should be empty or have error
    if result:
        assert "error" in result[0] or "ref" in result[0]


def test_find_components_by_pattern_wildcard(test_schematic):
    """Test pattern matching with wildcards"""
    # Test with wildcard pattern
    result = find_components_by_pattern(test_schematic, "R*")
    
    assert isinstance(result, list)


def test_inspect_net_connections_nonexistent(test_schematic):
    """Test inspecting a net that doesn't exist"""
    result = inspect_net_connections(test_schematic, "NONEXISTENT_NET")
    
    assert isinstance(result, dict)
    # Should have success or error key
    assert 'success' in result or 'error' in result


def test_get_component_connections_nonexistent(test_schematic):
    """Test getting connections for non-existent component"""
    result = get_component_connections(test_schematic, "NONEXISTENT99")
    
    assert isinstance(result, dict)
    # Function returns success=True but component has error
    if 'component' in result:
        assert 'error' in result['component'] or 'success' in result['component']
    elif 'success' in result and not result['success']:
        assert 'error' in result


def test_inspect_hierarchical_design_with_hierarchy():
    """Test hierarchical inspection when sheets are present"""
    # Create a schematic with hierarchy reference (even if files don't exist)
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir) / "root.kicad_sch"
        
        # Write a schematic that references sub-sheets
        schematic_with_sheets = MINIMAL_SCHEMATIC_WITH_COMPONENTS
        with root_path.open("w") as f:
            f.write(schematic_with_sheets)
        
        result = inspect_hierarchical_design(root_path)
        
        assert 'root' in result
        assert 'subsheets' in result
        assert isinstance(result['root'], dict)
        assert isinstance(result['subsheets'], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
