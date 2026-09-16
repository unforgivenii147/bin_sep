#!/data/data/com.termux/files/home/.local/bin/python
"""check_double_shebang.py – Check Double Shebang utilities.

This module provides functionality for check double shebang."""
from __future__ import annotations
import sys
from pathlib import Path
from dh import get_files

def process_file(path: Path) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    if path.is_symlink():
        return
    content = path.read_text()
    lines = content.splitlines()
    c = 0
    for line in lines:
        if line.startswith('#!'):
            c += 1
    if c > 1:
        print(path.name)

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    args = sys.argv[1:]
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                files.append(p)
            if p.is_dir():
                files.extend(get_files(p))
    else:
        files = get_files(cwd, ext=['.py'])
    for f in files:
        process_file(f)
if __name__ == '__main__':
    raise SystemExit(main())
