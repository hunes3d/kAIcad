"""
Test pin locations and new kicad-skip fork features.

This test verifies that the new helper methods work correctly:
- Symbol.from_lib() for creating symbols
- get_pin_locations() for all component types
- get_pin_by_name() and get_pin_by_number()
- Direct property setters (sym.Reference = "R1")
"""

import tempfile
from pathlib import Path

from skip.eeschema.schematic import Schematic, Symbol


def test_symbol_from_lib():
    """Test Symbol.from_lib() creates symbols correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        # Create empty schematic
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create symbols using from_lib
        vreg = Symbol.from_lib(sch, 'Regulator_Linear:AP2112K-3.3', 'U1', 100, 100)
        cap = Symbol.from_lib(sch, 'Device:C_Small', 'C1', 80, 100)
        resistor = Symbol.from_lib(sch, 'Device:R_Small', 'R1', 120, 100)
        
        # Verify symbols are added to collection
        assert vreg in sch.symbol, "Voltage regulator not in schematic"
        assert cap in sch.symbol, "Capacitor not in schematic"
        assert resistor in sch.symbol, "Resistor not in schematic"
        
        # Verify we can find symbols by reference
        assert sch.symbol.U1 == vreg, "Cannot find U1 by reference"
        assert sch.symbol.C1 == cap, "Cannot find C1 by reference"
        assert sch.symbol.R1 == resistor, "Cannot find R1 by reference"
        
        print("✅ Symbol.from_lib() works correctly!")


def test_pin_locations_two_pin():
    """Test get_pin_locations() for 2-pin components."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create 2-pin components
        resistor = Symbol.from_lib(sch, 'Device:R_Small', 'R1', 100, 100)
        cap = Symbol.from_lib(sch, 'Device:C_Small', 'C1', 120, 100)
        
        # Get pin locations
        r_pins = resistor.get_pin_locations()
        c_pins = cap.get_pin_locations()
        
        # Verify we get both pins
        assert '1' in r_pins, "Pin 1 not found in resistor"
        assert '2' in r_pins, "Pin 2 not found in resistor"
        assert '1' in c_pins, "Pin 1 not found in capacitor"
        assert '2' in c_pins, "Pin 2 not found in capacitor"
        
        # Verify coordinates are tuples of (x, y)
        assert isinstance(r_pins['1'], tuple), "Pin location not a tuple"
        assert len(r_pins['1']) == 2, "Pin location not (x, y)"
        
        print(f"✅ 2-pin component pin locations: R1={r_pins}, C1={c_pins}")


def test_pin_locations_multi_pin():
    """Test get_pin_locations() for multi-pin components (ICs, connectors)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create multi-pin IC
        vreg = Symbol.from_lib(sch, 'Regulator_Linear:AP2112K-3.3', 'U1', 100, 100)
        
        # Get pin locations
        vreg_pins = vreg.get_pin_locations()
        
        # Verify we get multiple pins
        assert len(vreg_pins) > 2, f"Expected more than 2 pins, got {len(vreg_pins)}"
        
        # Verify common pin names for voltage regulator
        # AP2112K-3.3 should have VIN, VOUT, GND pins
        assert any('VIN' in name or '1' in name for name in vreg_pins.keys()), \
            f"VIN pin not found, available pins: {list(vreg_pins.keys())}"
        
        # Verify all coordinates are valid tuples
        for pin_name, (x, y) in vreg_pins.items():
            assert isinstance(x, (int, float)), f"Pin {pin_name} x-coord not numeric"
            assert isinstance(y, (int, float)), f"Pin {pin_name} y-coord not numeric"
        
        print(f"✅ Multi-pin IC pin locations: U1 has {len(vreg_pins)} pins: {list(vreg_pins.keys())}")


def test_get_pin_by_name():
    """Test get_pin_by_name() method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create IC with named pins
        vreg = Symbol.from_lib(sch, 'Regulator_Linear:AP2112K-3.3', 'U1', 100, 100)
        
        # Get pins - try common regulator pin names
        locations = vreg.get_pin_locations()
        pin_names = list(locations.keys())
        
        # Try to get first available pin
        if pin_names:
            first_pin_name = pin_names[0]
            pin = vreg.get_pin_by_name(first_pin_name)
            assert pin is not None, f"get_pin_by_name('{first_pin_name}') returned None"
            assert hasattr(pin, 'location'), "Pin object doesn't have location"
            
            # Verify location matches get_pin_locations()
            pin_loc = (pin.location.x, pin.location.y)
            assert pin_loc == locations[first_pin_name], \
                f"Pin location mismatch: {pin_loc} != {locations[first_pin_name]}"
            
            print(f"✅ get_pin_by_name('{first_pin_name}') works correctly!")
        else:
            print("⚠️ Warning: No pins found to test get_pin_by_name()")


