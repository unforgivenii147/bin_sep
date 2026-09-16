#!/data/data/com.termux/files/home/.local/bin/python
"""bightml.py – Bightml utilities.

This module provides functionality for bightml."""
from __future__ import annotations
from pathlib import Path
from dh import get_files

def main() -> None:
    """main – main."""
    cwd = Path.home()
    files = get_files(cwd, ext=['.html', '.htm'])
    for f in files:
        if f.stat().st_size > 1024 * 1024:
            print(f.relative_to(cwd))
if __name__ == '__main__':
    raise SystemExit(main())
