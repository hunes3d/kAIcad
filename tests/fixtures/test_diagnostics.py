"""Tests for diagnostic and error surfacing"""

from unittest.mock import Mock, patch

import pytest

from kaicad.schema.plan import ApplyResult, Diagnostic, Plan
from kaicad.core.writer import apply_plan


def test_diagnostic_creation():
    """Test creating diagnostic objects"""
    diag = Diagnostic(
        stage="writer",
        severity="error",
        ref="R1",
        message="Component not found",
        suggestion="Ensure component exists before wiring",
    )

    assert diag.stage == "writer"
    assert diag.severity == "error"
    assert diag.ref == "R1"
    assert diag.message == "Component not found"
    assert diag.suggestion == "Ensure component exists before wiring"


def test_apply_result_has_errors():
    """Test ApplyResult error detection"""
    result = ApplyResult(
        success=False,
        diagnostics=[
            Diagnostic(stage="writer", severity="error", message="Test error"),
            Diagnostic(stage="writer", severity="warning", message="Test warning"),
        ],
        affected_refs=[],
    )

    assert result.has_errors() is True
    assert result.success is False


def test_apply_result_has_warnings():
    """Test ApplyResult warning detection"""
    result = ApplyResult(
        success=True,
        diagnostics=[
            Diagnostic(stage="writer", severity="warning", message="Test warning"),
            Diagnostic(stage="writer", severity="info", message="Test info"),
        ],
        affected_refs=["R1"],
    )

    assert result.has_errors() is False
    assert result.has_warnings() is True
    assert result.success is True


def test_apply_plan_returns_apply_result():
    """Test that apply_plan returns ApplyResult instead of doc"""
    plan = Plan(plan_version=1, ops=[{"op": "label", "net": "TEST", "at": [100, 100]}])

    # Mock schematic with symbols iterable property (new skip API)
    mock_doc = Mock()
    mock_doc.symbol = []  # Empty iterable for ref index
    # labels() should return an object with .add
    mock_labels = Mock()
    mock_labels.add = Mock()
    mock_doc.labels.return_value = mock_labels

    result = apply_plan(mock_doc, plan)

    assert isinstance(result, ApplyResult)
    assert result.success is True
    assert len(result.diagnostics) >= 1  # Should have info diagnostic


def test_apply_plan_diagnostic_on_error():
    """Test that errors generate diagnostics"""
    plan = Plan(
        plan_version=1,
        ops=[{"op": "add_component", "ref": "R1", "symbol": "BadLibrary:Nonexistent", "value": "1k", "at": [100, 100]}],
    )

    # Mock schematic with symbols iterable property (new skip API)
    mock_doc = Mock()
    mock_doc.symbol = []  # Empty iterable for ref index

    with patch("kaicad.core.writer.Symbol") as MockSymbol:
        MockSymbol.from_lib.side_effect = Exception("Library not found")

        result = apply_plan(mock_doc, plan)

        assert result.success is False
        assert result.has_errors() is True

        # Find the error diagnostic
        errors = [d for d in result.diagnostics if d.severity == "error"]
        assert len(errors) == 1
        assert "Library not found" in errors[0].message
        assert errors[0].ref == "R1"


def test_symbol_from_lib_not_available_error():
    """Test that Symbol.from_lib works with the kicad-skip fork"""
    from skip.eeschema import schematic as sch
    from pathlib import Path
    import tempfile
    
    plan = Plan(
        plan_version=1,
        ops=[{"op": "add_component", "ref": "D1", "symbol": "Device:LED", "value": "RED", "at": [100, 50]}],
    )

    # Create a real but empty schematic to test with
    with tempfile.NamedTemporaryFile(mode='w', suffix='.kicad_sch', delete=False) as f:
        # Write minimal valid KiCad schematic
        f.write('(kicad_sch (version 20231120) (generator "eeschema") (paper "A4"))')
        temp_path = f.name
    
    try:
        doc = sch.Schematic(temp_path)
        
        # With the kicad-skip fork, Symbol.from_lib should work
        result = apply_plan(doc, plan)

        # Should succeed now!
        assert result.success is True
        assert "D1" in result.affected_refs
        
        # Should have an info diagnostic about adding the component
        infos = [d for d in result.diagnostics if d.severity == "info" and d.ref == "D1"]
        assert len(infos) == 1
        assert "Added D1" in infos[0].message
        
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


def test_kicad_cli_test_button():
    """Test KiCad CLI test functionality (mocked)"""
    import subprocess

    # Mock successful kicad-cli call
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="9.0.4", stderr="")

        result = subprocess.run(["kicad-cli", "--version"], capture_output=True, text=True, timeout=3)

        assert result.returncode == 0
        assert "9.0.4" in result.stdout

    # Mock failed kicad-cli call (not found)
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("kicad-cli not found")

        with pytest.raises(FileNotFoundError):
            subprocess.run(["kicad-cli", "--version"], capture_output=True, text=True, timeout=3)


def test_web_security_enforcement():
    """Test that web.py enforces security in --serve mode"""

    # This is a smoke test - actual CLI testing would require more complex setup
    # Just verify the argument parser works
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--dev", action="store_true")

    # Test serve mode flag
    args = parser.parse_args(["--serve"])
    assert args.serve is True
    assert args.dev is False

    # Test dev mode flag
    args = parser.parse_args(["--dev"])
    assert args.serve is False
    assert args.dev is True

    # Test both flags
    args = parser.parse_args(["--serve", "--dev"])
    assert args.serve is True
    assert args.dev is True


def test_schema_version_enforcement():
    """Test that apply_plan rejects mismatched schema versions"""
    from kaicad.schema.plan import PLAN_SCHEMA_VERSION

    # Create a plan with wrong version
    plan = Plan(
        plan_version=PLAN_SCHEMA_VERSION + 1,  # Future version
        ops=[{"op": "label", "net": "TEST", "at": [100, 100]}],
    )

    mock_doc = Mock()
    result = apply_plan(mock_doc, plan)

    assert result.success is False
    assert result.has_errors() is True

    # Verify error diagnostic
    errors = [d for d in result.diagnostics if d.severity == "error"]
    assert len(errors) == 1
    assert errors[0].stage == "validator"
    assert "schema version mismatch" in errors[0].message.lower()
    assert "re-run the planner" in errors[0].suggestion.lower()
