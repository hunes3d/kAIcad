"""Tests for KiCad version detection."""

import pytest
from kaicad.kicad.version import (
    KiCadVersion,
    parse_kicad_version,
    check_kicad_tools,
)


def test_parse_kicad_version_standard_format():
    """Test parsing standard KiCad version format."""
    version = parse_kicad_version("KiCad 7.0.10")
    assert version is not None
    assert version.major == 7
    assert version.minor == 0
    assert version.patch == 10
    assert version.raw == "7.0.10"
    assert str(version) == "7.0.10"


def test_parse_kicad_version_no_prefix():
    """Test parsing version without 'KiCad' prefix."""
    version = parse_kicad_version("8.0.0")
    assert version is not None
    assert version.major == 8
    assert version.minor == 0
    assert version.patch == 0


def test_parse_kicad_version_invalid():
    """Test parsing invalid version strings."""
    assert parse_kicad_version("invalid") is None
    assert parse_kicad_version("KiCad") is None
    assert parse_kicad_version("7.0") is None
    assert parse_kicad_version("") is None


def test_kicad_version_is_supported():
    """Test version support detection."""
    v7 = KiCadVersion(major=7, minor=0, patch=0, raw="7.0.0")
    assert v7.is_supported is True

    v8 = KiCadVersion(major=8, minor=0, patch=0, raw="8.0.0")
    assert v8.is_supported is True

    v6 = KiCadVersion(major=6, minor=0, patch=0, raw="6.0.0")
    assert v6.is_supported is False


def test_check_kicad_tools():
    """Test KiCad tools availability check."""
    result = check_kicad_tools()
    
    assert isinstance(result, dict)
    assert "kicad_cli_available" in result
    assert "version" in result
    assert "is_supported" in result
    assert "error" in result
    assert "warnings" in result
    
    # Result should be boolean
    assert isinstance(result["kicad_cli_available"], bool)
    assert isinstance(result["is_supported"], bool)
    assert isinstance(result["warnings"], list)


def test_kicad_version_comparison():
    """Test version string representation."""
    v1 = KiCadVersion(major=7, minor=0, patch=10, raw="7.0.10")
    v2 = KiCadVersion(major=8, minor=1, patch=5, raw="8.1.5")
    
    assert str(v1) == "7.0.10"
    assert str(v2) == "8.1.5"
    
    assert v1.major < v2.major
    assert v2.minor > v1.minor


def test_parse_kicad_version_various_formats():
    """Test parsing different version format variations."""
    # With extra text
    v1 = parse_kicad_version("KiCad 7.0.10 (extra text)")
    assert v1 is None  # Currently doesn't handle extra text
    
    # Standard formats
    v2 = parse_kicad_version("7.0.10")
    assert v2 is not None
    assert v2.major == 7
    
    v3 = parse_kicad_version("KiCad 8.0.0")
    assert v3 is not None
    assert v3.major == 8
