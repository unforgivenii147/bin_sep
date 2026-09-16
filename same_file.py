#!/data/data/com.termux/files/home/.local/bin/python
"""same_file.py – Same File utilities.

This module provides functionality for same file."""
from __future__ import annotations
import sys
from pathlib import Path

def samefile(path1: str, path2: str) -> bool:
    """samefile – samefile.

Args:
    path1: Description of path1.
    path2: Description of path2.

Returns:
    bool: Description of return value."""
    try:
        return Path(path1).samefile(path2)
    except FileNotFoundError:
        return False
    except OSError as e:
        print(f'error: {e}', file=sys.stderr)
        return False
