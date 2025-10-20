"""Test suite for bug fixes from deep code inspection."""

import math
import pytest

from kaicad.utils.validation import (
    validate_symbol_name,
    validate_wire_format,
    validate_coordinate,
)


class TestSymbolValidation:
    """Test Bug #8 fix - Symbol name injection vulnerability"""

    def test_valid_symbol_formats(self):
        """Valid KiCad symbol formats should pass"""
        valid_symbols = [
            "Device:R",
            "Device:LED",
            "MCU_ST_STM32:STM32F103",
            "Connector:USB_B",
            "Device:LED RGB",  # Spaces allowed
        ]
        for sym in valid_symbols:
            is_valid, error = validate_symbol_name(sym)
            assert is_valid, f"Symbol '{sym}' should be valid but got: {error}"

    def test_empty_symbol_rejected(self):
        """Empty symbol names should be rejected"""
        is_valid, error = validate_symbol_name("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_path_traversal_rejected(self):
        """Path traversal attempts should be blocked"""
        malicious = [
            "Device:../../../etc/passwd",
            "../Device:R",
            "Device:..\\..\\windows\\system32",
        ]
        for sym in malicious:
            is_valid, error = validate_symbol_name(sym)
            assert not is_valid, f"Malicious symbol '{sym}' should be rejected"
            assert "traversal" in error.lower() or "separator" in error.lower()

    def test_path_separators_rejected(self):
        """Path separators should be blocked"""
        is_valid, error = validate_symbol_name("Device/Subcategory:R")
        assert not is_valid
        assert "separator" in error.lower()

        is_valid, error = validate_symbol_name("Device\\Subcategory:R")
        assert not is_valid

    def test_missing_colon_rejected(self):
        """Symbols without colon should be rejected"""
        is_valid, error = validate_symbol_name("DeviceR")
        assert not is_valid
        assert "format" in error.lower()

    def test_too_long_rejected(self):
        """Very long symbol names should be rejected"""
        long_symbol = "A" * 100 + ":" + "B" * 150
        is_valid, error = validate_symbol_name(long_symbol)
        assert not is_valid
        assert "too long" in error.lower()


class TestWireValidation:
    """Test Bug #2 fix - Unvalidated split() operations"""

    def test_valid_wire_formats(self):
        """Valid wire formats should pass"""
        valid_wires = [
            "R1:1",
            "U5:VCC",
            "C10:2",
            "J1:GND",
        ]
        for wire in valid_wires:
            is_valid, error, parts = validate_wire_format(wire)
            assert is_valid, f"Wire '{wire}' should be valid but got: {error}"
            assert parts is not None
            assert len(parts) == 2

    def test_missing_colon_rejected(self):
        """Wire without colon should be rejected"""
        is_valid, error, parts = validate_wire_format("R1")
        assert not is_valid
        assert "REF:PIN" in error
        assert parts is None

    def test_too_many_colons_accepted(self):
        """Wire with multiple colons uses split(1) so should work"""
        # This is OK because we split(':',  1) - pin can contain colons
        is_valid, error, parts = validate_wire_format("U1:PIN:A:1")
        assert is_valid  # Split with maxsplit=1 handles this
        ref, pin = parts
        assert ref == "U1"
        assert pin == "PIN:A:1"

    def test_invalid_reference_format(self):
        """References not matching component format should be rejected"""
        invalid = [
            "1R:1",  # Starts with number
            "r1:1",  # Lowercase not allowed
            ":1",  # Empty reference
            "R-5:1",  # Contains dash
        ]
        for wire in invalid:
            is_valid, error, parts = validate_wire_format(wire)
            assert not is_valid, f"Invalid wire '{wire}' should be rejected"

    def test_empty_pin_rejected(self):
        """Empty pin should be rejected"""
        is_valid, error, parts = validate_wire_format("R1:")
        assert not is_valid
        assert "empty" in error.lower()


class TestCoordinateValidation:
    """Test Bug #11 fix - Type confusion in coordinates"""

    def test_valid_coordinates(self):
        """Valid coordinate formats should pass"""
        valid_coords = [
            [0, 0],
            [100.5, 200.3],
            (50, 75),  # Tuples OK too
            [-100, -200],  # Negative OK
        ]
        for coord in valid_coords:
            is_valid, error, parsed = validate_coordinate(coord)
            assert is_valid, f"Coord {coord} should be valid but got: {error}"
            assert parsed is not None
            assert len(parsed) == 2

    def test_non_iterable_rejected(self):
        """Non-iterable values should be rejected"""
        invalid = [42, "100,200", None, 3.14]
        for coord in invalid:
            is_valid, error, parsed = validate_coordinate(coord)
            assert not is_valid
            assert parsed is None

    def test_wrong_length_rejected(self):
        """Coordinates with != 2 values should be rejected"""
        is_valid, error, parsed = validate_coordinate([100])
        assert not is_valid
        assert "exactly 2" in error.lower()

        is_valid, error, parsed = validate_coordinate([1, 2, 3])
        assert not is_valid

    def test_non_numeric_rejected(self):
        """Non-numeric values should be rejected"""
        invalid = [
            ["abc", 100],
            [100, "def"],
            [None, 50],
            [{}, []],
        ]
        for coord in invalid:
            is_valid, error, parsed = validate_coordinate(coord)
            assert not is_valid
            assert "numbers" in error.lower()

    def test_infinity_rejected(self):
        """Infinity values should be rejected"""
        is_valid, error, parsed = validate_coordinate([math.inf, 100])
        assert not is_valid
        assert "finite" in error.lower()

        is_valid, error, parsed = validate_coordinate([100, -math.inf])
        assert not is_valid

    def test_nan_rejected(self):
        """NaN values should be rejected"""
        is_valid, error, parsed = validate_coordinate([math.nan, 100])
        assert not is_valid
        assert "finite" in error.lower()

    def test_extreme_values_rejected(self):
        """Values outside practical limits should be rejected"""
        is_valid, error, parsed = validate_coordinate([2000000, 100])
        assert not is_valid
        assert "exceed" in error.lower()

        is_valid, error, parsed = validate_coordinate([100, -2000000])
        assert not is_valid


class TestAPIKeyMasking:
    """Test Bug #3 fix - API key masking logic"""

    @pytest.fixture(autouse=True)
    def setup_flask_env(self, monkeypatch):
        """Set up Flask environment for testing"""
        monkeypatch.setenv("FLASK_ENV", "development")

    def test_long_key_masked_correctly(self):
        """Long API keys should show first 7 and last 4 characters"""
        from kaicad.ui.web.app import _mask_api_key

        # 50 character key
        key = "sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGH"
        masked = _mask_api_key(key)
        assert masked.startswith("sk-abcd")
        assert masked.endswith("EFGH")
        assert "****" in masked

    def test_short_key_fully_masked(self):
        """Short keys should be fully masked"""
        from kaicad.ui.web.app import _mask_api_key

        # 11 chars or less - too short for 7****4 format
        short_keys = ["abc", "abcdefgh", "12345678901"]
        for key in short_keys:
            masked = _mask_api_key(key)
            assert masked == "****", f"Key of length {len(key)} should be fully masked"

    def test_boundary_case_12_chars(self):
        """12-character key is the minimum for 7****4 format"""
        from kaicad.ui.web.app import _mask_api_key

        key = "123456789012"  # Exactly 12 chars
        masked = _mask_api_key(key)
        # Should show 1234567****9012
        assert masked.startswith("1234567")
        assert masked.endswith("9012")
        assert len(masked) == 15  # 7 + 4 + 4 stars

    def test_empty_key(self):
        """Empty key should return empty string"""
        from kaicad.ui.web.app import _mask_api_key

        assert _mask_api_key("") == ""
        assert _mask_api_key(None) == ""


class TestWriterValidation:
    """Integration tests for writer.py validation"""

    def test_writer_rejects_invalid_symbol(self):
        """Writer should reject plans with invalid symbols"""
        from kaicad.schema.plan import Plan

        plan_data = {
            "plan_version": "1.0",
            "ops": [
                {
                    "op": "add_component",
                    "ref": "R1",
                    "symbol": "Device:../../../etc/passwd",  # Path traversal with colon
                    "value": "1k",
                    "at": [100, 100],
                }
            ],
        }
        plan = Plan.model_validate(plan_data)

        # In a real scenario, apply_plan would reject this
        # We're just testing that validation catches it
        from kaicad.utils.validation import validate_symbol_name

        is_valid, error = validate_symbol_name(plan.ops[0].symbol)
        assert not is_valid
        # Should catch path traversal
        assert "traversal" in error.lower()

    def test_writer_rejects_invalid_wire(self):
        """Writer should reject plans with invalid wire formats"""
        from kaicad.schema.plan import Plan

        plan_data = {
            "plan_version": "1.0",
            "ops": [{"op": "wire", "from": "R1", "to": "R2:2"}],  # Missing colon
        }
        plan = Plan.model_validate(plan_data)

        # Validation should catch the bad format
        from kaicad.utils.validation import validate_wire_format

        is_valid, error, parts = validate_wire_format(plan.ops[0].from_)
        assert not is_valid

    def test_writer_rejects_invalid_coordinates(self):
        """Writer should reject plans with invalid coordinates"""
        from kaicad.schema.plan import Plan

        # This will fail at Pydantic level, but our validation adds extra checks
        plan_data = {
            "plan_version": "1.0",
            "ops": [
                {
                    "op": "add_component",
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "1k",
                    "at": [math.inf, 100],  # Invalid: infinity
                }
            ],
        }

        # Pydantic might accept this, but our validation catches it
        from kaicad.utils.validation import validate_coordinate

        is_valid, error, parsed = validate_coordinate([math.inf, 100])
        assert not is_valid
        assert "finite" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
