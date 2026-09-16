#!/data/data/com.termux/files/home/.local/bin/python
"""list_pkgs_to_zpkg.py – List Pkgs To Zpkg utilities.

This module provides functionality for list pkgs to zpkg."""
from __future__ import annotations
from typing import Any
import sys
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import distributions
from pathlib import Path

def is_pure_python(dist: Any) -> bool:
    """is_pure_python – is pure python.

Args:
    dist: Description of dist.

Returns:
    bool: Description of return value."""
    try:
        if dist.files is None:
            return False
        return not any((f.suffix in {'.so', '.pyd', '.dylib'} for f in dist.files))
    except Exception:
        return False

def has_valid_name(name: str) -> bool:
    """has_valid_name – has valid name.

Args:
    name: Description of name.

Returns:
    bool: Description of return value."""
    return '-' not in name and '_' not in name

def get_top_level_modules(dist: Any) -> set[str]:
    """get_top_level_modules – get top level modules.

Args:
    dist: Description of dist.

Returns:
    set[str]: Description of return value."""
    try:
        if dist.read_text('top_level.txt'):
            return {line.strip() for line in dist.read_text('top_level.txt').splitlines() if line.strip()}
    except (FileNotFoundError, TypeError):
        pass
    if dist.files:
        top_levels = set()
        for file in dist.files:
            parts = file.parts
            if parts and (not parts[0].endswith('.dist-info')):
                top_levels.add(parts[0])
        return top_levels
    return set()

def is_user_site(dist_location: str) -> bool:
    """is_user_site – is user site.

Args:
    dist_location: Description of dist_location.

Returns:
    bool: Description of return value."""
    user_site = Path.home() / '.local' / 'lib'
    try:
        return str(user_site) in str(Path(dist_location).resolve())
    except Exception:
        return False

def check_package(dist: Any) -> str | None:
    """check_package – check package.

Args:
    dist: Description of dist.

Returns:
    str | None: Description of return value."""
    if not is_pure_python(dist):
        return None
    name = dist.name.lower()
    if not has_valid_name(name):
        return None
    if not is_user_site(dist._path):
        return None
    top_levels = get_top_level_modules(dist)
    if len(top_levels) != 1:
        return None
    return dist.name

def main() -> None:
    """main – main."""
    dists = list(distributions())
    with ProcessPoolExecutor() as executor:
        results = [r for r in executor.map(check_package, dists) if r is not None]
    if not results:
        print('No packages found matching criteria.', file=sys.stderr)
        sys.exit(0)
    results.sort(key=str.lower)
    output_path = Path.home() / 'list.txt'
    output_path.write_text('\n'.join(results) + '\n')
    print(f'Saved {len(results)} package names to {output_path}')
if __name__ == '__main__':
    raise SystemExit(main())
