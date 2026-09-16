#!/data/data/com.termux/files/home/.local/bin/python
"""extz.py – Extz utilities.

This module provides functionality for extz."""
from __future__ import annotations
from typing import Any, Iterator
from collections import Counter
from pathlib import Path

def walk_files(directory: Path | str) -> Iterator[Any]:
    """walk_files – walk files.

Args:
    directory: Description of directory."""
    for entry in directory.iterdir():
        if entry.is_symlink():
            continue
        if entry.name == '.git':
            continue
        if entry.is_file():
            yield entry
        elif entry.is_dir():
            yield from walk_files(entry)

def main() -> None:
    """main – main."""
    current_dir = Path.cwd()
    extension_counter = Counter()
    for path in walk_files(current_dir):
        ext = path.suffix if path.suffix else '.no_ext'
        extension_counter[ext] += 1
    if extension_counter:
        max_ext_len = max((len(ext) for ext in extension_counter))
        max_count_len = max((len(str(count)) for count in extension_counter.values()))
        print('extensions found:')
        for ext, count in sorted(extension_counter.items()):
            print(f' {ext:<{max_ext_len}}  {count:>{max_count_len}} files')
    else:
        print('No files found.')
if __name__ == '__main__':
    main()
