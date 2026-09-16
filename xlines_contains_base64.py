#!/data/data/com.termux/files/home/.local/bin/python
"""xlines_contains_base64.py – Xlines Contains Base64 utilities.

This module provides functionality for xlines contains base64."""
from __future__ import annotations
import sys
from pathlib import Path
from dh import get_nobinary

def process_file(path: Path) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    lines = path.read_text(encoding='utf-8').splitlines()
    nl = []
    found = 0
    for line in lines:
        if 'base64,' in line:
            found += 1
            indx = line.index('base64,') + 7
            cleaned = line[indx:]
            if '"' in cleaned:
                end_indx = cleaned.index('"')
                cleaned = cleaned[:end_indx]
            if ' ' in cleaned:
                end_indx = cleaned.index(' ')
                cleaned = cleaned[:end_indx]
            if ')' in cleaned:
                end_indx = cleaned.index(')')
                cleaned = cleaned[:end_indx]
            nl.append(cleaned)
    if found:
        print(f'{path.name} : {found}')
        with Path('b64').open('a', encoding='utf-8') as f:
            f.write('\n')
            f.writelines((f'{k}\n' for k in nl))

def main() -> None:
    """main – main."""
    args = sys.argv[1:]
    cwd = Path.cwd()
    files = [Path(arg) for arg in args] if args else get_nobinary(cwd)
    for f in files:
        process_file(f)
if __name__ == '__main__':
    raise SystemExit(main())
