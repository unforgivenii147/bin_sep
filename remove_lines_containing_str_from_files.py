#!/data/data/com.termux/files/home/.local/bin/python
"""remove_lines_containing_str_from_files.py – Remove Lines Containing Str From Files utilities.

This module provides functionality for remove lines containing str from files."""
from __future__ import annotations
import sys
from pathlib import Path
from dh import get_nobinary, gsz
STRTOFIND = ['dist-info', '.so', '.py', '.pth', '__', '.zip']

def clean_text(text: str) -> str:
    """clean_text – clean text.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""
    return '\n'.join((line for line in text.splitlines() if not any((s in line for s in STRTOFIND))))

def clean_file(path: str) -> None:
    """clean_file – clean file.

Args:
    path: Description of path."""
    try:
        original = Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return
    cleaned = clean_text(original)
    if cleaned != original:
        Path(path).write_text(cleaned, encoding='utf-8')

def main() -> None:
    """main – main."""
    root = Path.cwd()
    isz = gsz(root)
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_nobinary(root)
    if len(files) == 1:
        clean_file(files[0])
        sys.exit(0)
    pool = Pool(8)
    for f in files:
        p.apply_async(clean_file, (f,))
    pool.close()
    pool.join()
    esz = gsz(root)
    diffsize = isz - esz
    print(f'space freed : {fsz(diffsize)}')
if __name__ == '__main__':
    raise SystemExit(main())
