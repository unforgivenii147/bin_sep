#!/data/data/com.termux/files/home/.local/bin/python
"""rmhtml.py – Rmhtml utilities.

This module provides functionality for rmhtml."""
from __future__ import annotations
import re
import sys
from pathlib import Path
from dh import cprint, fsz, get_files, gsz, mpf3
MAX_QUEUE = 8

def process_file(path: Path | str) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    before = gsz(path)
    src = path.read_text(encoding='utf-8')
    pattern = re.compile('<!--[\\s\\S]*?-->', re.MULTILINE)
    out = pattern.sub('', src)
    if out != src:
        code = out.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        path.write_text(code, encoding='utf-8')
    after = gsz(path)
    print(f'[OK] {path.name} ', end='')
    diffsize = before - after
    cprint(f'{fsz(diffsize)}', 'cyan')

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=['.html', '.htm', '.xml'])
    mpf3(process_file, files)
    diff_size = before - gsz(cwd)
    print(f'space saved : {fsz(diff_size)}')
if __name__ == '__main__':
    raise SystemExit(main())
