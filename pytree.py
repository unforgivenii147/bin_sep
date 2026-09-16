#!/data/data/com.termux/files/home/.local/bin/python
"""pytree.py – Pytree utilities.

This module provides functionality for pytree."""
from __future__ import annotations
import argparse
import sys
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from dh import fsz, gsz

def walk_filesystem(root: Path, max_workers: int=4) -> Generator[tuple[Path, bool], None, None]:
    """walk_filesystem – walk filesystem.

Args:
    root: Description of root.
    max_workers: Description of max_workers.

Returns:
    Generator[tuple[Path, bool], None, None]: Description of return value."""

    def process_entry(entry: Path) -> tuple[Path, bool]:
        """process_entry – process entry.

Args:
    entry: Description of entry.

Returns:
    tuple[Path, bool]: Description of return value."""
        is_dir = entry.is_dir()
        if is_dir:
            return (entry, True)
        return (entry, False)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for entry in root.rglob('*'):
            if entry.name.startswith('.') or '.git' in entry.parts:
                continue
            futures.append(executor.submit(process_entry, entry))
        for future in futures:
            yield future.result()

def tree(root: Path, show_sizes: bool=False, dirs_only: bool=False, human_readable: bool=False, max_workers: int=4) -> None:
    """tree – tree.

Args:
    root: Description of root.
    show_sizes: Description of show_sizes.
    dirs_only: Description of dirs_only.
    human_readable: Description of human_readable.
    max_workers: Description of max_workers."""
    entries = sorted(walk_filesystem(root, max_workers), key=lambda x: (not x[1], x[0]))

    def print_entry(entry: Path, is_dir: bool, prefix: str='') -> None:
        """print_entry – print entry.

Args:
    entry: Description of entry.
    is_dir: Description of is_dir.
    prefix: Description of prefix."""
        if dirs_only and (not is_dir):
            return
        size_str = ''
        if show_sizes:
            size = gsz(entry) if is_dir else entry.stat().st_size
            size_str = f' [{(fsz(size) if human_readable else size)}]'
        print(f"{prefix}{('└── ' if prefix else '')}{entry.name}{size_str}")
    for entry, is_dir in entries:
        if entry == root:
            print(entry.name)
            continue
        parts = list(entry.relative_to(root).parts)
        prefix = ''
        for i, _part in enumerate(parts[:-1]):
            prefix += '    ' if i == len(parts) - 2 else '│   '
        print_entry(entry, is_dir, prefix)

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Python tree command implementation')
    parser.add_argument('directory', nargs='?', default='.', help='Directory to traverse')
    parser.add_argument('-s', '--sizes', action='store_true', help='Show sizes')
    parser.add_argument('-d', '--dirs-only', action='store_true', help='List directories only')
    parser.add_argument('-H', '--human-readable', action='store_true', help='Human-readable sizes')
    parser.add_argument('-j', '--jobs', type=int, default=8, help='Number of parallel workers')
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    if not root.exists():
        print(f'Error: {root} does not exist', file=sys.stderr)
        sys.exit(1)
    tree(root, args.sizes, args.dirs_only, args.human_readable, args.jobs)
if __name__ == '__main__':
    raise SystemExit(main())
