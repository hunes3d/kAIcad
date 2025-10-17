from pathlib import Path

def read_sym_lib_tables(project_dir: Path) -> list[str]:
    libs = set()
    candidates = [
        project_dir / "sym-lib-table",
        Path.home() / "AppData/Roaming/kicad/9.0/sym-lib-table",  # Windows
        Path.home() / ".config/kicad/9.0/sym-lib-table",          # Linux
        Path("/Library/Preferences/kicad/9.0/sym-lib-table")      # macOS (fallback)
    ]
    for p in candidates:
        try:
            if p.exists():
                txt = p.read_text(encoding="utf-8", errors="ignore")
                libs |= {line.split('"')[1] for line in txt.splitlines() if 'lib (name "' in line}
        except Exception:
            pass
    return sorted(libs)
