#!/data/data/com.termux/files/home/.local/bin/python
"""fimport.py – Fimport utilities.

This module provides functionality for fimport."""
from __future__ import annotations
import ast
from pathlib import Path
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from collections.abc import Iterable

class ImportVisitor(ast.NodeVisitor):
    """ImportVisitor – ImportVisitor."""

    def __init__(self) -> None:
        """__init__ –   init  ."""
        self._nesting_level = 0
        self.non_top_level_imports: list[ast.stmt] = []

    def _is_top_level(self) -> bool:
        """_is_top_level –  is top level.

Returns:
    bool: Description of return value."""
        return self._nesting_level == 0

    def _visit_nested(self, node: ast.AST) -> None:
        """_visit_nested –  visit nested.

Args:
    node: Description of node."""
        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """visit_FunctionDef – visit FunctionDef.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """visit_AsyncFunctionDef – visit AsyncFunctionDef.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """visit_ClassDef – visit ClassDef.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_For(self, node: ast.For) -> None:
        """visit_For – visit For.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """visit_AsyncFor – visit AsyncFor.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_While(self, node: ast.While) -> None:
        """visit_While – visit While.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_If(self, node: ast.If) -> None:
        """visit_If – visit If.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_With(self, node: ast.With) -> None:
        """visit_With – visit With.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """visit_AsyncWith – visit AsyncWith.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_Try(self, node: ast.Try) -> None:
        """visit_Try – visit Try.

Args:
    node: Description of node."""
        self._visit_nested(node)

    def visit_Import(self, node: ast.Import) -> None:
        """visit_Import – visit Import.

Args:
    node: Description of node."""
        if not self._is_top_level():
            self.non_top_level_imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """visit_ImportFrom – visit ImportFrom.

Args:
    node: Description of node."""
        if not self._is_top_level():
            self.non_top_level_imports.append(node)
        self.generic_visit(node)

def find_python_files(root: Path) -> Iterable[Path]:
    """find_python_files – find python files.

Args:
    root: Description of root.

Returns:
    Iterable[Path]: Description of return value."""
    return root.rglob('*.py')

def format_import(node: ast.stmt) -> str:
    """format_import – format import.

Args:
    node: Description of node.

Returns:
    str: Description of return value."""
    if isinstance(node, ast.Import):
        parts = []
        for alias in node.names:
            if alias.asname:
                parts.append(f'{alias.name} as {alias.asname}')
            else:
                parts.append(alias.name)
        return 'import ' + ', '.join(parts)
    if isinstance(node, ast.ImportFrom):
        module = node.module or ''
        parts = []
        for alias in node.names:
            if alias.asname:
                parts.append(f'{alias.name} as {alias.asname}')
            else:
                parts.append(alias.name)
        level_dots = '.' * (node.level or 0)
        module_str = level_dots + module if module else level_dots
        return f'from {module_str} import ' + ', '.join(parts)
    return '<unknown import>'

def inspect_file(path: Path) -> Any:
    """inspect_file – inspect file.

Args:
    path: Description of path."""
    try:
        source = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        source = path.read_text(encoding='utf-8', errors='ignore')
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        print(f'[WARN] Skipping {path} (syntax error: {e})')
        return []
    visitor = ImportVisitor()
    visitor.visit(tree)
    results = []
    for node in visitor.non_top_level_imports:
        lineno = getattr(node, 'lineno', '?')
        results.append((lineno, format_import(node)))
    return results

def main() -> None:
    """main – main."""
    root = Path.cwd()
    any_found = False
    for py_file in find_python_files(root):
        imports = inspect_file(py_file)
        if not imports:
            continue
        any_found = True
        print(f'\n{py_file}:')
        for lineno, stmt in imports:
            print(f'  line {lineno}: {stmt}')
    if not any_found:
        print('No non-top-level imports found.')
if __name__ == '__main__':
    raise SystemExit(main())
