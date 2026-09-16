#!/data/data/com.termux/files/home/.local/bin/python
"""faprinter.py – Faprinter utilities.

This module provides functionality for faprinter."""
from __future__ import annotations
from typing import Any, Iterator
import sys
from pathlib import Path
from faprint import faprint as pp

def ylines(path: Path) -> Iterator[Any]:
    """ylines – ylines.

Args:
    path: Description of path."""
    with path.open(encoding='utf-8') as f:
        yield from f
if __name__ == '__main__':
    fn = Path(sys.argv[1])
    for k in ylines(fn):
        print(pp(k))
