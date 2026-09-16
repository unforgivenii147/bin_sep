#!/data/data/com.termux/files/home/.local/bin/python
"""rmunusedfuncs.py – Rmunusedfuncs utilities.

This module provides functionality for rmunusedfuncs."""
from __future__ import annotations
from typing import Any
import argparse
import ast
import multiprocessing as mp
import shutil
import traceback
from pathlib import Path

def find_unused_functions(source: str) -> Any:
    """find_unused_functions – find unused functions.

Args:
    source: Description of source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ([], ['SyntaxError while parsing file'])
    defined = set()
    called = set()

    class Visitor(ast.NodeVisitor):
        """Visitor – Visitor."""

        def visit_FunctionDef(self, node: Any) -> None:
            """visit_FunctionDef – visit FunctionDef.

Args:
    node: Description of node."""
            defined.add(node.name)
            self.generic_visit(node)

        def visit_Call(self, node: Any) -> None:
            """visit_Call – visit Call.

Args:
    node: Description of node."""
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            self.generic_visit(node)
    Visitor().visit(tree)
    unused = defined - called
    return (list(unused), [])

def remove_functions_from_source(source: str, unused_functions: Any) -> str:
    """remove_functions_from_source – remove functions from source.

Args:
    source: Description of source.
    unused_functions: Description of unused_functions.

Returns:
    str: Description of return value."""
    tree = ast.parse(source)
    new_body = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in unused_functions:
            continue
        new_body.append(node)
    tree.body = new_body
    return ast.unparse(tree)

def process_file(path: Path | str, dry_run: bool=False) -> Any:
    """process_file – process file.

Args:
    path: Description of path.
    dry_run: Description of dry_run."""
    Path(path)
    errors = []
    path = Path(path)
    try:
        source = path.read_text(encoding='utf-8')
    except Exception as e:
        return (path, [], [f'Error reading file: {e}'])
    unused, parse_errors = find_unused_functions(source)
    errors.extend(parse_errors)
    if not unused:
        return (path, [], errors)
    try:
        new_source = remove_functions_from_source(source, unused)
    except Exception:
        errors.append('Error rewriting file:\n' + traceback.format_exc())
        return (path, unused, errors)
    if not dry_run:
        backup_path = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, backup_path)
        path.write_text(new_source, encoding='utf-8')
    return (path, unused, errors)

def gather_python_files(root: Path) -> list[Path]:
    """gather_python_files – gather python files.

Args:
    root: Description of root.

Returns:
    list[Path]: Description of return value."""
    return [p for p in root.rglob('*.py') if p.is_file()]

def worker(args: str) -> Any:
    """worker – worker.

Args:
    args: Description of args."""
    return process_file(*args)

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Remove unused functions recursively.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without modifying files.')
    parser.add_argument('--workers', type=int, default=mp.cpu_count(), help='Number of processes')
    args = parser.parse_args()
    root = Path()
    py_files = gather_python_files(root)
    print(f'Scanning {len(py_files)} Python files...')
    with mp.Pool(args.workers) as pool:
        results = pool.map(worker, [(f, args.dry_run) for f in py_files])
    print('\n=== RESULTS ===')
    for path, unused, errors in results:
        if unused:
            if args.dry_run:
                print(f'[DRY-RUN] Would remove {unused} from {path}')
            else:
                print(f'Removed {unused} from {path} (backup created)')
        for err in errors:
            print(f'[ERROR] {path}: {err}')
if __name__ == '__main__':
    raise SystemExit(main())
