#!/data/data/com.termux/files/home/.local/bin/python
"""afk_autoflake.py – Afk Autoflake utilities.

This module provides functionality for afk autoflake."""
from __future__ import annotations
from typing import Any
import argparse
import difflib
import multiprocessing as mp
import subprocess
from pathlib import Path

def _make_diff(path: Path | str) -> Any:
    """Return a unified diff of what autoflake would change."""
    original = Path(path).read_text()
    result = subprocess.run(['autoflake', '--remove-all-unused-imports', '--ignore-init-module-imports', '-'], input=original, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    fixed = result.stdout
    if fixed == original:
        return None
    return ''.join(difflib.unified_diff(original.splitlines(keepends=True), fixed.splitlines(keepends=True), fromfile=f'a/{path}', tofile=f'b/{path}'))

def check_or_fix_imports(path: Path | str, autofix: bool=False, show_diff: bool=False) -> bool:
    """check_or_fix_imports – check or fix imports.

Args:
    path: Description of path.
    autofix: Description of autofix.
    show_diff: Description of show_diff."""
    if not Path(path).exists():
        print(f'Error: The file `{path}` does not exist.')
        return
    command = ['autoflake', '--remove-all-unused-imports', '--ignore-init-module-imports', path]
    if autofix:
        command.append('--in-place')
    else:
        command.append('--check')
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return
        elif result.returncode == 1:
            if autofix:
                print(f'Successfully removed unused imports from `{path}`.')
            elif show_diff:
                diff = _make_diff(path)
                if diff:
                    print(diff, end='' if diff.endswith('\n') else '\n')
            else:
                output = (result.stdout or '') + (result.stderr or '')
                for line in output.splitlines():
                    if line.strip():
                        print(f'{path}: {line}')
    except FileNotFoundError:
        print('Error: `autoflake` is not installed. Run `pip install autoflake`.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check or fix unused imports in Python file(s).')
    parser.add_argument('file', nargs='?', help='Path to the Python file (if omitted, processes all .py files in current dir)')
    parser.add_argument('-a', '--autofix', action='store_true', help='Automatically remove unused imports')
    parser.add_argument('-d', '--diff', action='store_true', help='Show unified diff of the affected lines')
    args = parser.parse_args()
    if args.file:
        check_or_fix_imports(args.file, args.autofix, args.diff)
    else:
        files = sorted((str(p) for p in Path.cwd().glob('*.py')))
        if files:
            with mp.Pool(processes=8) as pool:
                results = [pool.apply_async(check_or_fix_imports, (f, args.autofix, args.diff)) for f in files]
                for r in results:
                    r.wait()
