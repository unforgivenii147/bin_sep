#!/data/data/com.termux/files/home/.local/bin/python
"""foldesiz.py – Foldesiz utilities.

This module provides functionality for foldesiz."""
from __future__ import annotations
from typing import Any
import operator
import os
import shutil
import sys
from pathlib import Path
from dh import fsz, should_skip, unique_path

def get_all_files(cwd: Path) -> list[Path]:
    """get_all_files – get all files.

Args:
    cwd: Description of cwd."""
    files = []
    for path in cwd.rglob('*'):
        if should_skip(path):
            continue
        if path.is_file():
            size = path.stat().st_size
            files.append((path, size))
    return sorted(files, key=operator.itemgetter(1))

def get_num_folders(files: Path | str) -> int:
    """get_num_folders – get num folders.

Args:
    files: Description of files.

Returns:
    int: Description of return value."""
    if len(files) < 2:
        return 1
    sizes = [size for _, size in files]
    max_size, min_size = (max(sizes), min(sizes))
    range_size = max_size - min_size
    target_range_per_folder = range_size / 100
    num_folders = max(1, int(range_size / target_range_per_folder))
    return min(num_folders, len(files))

def create_range_folders(cwd: Path, files: Path | str, num_folders: int) -> Any:
    """create_range_folders – create range folders.

Args:
    cwd: Description of cwd.
    files: Description of files.
    num_folders: Description of num_folders."""
    sizes = sorted([size for _, size in files])
    folder_ranges = []
    files_per_folder = len(files) // num_folders
    remainder = len(files) % num_folders
    start_idx = 0
    for i in range(num_folders):
        end_idx = start_idx + files_per_folder + (1 if i < remainder else 0)
        folder_files = sizes[start_idx:end_idx]
        if folder_files:
            min_size, max_size = (min(folder_files), max(folder_files))
            folder_name = f'{fsz(min_size)}-{fsz(max_size)}'
            folder_ranges.append((min_size, max_size, folder_name))
            folder_path = os.path.join(cwd, folder_name)
            Path(folder_path).mkdir(exist_ok=True, parents=True)
        start_idx = end_idx
    return folder_ranges

def distribute_files(files: Path | str, folders: Path | str, cwd: Path) -> None:
    """distribute_files – distribute files.

Args:
    files: Description of files.
    folders: Description of folders.
    cwd: Description of cwd."""
    size_to_folder = {}
    for min_size, max_size, folder_name in folders:
        size_to_folder[min_size, max_size] = folder_name
    moved_count = 0
    for path, size in files:
        for (min_size, max_size), folder_name in size_to_folder.items():
            if min_size <= size <= max_size:
                dest_folder = os.path.join(cwd, folder_name)
                dest_path = os.path.join(dest_folder, Path(path).name)
                try:
                    dest_path = unique_path(dest_path)
                    shutil.move(path, dest_path)
                    moved_count += 1
                    break
                except Exception as e:
                    print(f'Failed to move {path}: {e}')
                break
        else:
            print(f'No folder match for {Path(path).name} ({size:,} bytes)')

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    files = get_all_files(cwd)
    if not files:
        print('No files found.')
        return
    num_folders = int(sys.argv[1]) if len(sys.argv) > 0 else get_num_folders(files)
    print(f'{num_folders} dirs will be created')
    folders = create_range_folders(cwd, files, num_folders)
    distribute_files(files, folders, cwd)
    print('Folderization complete!')
if __name__ == '__main__':
    raise SystemExit(main())
