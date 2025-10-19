import subprocess
from pathlib import Path


def run_erc(sch: Path):
    out = sch.with_suffix(".erc.txt")
    subprocess.run(["kicad-cli", "sch", "erc", str(sch), "-o", str(out), "--format", "report"], check=False)


def export_netlist(sch: Path):
    out = sch.with_suffix(".net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", str(sch), "-o", str(out)], check=False)


def export_pdf(sch: Path):
    out = sch.with_suffix(".pdf")
    subprocess.run(["kicad-cli", "sch", "export", "pdf", str(sch), "-o", str(out)], check=False)
