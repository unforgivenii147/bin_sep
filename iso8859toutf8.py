#!/data/data/com.termux/files/home/.local/bin/python
"""iso8859toutf8.py – Iso8859Toutf8 utilities.

This module provides functionality for iso8859toutf8."""
from __future__ import annotations
from pathlib import Path
import codecs
import shutil

def convert_in_place(filename: Path | str) -> None:
    """convert_in_place – convert in place.

Args:
    filename: Description of filename."""
    backup = f'{filename}.bak'
    shutil.copy2(filename, backup)
    with codecs.open(backup, 'r', encoding='iso-8859-1') as f:
        content = f.read()
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Converted {filename} (backup saved as {backup})')
if __name__ == '__main__':
    convert_in_place('script.sh')
