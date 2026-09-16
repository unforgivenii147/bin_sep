#!/data/data/com.termux/files/home/.local/bin/python
"""clean_version.py – Clean Version utilities.

This module provides functionality for clean version."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
PKG_NAME_RE = re.compile('\n    ^\\s*\n    (?:\n        -e\\s+\n    )?\n    (?P<name>[A-Za-z0-9_.\\-]+)\n    ', re.VERBOSE)

def extract_package_name(line: str) -> str | None:
    """extract_package_name – extract package name.

Args:
    line: Description of line.

Returns:
    str | None: Description of return value."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    if line.startswith(('git+', 'http://', 'https://')):
        return None
    if '@' in line:
        name = line.split('@', 1)[0].strip()
        return name or None
    match = PKG_NAME_RE.match(line)
    if match:
        return match.group('name')
    return None

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Clean pip freeze output and keep only package names (overwrite file).')
    parser.add_argument('file', help='pip freeze output file')
    args = parser.parse_args()
    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(msg)
    lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    packages = []
    for line in lines:
        name = extract_package_name(line)
        if name:
            packages.append(name)
    seen = set()
    cleaned = [p for p in packages if not (p in seen or seen.add(p))]
    path.write_text('\n'.join(cleaned) + '\n', encoding='utf-8')
if __name__ == '__main__':
    raise SystemExit(main())
