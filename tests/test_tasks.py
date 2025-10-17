"""Tests for tasks module."""
import tempfile
from pathlib import Path
from unittest.mock import patch, call
import pytest
from sidecar.tasks import run_erc, export_netlist, export_pdf


def test_run_erc():
    """Test that run_erc calls kicad-cli with correct arguments."""
    test_sch = Path("/test/schematic.kicad_sch")
    expected_out = Path("/test/schematic.erc.txt")
    
    with patch("sidecar.tasks.subprocess.run") as mock_run:
        run_erc(test_sch)
        
        mock_run.assert_called_once_with(
            ["kicad-cli", "sch", "erc", str(test_sch), "-o", str(expected_out), "--format", "report"],
            check=False
        )


def test_export_netlist():
    """Test that export_netlist calls kicad-cli with correct arguments."""
    test_sch = Path("/test/circuit.kicad_sch")
    expected_out = Path("/test/circuit.net")
    
    with patch("sidecar.tasks.subprocess.run") as mock_run:
        export_netlist(test_sch)
        
        mock_run.assert_called_once_with(
            ["kicad-cli", "sch", "export", "netlist", str(test_sch), "-o", str(expected_out)],
            check=False
        )


def test_export_pdf():
    """Test that export_pdf calls kicad-cli with correct arguments."""
    test_sch = Path("/test/design.kicad_sch")
    expected_out = Path("/test/design.pdf")
    
    with patch("sidecar.tasks.subprocess.run") as mock_run:
        export_pdf(test_sch)
        
        mock_run.assert_called_once_with(
            ["kicad-cli", "sch", "export", "pdf", str(test_sch), "-o", str(expected_out)],
            check=False
        )


def test_run_erc_with_tempfile():
    """Test run_erc with actual temporary file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_sch = Path(tmpdir) / "test.kicad_sch"
        test_sch.touch()
        
        with patch("sidecar.tasks.subprocess.run") as mock_run:
            run_erc(test_sch)
            
            # Verify output path construction
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "kicad-cli"
            assert call_args[2] == "erc"
            assert str(test_sch) in call_args
            assert ".erc.txt" in call_args[5]


def test_export_netlist_with_tempfile():
    """Test export_netlist with actual temporary file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_sch = Path(tmpdir) / "circuit.kicad_sch"
        test_sch.touch()
        
        with patch("sidecar.tasks.subprocess.run") as mock_run:
            export_netlist(test_sch)
            
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "kicad-cli"
            assert call_args[3] == "netlist"
            assert ".net" in call_args[6]


def test_export_pdf_with_tempfile():
    """Test export_pdf with actual temporary file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_sch = Path(tmpdir) / "design.kicad_sch"
        test_sch.touch()
        
        with patch("sidecar.tasks.subprocess.run") as mock_run:
            export_pdf(test_sch)
            
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "kicad-cli"
            assert call_args[3] == "pdf"
            assert ".pdf" in call_args[6]


def test_all_tasks_use_check_false():
    """Test that all tasks use check=False to not raise on kicad-cli errors."""
    test_sch = Path("/test/test.kicad_sch")
    
    with patch("sidecar.tasks.subprocess.run") as mock_run:
        run_erc(test_sch)
        assert mock_run.call_args[1]["check"] is False
        
        export_netlist(test_sch)
        assert mock_run.call_args[1]["check"] is False
        
        export_pdf(test_sch)
        assert mock_run.call_args[1]["check"] is False


def test_tasks_handle_different_extensions():
    """Test that tasks correctly replace file extensions."""
    # Test with .sch extension
    old_sch = Path("/test/old_format.sch")
    
    with patch("sidecar.tasks.subprocess.run") as mock_run:
        run_erc(old_sch)
        call_args = mock_run.call_args[0][0]
        # Check that output has .erc.txt extension (path separators may vary by platform)
        assert "old_format.erc.txt" in str(call_args)
        
        export_netlist(old_sch)
        call_args = mock_run.call_args[0][0]
        assert "old_format.net" in str(call_args)
        
        export_pdf(old_sch)
        call_args = mock_run.call_args[0][0]
        assert "old_format.pdf" in str(call_args)
