#!/data/data/com.termux/files/home/.local/bin/python
"""img2asci.py – Img2Asci utilities.

This module provides functionality for img2asci."""
from __future__ import annotations
import os
import sys
from pathlib import Path
from ascii_magic import AsciiArt
from dh import get_files

def process_file(image_path: Path) -> None:
    """process_file – process file.

Args:
    image_path: Description of image_path."""
    Path(path)
    art = AsciiArt.from_image(image_path)
    art.to_terminal(columns=os.get_terminal_size().columns, width_ratio=2, monochrome=False)

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=['.jpg', '.png', '.bmp', '.webp'])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    pool = Pool(8)
    for _ in pool.imap_unordered(process_file, files):
        pass
    pool.close()
    pool.join()
if __name__ == '__main__':
    raise SystemExit(main())
