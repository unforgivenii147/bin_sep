#!/data/data/com.termux/files/home/.local/bin/python
"""cairosvg2pdf.py – Cairosvg2Pdf utilities.

This module provides functionality for cairosvg2pdf."""
from __future__ import annotations
import sys
from pathlib import Path
import cairosvg
from dh import cprint, fsz, get_files, gsz

def process_file(path: Path) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    try:
        outfile = path.with_suffix('.pdf')
        cairosvg.svg2pdf(url=str(path), write_to=str(outfile))
    except:
        return

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    before = gsz(cwd)
    args = sys.argv[1:]
    files = [Path(f) for f in args] if args else get_files(cwd, ext=['.svg'])
    for f in files:
        process_file(f)
    diff_size = before - gsz(cwd)
    cprint(f'space saved : {fsz(diff_size)}', 'cyan')
if __name__ == '__main__':
    raise SystemExit(main())
