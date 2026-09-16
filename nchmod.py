#!/data/data/com.termux/files/home/.local/bin/python
"""nchmod.py – Nchmod utilities.

This module provides functionality for nchmod."""
from __future__ import annotations
from typing import Any, Iterator
import stat
from pathlib import Path

def get_mode(path: Path) -> int:
    """get_mode – get mode.

Args:
    path: Description of path.

Returns:
    int: Description of return value."""
    return stat.S_IMODE(path.stat().st_mode)

def mkx(filename: Path) -> None:
    """mkx – mkx.

Args:
    filename: Description of filename."""
    original_mode = filename.stat().st_mode
    levels = [stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH]
    for at in range(len(levels), 0, -1):
        try:
            mode = original_mode
            for level in levels[:at]:
                mode |= level
            filename.chmod(mode)
            break
        except OSError:
            continue

def is_exec(path: Path) -> bool:
    """is_exec – is exec.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    return bool(path.stat().st_mode & stat.S_IXUSR)

def get_filez(p: Any) -> Iterator[Any]:
    """get_filez – get filez.

Args:
    p: Description of p."""
    if not p.is_dir():
        yield p
    for f in p.iterdir():
        if f.is_file() and (not f.is_symlink()):
            yield f
        if f.is_dir():
            yield f
            yield from get_filez(f)

def normalize_permissions(cwd: Path) -> None:
    """normalize_permissions – normalize permissions.

Args:
    cwd: Description of cwd."""
    DIR_PERM = 509
    FILE_PERM = 436
    for path in get_filez(cwd):
        if path.is_symlink() or not path.exists():
            continue
        if path.is_file() and (is_exec(path) or 'bin' in path.parts):
            mkx(path)
            continue
        try:
            current_perm = get_mode(path)
            if path.is_dir():
                if current_perm != DIR_PERM:
                    Path(path).chmod(DIR_PERM)
                    print(f'{path.relative_to(cwd)} {oct(current_perm)} : {oct(DIR_PERM)}')
            elif path.is_file():
                if path.suffix in {'.sh', '.so'} and (not is_exec(path)):
                    mkx(path)
                    continue
                if current_perm != FILE_PERM:
                    if path.parent.name != 'bin' and path.suffix != '.sh':
                        path.chmod(FILE_PERM)
                    print(f'{path.relative_to(cwd)}: {oct(current_perm)} --> {oct(FILE_PERM)}')
        except PermissionError as e:
            print(f'Permission denied: {path.name} ({e})')
        except FileNotFoundError:
            continue
        except OSError as e:
            print(f'OS error on {path.name}: {e}')
if __name__ == '__main__':
    cwd = Path.cwd()
    normalize_permissions(cwd)
