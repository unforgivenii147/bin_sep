#!/data/data/com.termux/files/home/.local/bin/python
"""ltxt.py – Ltxt utilities.

This module provides functionality for ltxt."""
from __future__ import annotations
from typing import Any
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dh import BIN_EXT
EXCLUDED_EXTENSIONS = BIN_EXT

def process_file(path: Path | str) -> Any:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    counter = Counter()
    try:
        with path.open(encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line:
                    counter[line] += 1
    except Exception as e:
        print(f'Error reading {path}: {e}')
    return counter

def collect_files_by_extension() -> Any:
    """collect_files_by_extension – collect files by extension."""
    ext_map = {}
    cwd = Path.cwd()
    for root, _, filenames in cwd.walk():
        for fname in filenames:
            if fname.startswith('.'):
                continue
            path = Path(root) / fname
            ext = path.suffix
            if ext in EXCLUDED_EXTENSIONS:
                continue
            if ext not in ext_map:
                ext_map[ext] = []
            ext_map[ext].append(path)
    return ext_map

def collect_lines_for_extension(ext: str, files: Path | str) -> None:
    """collect_lines_for_extension – collect lines for extension.

Args:
    ext: Description of ext.
    files: Description of files."""
    if not files:
        return
    global_counter = Counter()
    print(f"Processing {len(files)} files with extension '{ext}'")
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(futures):
            try:
                result = future.result()
                global_counter.update(result)
            except Exception as e:
                print(f'Error processing file: {e}')
    output_name = ext.lstrip('.')
    if not output_name:
        output_name = 'no_extension'
    output_file = Path(f'{output_name}.txt')
    with output_file.open('w', encoding='utf-8') as fo:
        written_lines = 0
        for line, count in global_counter.most_common():
            if count >= 2:
                fo.write(line + '\n')
                written_lines += 1
    print(f'Saved {written_lines} duplicate lines to {output_file}')

def main() -> None:
    """main – main."""
    ext_map = collect_files_by_extension()
    if not ext_map:
        print('No eligible files found.')
        return
    for ext, files in ext_map.items():
        collect_lines_for_extension(ext, files)
if __name__ == '__main__':
    raise SystemExit(main())
