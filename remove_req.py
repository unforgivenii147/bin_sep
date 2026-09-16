#!/data/data/com.termux/files/home/.local/bin/python
"""remove_req.py – Remove Req utilities.

This module provides functionality for remove req."""
from __future__ import annotations
import sys
from pathlib import Path

def process_file(path: Path, text: str) -> None:
    """process_file – process file.

Args:
    path: Description of path.
    text: Description of text."""
    path = Path(path)
    content = path.read_text()
    target = 'Requires-Dist: ' + text
    if target in content:
        lines = content.splitlines()
        nl = [line for line in lines if target not in line]
        newcontent = '\n'.join(nl)
        path.write_text(newcontent, encoding='utf-8')
        print(f'{path.parent.name} updated.')
if __name__ == '__main__':
    major, minor, _, _, _ = sys.version_info
    py_version = f'{major}{minor}'
    cwd = Path(f'/data/data/com.termux/files/usr/lib/python{py_version}/site-packages')
    target = sys.argv[1]
    for path in cwd.rglob('METADATA'):
        process_file(path, target)
