#!/data/data/com.termux/files/home/.local/bin/python
"""tell_font_name.py – Tell Font Name utilities.

This module provides functionality for tell font name."""
from __future__ import annotations
from typing import Any
import re
import sys
from pathlib import Path
from dh import cprint, get_files, mpf_async, unique_path
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttFont import TTFont

def is_ascii_printable(s: str) -> bool:
    """is_ascii_printable – is ascii printable.

Args:
    s: Description of s.

Returns:
    bool: Description of return value."""
    return all((32 <= ord(c) <= 126 for c in s))

def clean_filename(s: str) -> str:
    """clean_filename – clean filename.

Args:
    s: Description of s.

Returns:
    str: Description of return value."""
    s = re.sub('[^\\w\\\\-\\.]', '', s)
    return s.strip('_-.')

def get_best_name(font: TTFont, name_id: int) -> Any:
    """get_best_name – get best name.

Args:
    font: Description of font.
    name_id: Description of name_id."""
    fallback = None
    for rec in font['name'].names:
        if rec.nameID != name_id:
            continue
        try:
            name = rec.toUnicode().strip()
        except Exception:
            continue
        if rec.platformID == 3 and rec.langID == 1033:
            return name
        if is_ascii_printable(name):
            fallback = name
    return fallback

def get_font_names(path: Path | str) -> tuple[str, str] | tuple[None, None]:
    """get_font_names – get font names.

Args:
    path: Description of path.

Returns:
    tuple[str, str] | tuple[None, None]: Description of return value."""
    font = TTFont(path)
    family = get_best_name(font, 1)
    subfamily = get_best_name(font, 2)
    if not family:
        return (None, None)
    family = clean_filename(family)
    subfamily = 'Regular' if not subfamily else clean_filename(subfamily)
    if subfamily.lower() == family.lower():
        subfamily = 'Regular'
    return (family, subfamily)

def process_file(fn: Path) -> int:
    """process_file – process file.

Args:
    fn: Description of fn.

Returns:
    int: Description of return value."""
    Path(path)
    try:
        family, style = get_font_names(fn)
    except Exception as e:
        cprint(f'error: {e}', 'magenta')
        return 1
    if not family:
        cprint('name not found', 'magenta')
        return 1
    ext = fn.suffix.lower()
    new_path = fn.parent / f'{family}-{style}{ext}'
    if fn.name == new_path.name:
        cprint('no change', 'blue')
        return 0
    new_path = Path(str(new_path).replace('_1', '').replace('_2', '').replace('_3', '').replace('_4', '').replace('_5', '').replace('_6', '').replace('_7', '').replace('_8', '').replace('_9', ''))
    if new_path.exists():
        new_path = unique_path(new_path)
    fn.rename(new_path)
    cprint(f'{new_path.name}', 'green')
    return 0

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(arg) for arg in args] if args else get_files(cwd, extensions=['.ttf', '.woff', '.woff2', '.bin', '.otf', '.eot'])
    if not files:
        print('no files found')
        return
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf_async(process_file, files)
if __name__ == '__main__':
    raise SystemExit(main())
