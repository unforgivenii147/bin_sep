#!/data/data/com.termux/files/home/.local/bin/python
"""rmunused_funcs.py – Rmunused Funcs utilities.

This module provides functionality for rmunused funcs."""
from __future__ import annotations
from typing import Any
import ast
import logging
import multiprocessing
import shutil
from functools import partial
from pathlib import Path
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_defined_and_called(path: Path | str) -> Any:
    """get_defined_and_called – get defined and called.

Args:
    path: Description of path."""
    try:
        with Path(path).open('r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return (None, None, e)
    defined = set()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined.add(node.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return (defined, called, None)

def process_file(path: Path | str, dry_run: bool=True) -> str | None:
    """process_file – process file.

Args:
    path: Description of path.
    dry_run: Description of dry_run.

Returns:
    str | None: Description of return value."""
    Path(path)
    defined, called, err = get_defined_and_called(path)
    if err:
        return f'Error parsing {path}: {err}'
    unused = [f for f in defined if f not in called and (not f.startswith('_'))]
    if not unused:
        return None
    if dry_run:
        return f'[DRY-RUN] Would remove {unused} from {path}'
    shutil.copy2(path, path.with_suffix('.py.bak'))
    return f'Processed {path}: Found {len(unused)} potentially unused functions.'

def run_cleaner(dry_run: bool=True) -> None:
    """run_cleaner – run cleaner.

Args:
    dry_run: Description of dry_run."""
    files = list(Path().rglob('*.py'))
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    func = partial(process_file, dry_run=dry_run)
    results = pool.map(func, files)
    for res in results:
        if res:
            print(res)
if __name__ == '__main__':
    run_cleaner(dry_run=True)
