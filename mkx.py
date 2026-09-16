#!/data/data/com.termux/files/home/.local/bin/python
"""mkx.py – Mkx utilities.

This module provides functionality for mkx."""
from __future__ import annotations
import re
import stat
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dh import is_binary

def has_shebang(path: Path) -> bool:
    """has_shebang – has shebang.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    try:
        with path.open('rb') as f:
            return f.read(2) == b'#!'
    except (OSError, PermissionError):
        return False

def is_shared_object(path: Path) -> bool:
    """is_shared_object – is shared object.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    return bool(re.match('.*\\.so(?:\\.\\d+)*$', path.name))

def make_exec(path: Path) -> None:
    """make_exec – make exec.

Args:
    path: Description of path."""
    try:
        current = path.stat().st_mode
        path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass

def is_exec(path: Path) -> bool:
    """is_exec – is exec.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    try:
        return bool(path.stat().st_mode & stat.S_IXUSR)
    except OSError:
        return False

def should_be_executable(path: Path) -> bool:
    """should_be_executable – should be executable.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    if path.parent.name in {'sbin', 'bin', '.bin'}:
        return True
    if is_shared_object(path):
        return True
    if has_shebang(path):
        return True
    return bool(not path.suffix and is_binary(path))

def process_file(path: Path, cwd: Path) -> str | None:
    """process_file – process file.

Args:
    path: Description of path.
    cwd: Description of cwd.

Returns:
    str | None: Description of return value."""
    if path.is_file() and (not is_exec(path)) and should_be_executable(path):
        make_exec(path)
        return f'[+] Made executable: {path.relative_to(cwd)}'
    return None

def process_directory(cwd: Path, workers: int=4) -> None:
    """process_directory – process directory.

Args:
    cwd: Description of cwd.
    workers: Description of workers."""
    files = [p for p in cwd.rglob('*') if p.is_file() and '.git' not in p.parts and (not p.is_symlink())]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, f, cwd): f for f in files}
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(result)
if __name__ == '__main__':
    process_directory(Path.cwd())
