#!/data/data/com.termux/files/home/.local/bin/python
"""clean_req.py – Clean Req utilities.

This module provides functionality for clean req."""
from __future__ import annotations
import re
import sys
from pathlib import Path
_VERSION_OP_RE = re.compile('\\s*(?:===|==|!=|>=|<=|~=|>|<)\\s*')

def clean_requirement(line: str) -> str:
    """clean_requirement – clean requirement.

Args:
    line: Description of line.

Returns:
    str: Description of return value."""
    line = line.split('#', 1)[0].strip()
    if not line:
        return ''
    line = line.split(';', 1)[0].strip()
    if not line:
        return ''
    line = re.sub('\\[.*?\\]', '', line).strip()
    if not line:
        return ''
    parts = _VERSION_OP_RE.split(line, maxsplit=1)
    return parts[0].strip()

def group_key(name: str) -> tuple[int, str]:
    """group_key – group key.

Args:
    name: Description of name.

Returns:
    tuple[int, str]: Description of return value."""
    first = name[0]
    if first.isupper():
        return (0, name)
    if first.islower():
        return (1, name)
    return (2, name)

def main() -> None:
    """main – main."""
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} requirements.txt', file=sys.stderr)
        sys.exit(1)
    fname = sys.argv[1]
    try:
        with Path(fname).open(encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.", file=sys.stderr)
        sys.exit(1)
    cleaned = []
    seen = set()
    for line in lines:
        c = clean_requirement(line)
        if c and c not in seen:
            cleaned.append(c)
            seen.add(c)
    cleaned = sorted(cleaned, key=group_key)
    with Path(fname).open('w', encoding='utf-8') as f:
        f.writelines((item + '\n' for item in cleaned))
    print('\n=== Cleaned Requirements ===')
    for item in cleaned:
        print(item)
if __name__ == '__main__':
    raise SystemExit(main())
