#!/data/data/com.termux/files/home/.local/bin/python
"""pyjtc.py – Pyjtc utilities.

This module provides functionality for pyjtc."""
from __future__ import annotations
from typing import Any
import argparse
import re
from pathlib import Path

def remove_comments_and_strings(content: str, filetype: str, keep_strings: bool=False) -> Any:
    """remove_comments_and_strings – remove comments and strings.

Args:
    content: Description of content.
    filetype: Description of filetype.
    keep_strings: Description of keep_strings."""
    if filetype in {'c', 'cpp', 'h', 'hpp'}:
        content = re.sub('//.*', '', content)
        content = re.sub('/\\*.*?\\*/', '', content, flags=re.DOTALL)
        if not keep_strings:
            content = re.sub('\\"[^\\"]*\\"', '', content)
            content = re.sub("'[^']*'", '', content)
    elif filetype == 'py':
        content = re.sub('#.*', '', content)
        content = re.sub('\\"\\"\\"[\\s\\S]*?\\"\\"\\"', '', content)
        content = re.sub("'''[\\s\\S]*?'''", '', content)
        if not keep_strings:
            content = re.sub('\\"[^\\"]*\\"', '', content)
            content = re.sub("'[^']*'", '', content)
    elif filetype == 'sh':
        content = re.sub('#.*', '', content)
        if not keep_strings:
            content = re.sub('\\"[^\\"]*\\"', '', content)
            content = re.sub("'[^']*'", '', content)
    return content

def process_file(path: Path | str, inplace: bool=False, keep_strings: bool=False) -> None:
    """process_file – process file.

Args:
    path: Description of path.
    inplace: Description of inplace.
    keep_strings: Description of keep_strings."""
    p = Path(path)
    ext = p.suffix[1:].lower()
    if ext not in {'hpp', 'h', 'c', 'cpp', 'py', 'sh'}:
        print(f'Unsupported file type: {ext}')
        return
    content = p.read_text(encoding='utf-8')
    cleaned = remove_comments_and_strings(content, ext, keep_strings)
    if inplace:
        p.write_text(cleaned, encoding='utf-8')
        print(f'File {path} cleaned and saved in-place.')
    else:
        print(f'--- Cleaned {path} ---\n{cleaned}\n')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remove comments and docstrings from code files, optionally keeping strings.')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='Files to process')
    parser.add_argument('-i', '--inplace', action='store_true', help='Edit files in-place')
    parser.add_argument('-s', '--strings', action='store_true', help='Keep strings in the output')
    args = parser.parse_args()
    for path in args.files:
        process_file(path, inplace=args.inplace, keep_strings=args.strings)
