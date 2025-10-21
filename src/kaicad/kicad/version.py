"""KiCad version detection and validation utilities."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class KiCadVersion:
    """Represents a KiCad version."""

    major: int
    minor: int
    patch: int
    raw: str

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def is_supported(self) -> bool:
        """Check if this version is supported (>= 7.0.0)."""
        return self.major >= 7


def check_kicad_cli() -> Tuple[bool, str]:
    """Check if kicad-cli is available and get version.

    Returns:
        Tuple of (is_available, version_or_error_message)
    """
    try:
        result = subprocess.run(
            ["kicad-cli", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        version_output = result.stdout.strip()
        logger.info(f"Found kicad-cli: {version_output}")
        return True, version_output
    except FileNotFoundError:
        error_msg = (
            "kicad-cli not found in PATH. Please install KiCad >= 7.0 "
            "and ensure kicad-cli is accessible."
        )
        logger.warning(error_msg)
        return False, error_msg
    except subprocess.TimeoutExpired:
        error_msg = "kicad-cli command timed out"
        logger.error(error_msg)
        return False, error_msg
    except subprocess.CalledProcessError as e:
        error_msg = f"kicad-cli failed: {e.stderr}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error checking kicad-cli: {e}"
        logger.error(error_msg)
        return False, error_msg


def parse_kicad_version(version_string: str) -> Optional[KiCadVersion]:
    """Parse KiCad version string.

    Args:
        version_string: Output from 'kicad-cli --version'

    Returns:
        KiCadVersion object or None if parsing fails

    Examples:
        >>> parse_kicad_version("KiCad 7.0.10")
        KiCadVersion(major=7, minor=0, patch=10, raw='7.0.10')
        >>> parse_kicad_version("KiCad 8.0.0")
        KiCadVersion(major=8, minor=0, patch=0, raw='8.0.0')
    """
    try:
        # Expected format: "KiCad X.Y.Z" or just "X.Y.Z"
        parts = version_string.split()
        version_part = parts[-1] if parts else version_string

        # Split version numbers
        version_numbers = version_part.split(".")
        if len(version_numbers) < 3:
            logger.warning(f"Could not parse version: {version_string}")
            return None

        major = int(version_numbers[0])
        minor = int(version_numbers[1])
        patch = int(version_numbers[2])

        return KiCadVersion(major=major, minor=minor, patch=patch, raw=version_part)
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse KiCad version '{version_string}': {e}")
        return None


def get_kicad_version() -> Optional[KiCadVersion]:
    """Get parsed KiCad version.

    Returns:
        KiCadVersion object or None if KiCad not found or version cannot be parsed
    """
    is_available, version_string = check_kicad_cli()
    if not is_available:
        return None

    return parse_kicad_version(version_string)


def check_kicad_tools() -> dict:
    """Check availability of KiCad CLI tools.

    Returns:
        Dictionary with tool availability and version information
    """
    kicad_cli_available, version_or_error = check_kicad_cli()
    version = parse_kicad_version(version_or_error) if kicad_cli_available else None

    return {
        "kicad_cli_available": kicad_cli_available,
        "version": str(version) if version else None,
        "version_object": version,
        "is_supported": version.is_supported if version else False,
        "error": None if kicad_cli_available else version_or_error,
        "warnings": _get_version_warnings(version) if version else [],
    }


def _get_version_warnings(version: Optional[KiCadVersion]) -> list[str]:
    """Get warnings about KiCad version."""
    if version is None:
        return ["Could not detect KiCad version"]

    warnings = []
    if not version.is_supported:
        warnings.append(
            f"KiCad {version} is not fully supported. Please upgrade to KiCad >= 7.0"
        )

    if version.major == 7 and version.minor == 0 and version.patch < 10:
        warnings.append(
            f"KiCad {version} may have stability issues. Consider upgrading to 7.0.10 or later"
        )

    return warnings


# Public API
__all__ = [
    "KiCadVersion",
    "check_kicad_cli",
    "get_kicad_version",
    "parse_kicad_version",
    "check_kicad_tools",
]
