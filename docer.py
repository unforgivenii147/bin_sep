#!/data/data/com.termux/files/home/.local/bin/python
"""docer.py – Docer utilities.

This module provides functionality for docer."""
from __future__ import annotations
import sys
from pathlib import Path

def process_file(path: Path | str) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    content = path.read_bytes()
    target_dir = Path('/sdcard/doc')
    if not target_dir.exists():
        target_dir.mkdir(exist_ok=True)
    target_path = target_dir / path.name
    if not target_path.exists():
        target_path.write_bytes(content)
        path.unlink()
        print('done.')
    else:
        print(f'target file : {target_path.name} exists. remove it and try again')
if __name__ == '__main__':
    fn = Path(sys.argv[1])
    process_file(fn)
