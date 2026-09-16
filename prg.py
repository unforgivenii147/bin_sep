#!/data/data/com.termux/files/home/.local/bin/python
"""prg.py – Prg utilities.

This module provides functionality for prg."""
from __future__ import annotations
from typing import Any
import argparse
import re
from collections.abc import Generator
from multiprocessing import Pool
from pathlib import Path
from binaryornot import is_binary
from dh import BIN_EXT, TXT_EXT
from fastwalk import walk_files

def walk_paths(paths: list[str | Path]) -> Generator[Path, None, None]:
    """walk_paths – walk paths.

Args:
    paths: Description of paths.

Returns:
    Generator[Path, None, None]: Description of return value."""
    for path_str in paths:
        path = Path(path_str)
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from walk_files(path)

def search_file(path: Path, pattern: str) -> Generator[tuple[Path, int, str], None, None]:
    """search_file – search file.

Args:
    path: Description of path.
    pattern: Description of pattern.

Returns:
    Generator[tuple[Path, int, str], None, None]: Description of return value."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                matches = list(re.finditer(pattern, line))
                if matches:
                    colorized = colorize_line(line.rstrip('\n'), matches)
                    yield (path, line_num, colorized)
    except OSError:
        pass

def colorize_line(line: str, matches: Any) -> str:
    """colorize_line – colorize line.

Args:
    line: Description of line.
    matches: Description of matches.

Returns:
    str: Description of return value."""
    if not matches:
        return line
    parts = []
    last_end = 0
    for match in sorted(matches, key=lambda m: m.start()):
        start, end = match.span()
        parts.append(line[last_end:start])
        parts.append(f'\x1b[91m{line[start:end]}\x1b[0m')
        last_end = end
    parts.append(line[last_end:])
    return ''.join(parts)

def ripgrep(paths: list[str | Path], pattern: str, max_workers: int=8) -> Any:
    """ripgrep – ripgrep.

Args:
    paths: Description of paths.
    pattern: Description of pattern.
    max_workers: Description of max_workers."""

    def process_file(path: Path) -> Any:
        """process_file – process file.

Args:
    path: Description of path."""
        if is_binary(path) or path.suffix not in TXT_EXT or path.suffix in BIN_EXT:
            return []
        print(f'-> {path.name} ... ')
        return list(search_file(path, pattern))
    results = []
    with Pool(8) as p:
        results = p.map(process_file, files)
    for result in results:
        for path, line_num, colorized_line in result:
            print(f'{path}({line_num}) {colorized_line}')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ripgrep-like search tool')
    parser.add_argument('pattern', help='Search pattern (regex)')
    parser.add_argument('paths', nargs='*', default=['.'], help='Files or directories to search')
    parser.add_argument('-w', '--workers', type=int, default=4, help='Number of parallel workers')
    args = parser.parse_args()
    ripgrep(args.paths, args.pattern, args.workers)
