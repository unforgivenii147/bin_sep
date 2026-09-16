#!/data/data/com.termux/files/home/.local/bin/python
"""pyrgtxt.py – Pyrgtxt utilities.

This module provides functionality for pyrgtxt."""
from __future__ import annotations
from typing import Any
import sys
from pathlib import Path
from joblib import Parallel, delayed

def is_text_file(path: Path | str) -> bool:
    """is_text_file – is text file.

Args:
    path: Description of path."""
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' not in chunk
    except (OSError, PermissionError):
        return False

def search_in_file(path: Path | str, search_string: str) -> list[Any]:
    """search_in_file – search in file.

Args:
    path: Description of path.
    search_string: Description of search_string."""
    try:
        if not is_text_file(path):
            return []
        with open(path, encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if search_string in content:
                return [str(path.relative_to(Path.cwd()))]
    except (OSError, PermissionError, UnicodeDecodeError):
        pass
    return []

def search_in_directory(directory: Path | str, search_string: str, n_jobs: Any=-1) -> Any:
    """search_in_directory – search in directory.

Args:
    directory: Description of directory.
    search_string: Description of search_string.
    n_jobs: Description of n_jobs."""
    files = [f for f in directory.rglob('*') if f.is_file()]
    results = Parallel(n_jobs=n_jobs)((delayed(search_in_file)(file, search_string) for file in files))
    matches = [match for sublist in results for match in sublist]
    return matches
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python search_for.py <search_string>')
        sys.exit(1)
    search_string = sys.argv[1]
    current_dir = Path.cwd()
    print(f"Searching for '{search_string}' in text files under: {current_dir}")
    matches = search_in_directory(current_dir, search_string)
    if matches:
        print('\nFound in:')
        for match in matches:
            print(match)
    else:
        print('\nNo matches found.')
