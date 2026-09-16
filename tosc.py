#!/data/data/com.termux/files/home/.local/bin/python
"""tosc.py – Tosc utilities.

This module provides functionality for tosc."""
from __future__ import annotations
import shutil
import sys
from pathlib import Path
from dh import unique_path
dest = Path.home() / 'isaac' / 'may' / 'scripts'

def main() -> None:
    """main – main."""
    fn = Path(sys.argv[1])
    dest_path = dest / fn.name
    if dest_path.exists():
        dest_path = unique_path(dest_path)
    shutil.move(str(fn), str(dest_path))
    print(f'{fn.name} --> {dest_path.name}')
if __name__ == '__main__':
    raise SystemExit(main())
