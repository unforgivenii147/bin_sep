#!/data/data/com.termux/files/home/.local/bin/python
"""joinlines.py – Joinlines utilities.

This module provides functionality for joinlines."""
from __future__ import annotations
from pathlib import Path
from sys import argv

def main() -> None:
    """main – main."""
    nl = ''
    with Path(argv[1]).open(encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                nl += line.strip('\n')
    Path(argv[1]).write_text(nl + '\n', encoding='utf-8')
if __name__ == '__main__':
    raise SystemExit(main())
