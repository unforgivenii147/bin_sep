#!/data/data/com.termux/files/home/.local/bin/python
"""rminfo.py – Rminfo utilities.

This module provides functionality for rminfo."""
from __future__ import annotations
import re
from pathlib import Path
HEADER_PATTERN = re.compile('^# Author\\s*:.*\\n# Email\\s*:.*\\n# Time\\s*:.*\\n\\n?', re.MULTILINE)

def strip_header(path: Path) -> bool:
    """Remove the header from a single file. Returns True if modified."""
    text = path.read_text(encoding='utf-8')
    new_text = HEADER_PATTERN.sub('', text, count=1)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        return True
    return False

def main() -> None:
    """main – main."""
    root = Path.cwd()
    modified = 0
    for py_file in root.rglob('*.py'):
        try:
            if strip_header(py_file):
                print(f'Cleaned: {py_file.relative_to(root)}')
                modified += 1
        except (UnicodeDecodeError, OSError) as e:
            print(f'Skipped {py_file}: {e}')
    print(f'\nDone. {modified} file(s) modified.')
if __name__ == '__main__':
    main()
