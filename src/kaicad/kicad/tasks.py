import subprocess
from pathlib import Path


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
    out = sch.with_suffix(".erc.txt")
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
    out = sch.with_suffix(".net")
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
    out = sch.with_suffix(".pdf")
    return subprocess.run(
        ["kicad-cli", "sch", "export", "pdf", str(sch), "-o", str(out)],
        check=True,
        capture_output=True,
        text=True
    )
