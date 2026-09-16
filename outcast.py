#!/data/data/com.termux/files/home/.local/bin/python
"""outcast.py – Outcast utilities.

This module provides functionality for outcast."""
from __future__ import annotations
from typing import Any
from pathlib import Path

def copy_largest_file(source_dir: Path | str, dest: Any) -> None:
    """copy_largest_file – copy largest file.

Args:
    source_dir: Description of source_dir.
    dest: Description of dest."""
    largest = None
    max = -1
    for path in source_dir.iterdir():
        if path.is_file():
            size = path.stat().st_size
            if size > max:
                max = size
                largest = path
    if largest:
        dest.write_bytes(largest.read_bytes())
        print(f'{dest.name} ({max / (1024 * 1024)} MB)')

def get_random_filename(length: int=6) -> str:
    """get_random_filename – get random filename.

Args:
    length: Description of length.

Returns:
    str: Description of return value."""
    from random import choice
    from string import ascii_lowercase
    letters: str = ascii_lowercase
    return ''.join((choice(letters) for _ in range(length)))
if __name__ == '__main__':
    source = Path('/sdcard/Android/data/org.telegram.messenger/cache')
    dest = Path(f'/sdcard/Download/{get_random_filename()}.mkv')
    copy_largest_file(source, dest)
