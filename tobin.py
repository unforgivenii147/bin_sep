#!/data/data/com.termux/files/home/.local/bin/python
"""tobin.py – Tobin utilities.

This module provides functionality for tobin."""
from __future__ import annotations
import sys
from hashlib import sha256
from pathlib import Path
CHUNK_SIZE = 32768
dest = Path.home() / 'sbin'

def get_sha256(path: str | Path) -> str:
    """get_sha256 – get sha256.

Args:
    path: Description of path.

Returns:
    str: Description of return value."""
    path = Path(path)
    h = sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b''):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    """main – main."""
    fn = Path(sys.argv[1])
    dest_path = dest / fn.name
    if dest_path.exists():
        print('target exists')
        if get_sha256(dest_path) == get_sha256(fn):
            print('the target hash and source are equal')
            fn.unlink()
            sys.exit(1)
    fn.rename(dest_path)
if __name__ == '__main__':
    raise SystemExit(main())
