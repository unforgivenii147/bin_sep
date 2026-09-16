#!/data/data/com.termux/files/home/.local/bin/python
"""cliner2.py – Cliner2 utilities.

This module provides functionality for cliner2."""
from __future__ import annotations
import re
from pathlib import Path
LOG_EXT = '.log'
PATTERNS = ['\\^\\[', '\\[[\\dA-Z;]+m', '\\[\\d+[A-Z]', '\\[[\\dA-Z;]+', '\\^M', '\\(B', '\\(0', '\\x1b\\[[0-9;]*[A-Za-z]', '\\x1b\\([0-9AB]', '\\r', '\\x0f', '\\x0e']

def clean_line(line: str) -> str:
    """clean_line – clean line.

Args:
    line: Description of line.

Returns:
    str: Description of return value."""
    cleaned = line
    for pattern in PATTERNS:
        cleaned = re.sub(pattern, '', cleaned)
    return re.sub(' {2,}', ' ', cleaned)

def clean_file(path: Path) -> None:
    """clean_file – clean file.

Args:
    path: Description of path."""
    try:
        with Path(path).open(encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        cleaned_lines = [clean_line(line) for line in lines]
        with Path(path).open('w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        print(f'✓ Cleaned: {path}')
    except Exception as e:
        print(f'✗ Error processing {path}: {e}')

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    log_files = list(cwd.rglob(f'*{LOG_EXT}'))
    if not log_files:
        print(f'No {LOG_EXT} files found.')
        return
    print(f'Found {len(log_files)} log file(s). Cleaning...\n')
    for log_file in log_files:
        clean_file(log_file)
    print(f'\nDone. Processed {len(log_files)} file(s).')
if __name__ == '__main__':
    raise SystemExit(main())
