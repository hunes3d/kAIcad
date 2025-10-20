"""File backup utilities for kAIcad."""

import shutil
import tempfile
from pathlib import Path
from typing import Tuple


def create_backup_atomic(file_path: Path) -> Path:
    """
    Create a backup file atomically.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to the backup file
        
    Raises:
        IOError: If backup fails
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    
    # Use shutil.copy2 to preserve metadata
    shutil.copy2(file_path, backup_path)
    
    return backup_path


def write_file_atomic(file_path: Path, content: str) -> None:
    """
    Write file content atomically using temporary file and rename.
    
    Args:
        file_path: Destination file path
        content: Content to write
        
    Raises:
        IOError: If write fails
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file in same directory for atomic rename
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        dir=file_path.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    # Atomic rename (POSIX) or near-atomic (Windows)
    tmp_path.replace(file_path)


def backup_and_write_schematic(
    sch_path: Path,
    schematic_obj,
    create_backup: bool = True
) -> Tuple[bool, str]:
    """
    Backup and write schematic file atomically.
    
    Args:
        sch_path: Path to schematic file
        schematic_obj: Schematic object with to_file() method
        create_backup: Whether to create backup
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create backup if requested
        if create_backup:
            backup_path = create_backup_atomic(sch_path)
        
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=sch_path.parent,
            delete=False,
            suffix='.tmp'
        ) as tmp:
            tmp_path = Path(tmp.name)
        
        # Use schematic's to_file method
        schematic_obj.to_file(str(tmp_path))
        
        # Atomic rename
        tmp_path.replace(sch_path)
        
        return True, "Schematic saved successfully"
        
    except Exception as e:
        return False, f"Failed to save schematic: {e}"
