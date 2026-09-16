#!/data/data/com.termux/files/home/.local/bin/python
"""fsim.py – Fsim utilities.

This module provides functionality for fsim."""
from __future__ import annotations
from typing import Any
import os
import shutil
import sys
from pathlib import Path
import ssdeep

def get_all_files(root: str='.') -> list[Path]:
    """get_all_files – get all files.

Args:
    root: Description of root."""
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            full_path = os.path.join(dirpath, f)
            paths.append(full_path)
    return paths

def compute_hashes(files: Path | str) -> Any:
    """compute_hashes – compute hashes.

Args:
    files: Description of files."""
    hashes = {}
    for f in files:
        try:
            with Path(f).open('rb') as fh:
                data = fh.read()
                hashes[f] = ssdeep.hash(data)
        except Exception as e:
            print(f'Skipping {f}: {e}')
    return hashes

def group_similar_files(hashes: Any, threshold: int) -> Any:
    """group_similar_files – group similar files.

Args:
    hashes: Description of hashes.
    threshold: Description of threshold."""
    visited = set()
    groups = []
    files = list(hashes.keys())
    for i, f1 in enumerate(files):
        if f1 in visited:
            continue
        group = [f1]
        visited.add(f1)
        for f2 in files[i + 1:]:
            if f2 in visited:
                continue
            score = ssdeep.compare(hashes[f1], hashes[f2])
            if score >= threshold:
                group.append(f2)
                visited.add(f2)
        if len(group) > 1:
            groups.append(group)
    return groups

def copy_groups(groups: Any, output_dir: str='output') -> None:
    """copy_groups – copy groups.

Args:
    groups: Description of groups.
    output_dir: Description of output_dir."""
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    for idx, group in enumerate(groups, start=1):
        group_dir = os.path.join(output_dir, f'group_{idx}')
        Path(group_dir).mkdir(exist_ok=True, parents=True)
        for f in group:
            try:
                shutil.move(f, group_dir)
            except Exception as e:
                print(f'Failed to copy {f}: {e}')

def main() -> None:
    """main – main."""
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <threshold>')
        sys.exit(1)
    try:
        threshold = int(sys.argv[1])
    except ValueError:
        print('Threshold must be an integer (0–100).')
        sys.exit(1)
    files = get_all_files('.')
    print(f'Found {len(files)} files. Computing hashes...')
    hashes = compute_hashes(files)
    print('Comparing files...')
    groups = group_similar_files(hashes, threshold)
    if not groups:
        print('No similar files found.')
    else:
        print(f'Found {len(groups)} groups of similar files.')
        copy_groups(groups)
        print("Copied groups to 'output' directory.")
if __name__ == '__main__':
    raise SystemExit(main())
