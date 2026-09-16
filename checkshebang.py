#!/data/data/com.termux/files/home/.local/bin/python
"""checkshebang.py – Checkshebang utilities.

This module provides functionality for checkshebang."""
from __future__ import annotations
from pathlib import Path

def fix_file(path: Path) -> bool:
    """fix_file – fix file.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    text = path.read_text(encoding='utf-8', errors='ignore')
    lines = text.splitlines(keepends=False)
    if not lines:
        return False
    i = 0
    for line in lines:
        if line.startswith('#!'):
            i += 1
    return i > 1

def main() -> None:
    """main – main."""
    fixed = 0
    cwd = Path.cwd()
    for file in cwd.rglob('*.py'):
        if fix_file(file):
            fixed += 1
            print(f'{file} has 2 shebang')
    print(f'\nDone. Updated {fixed} files.')
if __name__ == '__main__':
    raise SystemExit(main())
