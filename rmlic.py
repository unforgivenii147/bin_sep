#!/data/data/com.termux/files/home/.local/bin/python
"""rmlic.py – Rmlic utilities.

This module provides functionality for rmlic."""
from __future__ import annotations
import re
from pathlib import Path
from dh import cprint, fsz, get_nobinary, gsz
LIC_FILE = Path('/sdcard/lic')
MIN_BLANK_LINES = 3
NUM_WORKERS = 8

def load_patterns(lic_path: Path) -> list[str]:
    """load_patterns – load patterns.

Args:
    lic_path: Description of lic_path.

Returns:
    list[str]: Description of return value."""
    try:
        content = Path(lic_path).read_text(encoding='utf-8', errors='ignore')
        pattern_separator = '\\n(?:\\s*\\n){' + str(MIN_BLANK_LINES) + ',}'
        patterns = re.split(pattern_separator, content)
        patterns = [p.strip() for p in patterns if p.strip()]
        for pattern in patterns:
            pattern[:50].replace('\n', '\\n')
        return patterns
    except Exception as e:
        print(f'Error loading patterns from {lic_path}: {e}')
        return []

def escape_for_regex(text: str) -> str:
    """escape_for_regex – escape for regex.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""
    escaped = re.escape(text)
    return escaped.replace('\\n', '\\s*\\n\\s*')

def remove_patterns_from_content(content: str, patterns: list[str]) -> str:
    """remove_patterns_from_content – remove patterns from content.

Args:
    content: Description of content.
    patterns: Description of patterns.

Returns:
    str: Description of return value."""
    cleaned = content
    for pattern in patterns:
        regex_pattern = escape_for_regex(pattern)
        cleaned = re.sub(regex_pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned

def process_file(path: Path, patterns: list[str]) -> tuple:
    """process_file – process file.

Args:
    path: Description of path.
    patterns: Description of patterns.

Returns:
    tuple: Description of return value."""
    path = Path(path)
    path = Path(path)
    before = gsz(path)
    original_content = path.read_text(encoding='utf-8')
    cleaned_content = remove_patterns_from_content(original_content, patterns)
    if len(cleaned_content) != len(original_content):
        path.write_text(cleaned_content, encoding='utf-8')
        cprint(f'{path.name} updated', 'green', end=' | ')
        ds = before - gsz(path)
        cprint(f'{fsz(ds)}')
        del before, ds, cleaned_content, original_content, path

def main() -> None:
    """main – main."""
    if not LIC_FILE.exists():
        print(f'Error: License file not found: {LIC_FILE}')
        return
    patterns = load_patterns(LIC_FILE)
    if not patterns:
        print('No patterns found. Exiting.')
        return
    print()
    cwd = Path.cwd()
    all_files = get_nobinary(cwd)
    if not all_files:
        print('No files to process.')
        return
    for f in all_files:
        process_file(f, patterns)
if __name__ == '__main__':
    raise SystemExit(main())
