#!/data/data/com.termux/files/home/.local/bin/python
"""strip_stdlib.py – Strip Stdlib utilities.

This module provides functionality for strip stdlib."""
from __future__ import annotations
import sys
from pathlib import Path
from dh import STDLIB

def read_requirements(filename: Path | str) -> list[str]:
    """read_requirements – read requirements.

Args:
    filename: Description of filename.

Returns:
    list[str]: Description of return value."""
    req_file = Path(filename)
    with Path(req_file).open(encoding='utf-8') as f:
        return [line.strip().replace('-', '_').lower() for line in f if line.strip() and (not line.startswith('#'))]

def strip_stdlib(fname: str) -> None:
    """strip_stdlib – strip stdlib.

Args:
    fname: Description of fname."""
    lines = read_requirements(fname)
    new_lines = [line for line in lines if line not in STDLIB]
    Path(fname).write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    removed = len(lines) - len(new_lines)
    print(f'Removed {removed} packages')
if __name__ == '__main__':
    fn = sys.argv[1]
    strip_stdlib(fn)
