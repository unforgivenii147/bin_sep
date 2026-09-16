#!/data/data/com.termux/files/home/.local/bin/python
"""binortxt.py – Binortxt utilities.

This module provides functionality for binortxt."""
from __future__ import annotations
from pathlib import Path
from dh import get_files, is_binary, mpf3
cwd = Path.cwd()
bin_dir = Path(f'{cwd}/binary')
bin_dir.mkdir(exist_ok=True)

def process_file(path: Path | str) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    if is_binary(path):
        newpath = bin_dir / path.name
        path.rename(newpath)

def main() -> None:
    """main – main."""
    files = get_files(cwd)
    mpf3(process_file, files)
if __name__ == '__main__':
    raise SystemExit(main())
