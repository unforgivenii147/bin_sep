#!/data/data/com.termux/files/home/.local/bin/python
"""dedupath.py – Dedupath utilities.

This module provides functionality for dedupath."""
from __future__ import annotations
from typing import Any
import os
from pathlib import Path

def get_path_entries() -> Any:
    """get_path_entries – get path entries."""
    path_str = os.environ.get('PATH', '')
    return path_str.split(':') if path_str else []

def remove_duplicates_preserve_order(entries: Any) -> Any:
    """remove_duplicates_preserve_order – remove duplicates preserve order.

Args:
    entries: Description of entries."""
    seen = set()
    unique_entries = []
    for entry in entries:
        if entry and entry not in seen:
            seen.add(entry)
            print(entry)
            unique_entries.append(entry)
    return unique_entries

def read_bashrc(bashrc_path: Path | str) -> Any:
    """read_bashrc – read bashrc.

Args:
    bashrc_path: Description of bashrc_path."""
    if bashrc_path.exists():
        return bashrc_path.read_text()
    return ''

def update_bashrc_with_path(bashrc_content: Any, new_path_entries: Path | str) -> Any:
    """update_bashrc_with_path – update bashrc with path.

Args:
    bashrc_content: Description of bashrc_content.
    new_path_entries: Description of new_path_entries."""
    new_path_str = ':'.join(new_path_entries)
    path_export = f'export PATH="{new_path_str}"\n'
    lines = bashrc_content.split('\n')
    path_line_indices = [i for i, line in enumerate(lines) if line.strip().startswith('export PATH=')]
    if path_line_indices:
        lines[path_line_indices[0]] = path_export.rstrip()
        updated_content = '\n'.join(lines)
    else:
        updated_content = bashrc_content.rstrip() + '\n' + path_export
    return updated_content

def main() -> None:
    """main – main."""
    bashrc_path = Path.home() / '.bashrc'
    path_entries = get_path_entries()
    print(f'Current PATH entries: {len(path_entries)}')
    unique_entries = remove_duplicates_preserve_order(path_entries)
    print(f'Unique PATH entries: {len(unique_entries)}')
    print(f'Removed {len(path_entries) - len(unique_entries)} duplicate(s)')
    if len(path_entries) == len(unique_entries):
        print('✓ No duplicates found!')
        return
    print('\nDuplicate entries removed:')
    for entry in path_entries:
        if entry not in unique_entries:
            print(f'  - {entry}')
    bashrc_content = read_bashrc(bashrc_path)
    updated_content = update_bashrc_with_path(bashrc_content, unique_entries)
    backup_path = bashrc_path.with_suffix('.bashrc.backup')
    if bashrc_path.exists():
        bashrc_path.write_text(bashrc_content)
        backup_path.write_text(bashrc_content)
        print(f'\n✓ Backed up original to {backup_path}')
    bashrc_path.write_text(updated_content)
    print(f'✓ Updated {bashrc_path}')
    print("\nNote: Run 'source ~/.bashrc' to apply changes to current shell")
if __name__ == '__main__':
    raise SystemExit(main())
