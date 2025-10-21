import logging
import subprocess
from pathlib import Path

from kaicad.kicad.version import check_kicad_cli

logger = logging.getLogger(__name__)


def _ensure_kicad_cli_available() -> None:
    """Check if kicad-cli is available before running commands.
    
    Raises:
        FileNotFoundError: If kicad-cli is not available with helpful message
    """
    is_available, version_or_error = check_kicad_cli()
    if not is_available:
        raise FileNotFoundError(
            f"kicad-cli is not available: {version_or_error}\n"
            "Please install KiCad >= 7.0 and ensure kicad-cli is in your PATH."
        )


def run_erc(sch: Path) -> subprocess.CompletedProcess:
    """
    Run KiCad ERC (Electrical Rules Check) on schematic.
    
    Args:
        sch: Path to .kicad_sch file
        
    Returns:
        CompletedProcess with captured output
        
    Raises:
        CalledProcessError: If kicad-cli returns non-zero exit code
        FileNotFoundError: If kicad-cli is not found in PATH
    """
    _ensure_kicad_cli_available()
    out = sch.with_suffix(".erc.txt")
    logger.info(f"Running ERC on {sch}")
    return subprocess.run(
        ["kicad-cli", "sch", "erc", str(sch), "-o", str(out), "--format", "report"],
        check=True,  # Raise CalledProcessError on failure
        capture_output=True,
        text=True
    )


def export_netlist(sch: Path) -> subprocess.CompletedProcess:
    """
    Export netlist from schematic.
    
    Args:
        sch: Path to .kicad_sch file
        
    Returns:
        CompletedProcess with captured output
        
    Raises:
        CalledProcessError: If kicad-cli returns non-zero exit code
        FileNotFoundError: If kicad-cli is not found in PATH
    """
    _ensure_kicad_cli_available()
    out = sch.with_suffix(".net")
    logger.info(f"Exporting netlist from {sch}")
    return subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", str(sch), "-o", str(out)],
        check=True,
        capture_output=True,
        text=True
    )


def export_pdf(sch: Path) -> subprocess.CompletedProcess:
    """
    Export schematic to PDF.
    
    Args:
        sch: Path to .kicad_sch file
        
    Returns:
        CompletedProcess with captured output
        
    Raises:
        CalledProcessError: If kicad-cli returns non-zero exit code
        FileNotFoundError: If kicad-cli is not found in PATH
    """
    _ensure_kicad_cli_available()
    out = sch.with_suffix(".pdf")
    logger.info(f"Exporting PDF from {sch}")
    return subprocess.run(
        ["kicad-cli", "sch", "export", "pdf", str(sch), "-o", str(out)],
        check=True,
        capture_output=True,
        text=True
    )
