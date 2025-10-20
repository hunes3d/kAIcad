"""Input validation utilities for kAIcad web interface."""

import math
import re
from pathlib import Path
from typing import Any, Optional, Tuple

from .constants import (
    ASCII_PRINTABLE_MAX,
    ASCII_PRINTABLE_MIN,
    MAX_API_KEY_LENGTH,
    MAX_FILENAME_LENGTH,
    MAX_MODEL_NAME_LENGTH,
    MAX_PROMPT_LENGTH,
    MIN_API_KEY_LENGTH,
)


def validate_project_path(path_str: str) -> Tuple[bool, str, Path | None]:
    """
    Validate a project path for security and existence.
    
    Args:
        path_str: Path string from user input
        
    Returns:
        Tuple of (is_valid, error_message, resolved_path)
        
    Security checks:
        - No null bytes
        - No path traversal attempts
        - Must exist
        - Must be absolute after resolution
    """
    if not path_str or not path_str.strip():
        return False, "Path cannot be empty", None
    
    path_str = path_str.strip()
    
    # Check for null bytes (security)
    if "\x00" in path_str:
        return False, "Invalid path: contains null bytes", None
    
    # Check for suspicious patterns
    suspicious_patterns = ["../", "..\\", "%2e%2e", "~"]
    if any(pattern in path_str.lower() for pattern in suspicious_patterns):
        return False, "Invalid path: path traversal detected", None
    
    try:
        # Resolve to absolute path
        path = Path(path_str).resolve()
        
        # Verify it exists
        if not path.exists():
            return False, f"Path does not exist: {path}", None
        
        # Verify it's a file or directory
        if not (path.is_file() or path.is_dir()):
            return False, "Path is neither a file nor directory", None
        
        return True, "", path
        
    except (ValueError, OSError, RuntimeError) as e:
        return False, f"Invalid path: {e}", None


def validate_model_name(model: str) -> Tuple[bool, str]:
    """
    Validate model name.
    
    Args:
        model: Model name string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model or not model.strip():
        return False, "Model name cannot be empty"
    
    model = model.strip()
    
    # Must be alphanumeric with hyphens, dots, underscores
    if not re.match(r'^[a-zA-Z0-9._-]+$', model):
        return False, "Invalid model name format"
    
    # Reasonable length limit
    if len(model) > MAX_MODEL_NAME_LENGTH:
        return False, "Model name too long"
    
    return True, ""


def validate_prompt(prompt: str, max_length: int = MAX_PROMPT_LENGTH) -> Tuple[bool, str]:
    """
    Validate user prompt/message.
    
    Args:
        prompt: User input prompt
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    prompt = prompt.strip()
    
    # Check length
    if len(prompt) > max_length:
        return False, f"Prompt too long (max {max_length} characters)"
    
    # Check for null bytes
    if "\x00" in prompt:
        return False, "Invalid prompt: contains null bytes"
    
    return True, ""


