#!/data/data/com.termux/files/home/.local/bin/python
"""os2p3.py – Os2P3 utilities.

This module provides functionality for os2p3."""
from __future__ import annotations
import re
from pathlib import Path
OS_PATH_TO_PATHLIB = {'os\\.path\\.join\\(': 'Path(', 'os\\.path\\.dirname\\(': '.parent', 'os\\.path\\.basename\\(': '.name', 'os\\.path\\.exists\\(': '.exists()', 'os\\.path\\.isfile\\(': '.is_file()', 'os\\.path\\.isdir\\(': '.is_dir()', 'os\\.path\\.abspath\\(': 'Path(', 'os\\.path\\.relpath\\(': 'Path(', 'os\\.path\\.normpath\\(': 'Path(', 'os\\.path\\.expanduser\\(': 'Path(', 'os\\.path\\.getsize\\(': '.stat().st_size', 'os\\.path\\.getmtime\\(': '.stat().st_mtime', 'os\\.path\\.getatime\\(': '.stat().st_atime', 'os\\.path\\.split\\(': '.parts', 'os\\.path\\.splitext\\(': '.suffix'}
OS_PATH_IMPORT_PATTERNS = ['import os\\.path', 'from os\\.path import', 'from os import path', 'import os']

def refactor_file(path: Path | str) -> bool:
    """refactor_file – refactor file.

Args:
    path: Description of path."""
    content = path.read_text(encoding='utf-8')
    original_content = content
    for pattern in OS_PATH_IMPORT_PATTERNS:
        content = re.sub(pattern, 'from pathlib import Path', content)
    for os_path_func, pathlib_replacement in OS_PATH_TO_PATHLIB.items():
        content = re.sub(os_path_func, pathlib_replacement, content)
    content = re.sub('Path\\(([^)]+)\\)', lambda m: f"Path({m.group(1).replace(' ', '').replace(',', ', ')})", content)
    content = re.sub('Path\\(([^)]+)\\)', lambda m: f'Path({m.group(1)})', content)
    content = re.sub('(\\w+)\\s*\\.parent', 'Path(\\1).parent', content)
    content = re.sub('(\\w+)\\s*\\.name', 'Path(\\1).name', content)
    content = re.sub('(\\w+)\\s*\\.exists\\(\\)', 'Path(\\1).exists()', content)
    content = re.sub('(\\w+)\\s*\\.is_file\\(\\)', 'Path(\\1).is_file()', content)
    content = re.sub('(\\w+)\\s*\\.is_dir\\(\\)', 'Path(\\1).is_dir()', content)
    content = re.sub('Path\\(([^)]+)\\)', lambda m: f'Path({m.group(1)}).resolve()' if 'abspath' in m.group(0) else m.group(0), content)
    content = re.sub('(\\w+)\\s*\\.stat\\(\\)\\s*\\.st_size', 'Path(\\1).stat().st_size', content)
    content = re.sub('(\\w+)\\s*\\.stat\\(\\)\\s*\\.st_mtime', 'Path(\\1).stat().st_mtime', content)
    content = re.sub('(\\w+)\\s*\\.stat\\(\\)\\s*\\.st_atime', 'Path(\\1).stat().st_atime', content)
    if 'from pathlib import Path' not in content and 'import pathlib' not in content:
        content = 'from pathlib import Path\n' + content
    if content != original_content:
        path.write_text(content, encoding='utf-8')
        return True
    return False

def refactor_directory(directory: Path | str) -> None:
    """refactor_directory – refactor directory.

Args:
    directory: Description of directory."""
    python_files = directory.rglob('*.py')
    refactored_count = 0
    for path in python_files:
        if refactor_file(path):
            print(f'Refactored: {path.relative_to(Path.cwd())}')
            refactored_count += 1
    print(f'\nRefactored {refactored_count} files.')
if __name__ == '__main__':
    current_dir = Path.cwd()
    print(f'Refactoring Python files in: {current_dir}')
    refactor_directory(current_dir)
