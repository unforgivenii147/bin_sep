#!/data/data/com.termux/files/home/.local/bin/python
"""splitt.py – Splitt utilities.

This module provides functionality for splitt."""
from __future__ import annotations
import sys
from pathlib import Path

def split_file_by_delimiter(fname: str, delim: str) -> None:
    """split_file_by_delimiter – split file by delimiter.

Args:
    fname: Description of fname.
    delim: Description of delim."""
    content = Path(fname).read_text(encoding='utf-8')
    path = Path(fname)
    basen = path.stem
    i = 0
    ext = path.suffix
    endl = '\n'
    if not Path('output').exists():
        Path('output').mkdir()
    for part in content.split(delim):
        outfile = f'output/{basen + str(i) + ext}'
        with Path(outfile).open('w', encoding='utf-8') as fo:
            fo.write(delim)
            fo.write(part)
            fo.write(endl)
            i += 1
        print(f'{outfile} created')

def main() -> None:
    """main – main."""
    fn = sys.argv[1]
    delim = sys.argv[2]
    split_file_by_delimiter(fn, delim)
    print('metadata updated.')
if __name__ == '__main__':
    raise SystemExit(main())