def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate API key format.
    
    Args:
        api_key: API key string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    
    api_key = api_key.strip()
    
    # Check for null bytes
    if "\x00" in api_key:
        return False, "Invalid API key: contains null bytes"
    
    # Reasonable length checks (typical API keys are 20-200 chars)
    if len(api_key) < MIN_API_KEY_LENGTH:
        return False, "API key too short"
    
    if len(api_key) > MAX_API_KEY_LENGTH:
        return False, "API key too long"
    
    # Must be printable ASCII (no control characters)
    if not all(ASCII_PRINTABLE_MIN <= ord(c) <= ASCII_PRINTABLE_MAX for c in api_key):
        return False, "API key contains invalid characters"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename (only basename, no path components)
    """
    # Get basename only (removes any path components)
    filename = Path(filename).name
    
    # Remove any remaining suspicious characters
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        filename = filename[:MAX_FILENAME_LENGTH]
    
    return filename


__all__ = [
    "validate_project_path",
    "validate_model_name", 
    "validate_prompt",
    "validate_api_key",
    "sanitize_filename",
    "validate_symbol_name",
    "validate_wire_format",
    "validate_coordinate",
]


def validate_symbol_name(symbol: str) -> Tuple[bool, Optional[str]]:
    """
    Validate KiCad symbol reference format to prevent injection attacks.
    
    Args:
        symbol: Symbol name in format 'Library:Name' (e.g., 'Device:R')
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Security:
        - Prevents path traversal attacks
        - Validates format matches KiCad conventions
        - Blocks path separators and suspicious characters
    """
    if not symbol or not symbol.strip():
        return False, "Symbol name cannot be empty"
    
    # KiCad format: Library:Symbol (e.g., "Device:R")
    if ':' not in symbol:
        return False, "Symbol must be in format 'Library:Name'"
    
    parts = symbol.split(':', 1)
    if len(parts) != 2:
        return False, "Symbol must be in format 'Library:Name'"
    
    lib, name = parts
    
    # Check for empty parts
    if not lib.strip() or not name.strip():
        return False, "Library and symbol name cannot be empty"
    
    # Check for path traversal attacks
    if '..' in lib or '..' in name:
        return False, "Symbol name contains path traversal"
    
    if '/' in symbol or '\\' in symbol:
        return False, "Symbol name contains path separators"
    
    # Allow alphanumeric, dash, underscore, plus, dot (common in KiCad)
    # Also allow spaces for symbol names like "Device:LED RGB"
    if not re.match(r'^[a-zA-Z0-9_\-+. ]+:[a-zA-Z0-9_\-+. ]+$', symbol):
        return False, "Symbol name contains invalid characters"
    
    # Check length limits
    if len(symbol) > 200:  # Reasonable limit for symbol names
        return False, "Symbol name too long (max 200 characters)"
    
    return True, None


def validate_wire_format(wire_spec: str) -> Tuple[bool, Optional[str], Optional[Tuple[str, str]]]:
    """
    Validate wire specification format 'REF:PIN'.
    
    Args:
        wire_spec: Wire specification like 'R1:1' or 'U1:VCC'
        
    Returns:
        Tuple of (is_valid, error_message, (ref, pin) or None)
    """
    if not wire_spec or not wire_spec.strip():
        return False, "Wire specification cannot be empty", None
    
    if ':' not in wire_spec:
        return False, f"Wire format must be 'REF:PIN', got '{wire_spec}'", None
    
    parts = wire_spec.split(':', 1)
    if len(parts) != 2:
        return False, f"Wire format must be 'REF:PIN', got '{wire_spec}'", None
    
    ref, pin = parts
    
    # Validate reference (like R1, U5, C10)
    if not ref.strip():
        return False, "Component reference cannot be empty", None
    
    if not re.match(r'^[A-Z]+[0-9]+$', ref.strip()):
        return False, f"Invalid component reference '{ref}' (expected format: R1, U5, C10)", None
    
    # Validate pin (can be number or name like VCC, GND, A, 1, 2)
    if not pin.strip():
        return False, "Pin name/number cannot be empty", None
    
    if len(pin) > 50:  # Reasonable limit
        return False, "Pin name too long", None
    
    return True, None, (ref.strip(), pin.strip())


def validate_coordinate(coord: Any) -> Tuple[bool, Optional[str], Optional[Tuple[float, float]]]:
    """
    Validate coordinate format [x, y] and convert to floats.
    
    Args:
        coord: Coordinate value (should be list/tuple of 2 numbers)
        
    Returns:
        Tuple of (is_valid, error_message, (x, y) or None)
    """
    # Check if iterable
    if not isinstance(coord, (list, tuple)):
        return False, f"Coordinate must be [x, y], got {type(coord).__name__}", None
    
    # Check length
    if len(coord) != 2:
        return False, f"Coordinate must have exactly 2 values, got {len(coord)}", None
    
    # Try to convert to floats
    try:
        x = float(coord[0])
        y = float(coord[1])
    except (ValueError, TypeError) as e:
        return False, f"Coordinate values must be numbers: {e}", None
    
    # Check for NaN and infinity
    if not (math.isfinite(x) and math.isfinite(y)):
        return False, "Coordinate values must be finite numbers", None
    
    # Check bounds (KiCad practical limits)
    MAX_COORD = 1000000.0
    if abs(x) > MAX_COORD or abs(y) > MAX_COORD:
        return False, f"Coordinate values exceed maximum {MAX_COORD}", None
    
    return True, None, (x, y)