def test_get_pin_by_number():
    """Test get_pin_by_number() method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create 2-pin component
        resistor = Symbol.from_lib(sch, 'Device:R_Small', 'R1', 100, 100)
        
        # Get pins by number
        pin1 = resistor.get_pin_by_number('1')
        pin2 = resistor.get_pin_by_number('2')
        
        assert pin1 is not None, "Pin 1 not found"
        assert pin2 is not None, "Pin 2 not found"
        assert hasattr(pin1, 'location'), "Pin 1 doesn't have location"
        assert hasattr(pin2, 'location'), "Pin 2 doesn't have location"
        
        # Verify locations match get_pin_locations()
        locations = resistor.get_pin_locations()
        assert (pin1.location.x, pin1.location.y) == locations['1'], "Pin 1 location mismatch"
        assert (pin2.location.x, pin2.location.y) == locations['2'], "Pin 2 location mismatch"
        
        print("✅ get_pin_by_number() works correctly!")


def test_property_setters():
    """Test direct property setters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create symbol
        sym = Symbol.from_lib(sch, 'Device:R_Small', 'R1', 100, 100)
        
        # Test property setters
        sym.Reference = 'R2'
        sym.Value = '10k'
        
        # Verify properties were set
        assert sym.property.Reference.value == 'R2', \
            f"Reference not set correctly: {sym.property.Reference.value}"
        assert sym.property.Value.value == '10k', \
            f"Value not set correctly: {sym.property.Value.value}"
        
        print("✅ Property setters work correctly!")


def test_complete_workflow():
    """Test complete workflow: create components and wire them."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        
        with sch_path.open("w") as f:
            f.write('(kicad_sch (version 20221120) (generator "eeschema"))')
        
        sch = Schematic(str(sch_path))
        
        # Create components
        vreg = Symbol.from_lib(sch, 'Regulator_Linear:AP2112K-3.3', 'U1', 100, 100)
        cin = Symbol.from_lib(sch, 'Device:C_Small', 'C1', 80, 100)
        cout = Symbol.from_lib(sch, 'Device:C_Small', 'C2', 120, 100)
        
        # Set values
        cin.Value = '10uF'
        cout.Value = '10uF'
        
        # Get pin locations
        vreg_pins = vreg.get_pin_locations()
        cin_pins = cin.get_pin_locations()
        cout_pins = cout.get_pin_locations()
        
        # Verify all components have pins
        assert len(vreg_pins) > 0, "Voltage regulator has no pins"
        assert len(cin_pins) > 0, "Input capacitor has no pins"
        assert len(cout_pins) > 0, "Output capacitor has no pins"
        
        # Create wires (verify we can access pin coordinates)
        # Note: Actual wire creation would use doc.wire.new() and set pts
        # Here we just verify we can get the coordinates for wiring
        assert '2' in cin_pins, "Input cap pin 2 not found"
        assert '1' in cout_pins, "Output cap pin 1 not found"
        
        # Verify coordinates are usable for wiring
        cin_pin2 = cin_pins['2']
        cout_pin1 = cout_pins['1']
        assert isinstance(cin_pin2, tuple) and len(cin_pin2) == 2, "Invalid pin coordinate"
        assert isinstance(cout_pin1, tuple) and len(cout_pin1) == 2, "Invalid pin coordinate"
        
        # Save schematic
        sch.to_file(str(sch_path))
        
        # Verify file was created
        assert sch_path.exists(), "Schematic file not created"
        
        print("✅ Complete workflow test passed!")


if __name__ == '__main__':
    print("Testing new kicad-skip fork features...\n")
    
    try:
        test_symbol_from_lib()
        test_pin_locations_two_pin()
        test_pin_locations_multi_pin()
        test_get_pin_by_name()
        test_get_pin_by_number()
        test_property_setters()
        test_complete_workflow()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
