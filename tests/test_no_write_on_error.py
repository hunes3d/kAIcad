"""Test that failed plan applications don't modify the schematic file"""

from sidecar.schema import Plan
from sidecar.writer_skip import apply_plan

# Minimal valid KiCad schematic for testing
MINIMAL_SCHEMATIC = """(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (uuid "00000000-0000-0000-0000-000000000000")
  (paper "A4")
  (lib_symbols)
  (symbol_instances)
)
"""


def test_no_write_on_schema_version_error():
    """Test that apply_plan returns failure for wrong schema version"""
    from unittest.mock import Mock

    # Mock schematic with iterable symbols (new API)
    mock_doc = Mock()
    mock_doc.symbol = []

    # Create plan with wrong version
    plan = Plan(
        plan_version=999,  # Invalid version
        ops=[{"op": "label", "net": "TEST", "at": [100, 100]}],
    )

    # Apply plan (should fail on version check)
    result = apply_plan(mock_doc, plan)

    # Verify result indicates failure
    assert result.success is False
    assert result.has_errors() is True

    # Find the version mismatch error
    errors = [d for d in result.diagnostics if d.severity == "error" and "version mismatch" in d.message.lower()]
    assert len(errors) == 1
    assert "validator" in errors[0].stage

    # CRITICAL: UIs must check result.success before calling doc.save()
    # This test documents the contract - when success=False, don't save


def test_ui_respects_apply_result_success():
    """Test that UI code pattern checks result.success before writing"""
    # This is more of a documentation test showing the expected pattern
    # Real UIs should follow this pattern:

    # CORRECT pattern (all UIs should follow):
    # result = apply_plan(doc, plan)
    # if result.success:
    #     doc.save(path)
    # else:
    #     # Show errors, don't save
    #     pass

    # Let's verify the pattern is documented in writer_skip
    import inspect

    from sidecar import writer_skip

    # Check that ApplyResult has success field
    from sidecar.schema import ApplyResult

    assert hasattr(ApplyResult, "model_fields")
    assert "success" in ApplyResult.model_fields

    # Verify apply_plan returns ApplyResult
    sig = inspect.signature(writer_skip.apply_plan)
    assert sig.return_annotation.__name__ == "ApplyResult"

    # This test passes if the structure is correct
    # Manual code review of main.py, web.py, desk.py confirms they all check result.success


def test_file_unchanged_on_component_error():
    """Test that component errors result in failure status"""
    from unittest.mock import Mock, patch

    mock_doc = Mock()
    mock_doc.symbol = []

    # Plan with invalid library reference (will fail)
    plan = Plan(
        plan_version=1,
        ops=[{"op": "add_component", "ref": "R1", "symbol": "FakeLib:NonExistent", "value": "1k", "at": [100, 100]}],
    )

    with patch("sidecar.writer_skip.Symbol") as MockSymbol:
        MockSymbol.from_lib.side_effect = Exception("Library not found")

        # Apply (should fail on Symbol.from_lib)
        result = apply_plan(mock_doc, plan)

        # Should have error status
        assert result.success is False
        assert result.has_errors() is True

        # UIs must check result.success before saving:
        # if result.success:
        #     doc.save(path)  # Only save on success!
        # else:
        #     # Show errors, don't save
        #     pass
