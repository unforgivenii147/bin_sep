#!/data/data/com.termux/files/home/.local/bin/python
"""rmlines_with.py – Rmlines With utilities.

This module provides functionality for rmlines with."""
from __future__ import annotations
import sys
from pathlib import Path

def clean_file(path: Path, target: str) -> None:
    """clean_file – clean file.

Args:
    path: Description of path.
    target: Description of target."""
    lines = path.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True)
    cleaned = [p for p in lines if target not in p]
    result = ''.join(cleaned)
    path.write_text(result, encoding='utf-8')

def main() -> None:
    """main – main."""
    fn = Path(sys.argv[1])
    str_to_find = sys.argv[2]
    clean_file(fn, str_to_find)
if __name__ == '__main__':
    raise SystemExit(main())
