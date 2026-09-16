#!/data/data/com.termux/files/home/.local/bin/python
"""exconst.py – Exconst utilities.

This module provides functionality for exconst."""
from __future__ import annotations
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple
import libcst as cst

class Constant(NamedTuple):
    """Constant – Constant."""
    name: str
    value: str
    file: Path

class ConstantExtractor(cst.CSTVisitor):
    """ConstantExtractor – ConstantExtractor."""

    def __init__(self, path: Path) -> None:
        """__init__ –   init  .

Args:
    path: Description of path."""
        self.path = path
        self.constants: list[Constant] = []

    def visit_Assign(self, node: cst.Assign) -> None:
        """visit_Assign – visit Assign.

Args:
    node: Description of node."""
        for target in node.targets:
            if isinstance(target.target, cst.Name):
                name = target.target.value
                if name.isupper() and (not name.startswith('_')):
                    value = self._extract_value(node.value)
                    self.constants.append(Constant(name, value, self.path))

    def _extract_value(self, node: cst.BaseExpression) -> str:
        """_extract_value –  extract value.

Args:
    node: Description of node.

Returns:
    str: Description of return value."""
        return node.deep_clone().deep_replace(lambda n: n).deep_equals(node) and node.visit(cst.CSTCodeGenerator()) or cst.Module([cst.SimpleStatementLine([cst.Expr(node)])]).code.strip()

def extract_from_file(path: Path) -> list[Constant]:
    """extract_from_file – extract from file.

Args:
    path: Description of path.

Returns:
    list[Constant]: Description of return value."""
    try:
        source = path.read_text(encoding='utf-8')
        tree = cst.parse_module(source)
        extractor = ConstantExtractor(path)
        tree.walk(extractor)
        return extractor.constants
    except (SyntaxError, UnicodeDecodeError):
        return []

def get_python_files(paths: list[Path]) -> list[Path]:
    """get_python_files – get python files.

Args:
    paths: Description of paths.

Returns:
    list[Path]: Description of return value."""
    python_files = []
    for path in paths:
        if path.is_file() and path.suffix == '.py':
            python_files.append(path)
        elif path.is_dir():
            python_files.extend(path.glob('**/*.py'))
    return python_files

def main() -> None:
    """main – main."""
    input_paths = [Path(arg) for arg in sys.argv[1:]] if len(sys.argv) > 1 else [Path.cwd()]
    python_files = get_python_files(input_paths)
    constants: dict[Path, list[Constant]] = {}
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(extract_from_file, file): file for file in python_files}
        for future in as_completed(futures):
            result = future.result()
            if result:
                constants[futures[future]] = result
    for path in sorted(constants.keys()):
        print(f'\n{path}:')
        for const in sorted(constants[path], key=lambda c: c.name):
            print(f'  {const.name} = {const.value}')
    total = sum((len(consts) for consts in constants.values()))
    print(f'\nTotal constants found: {total}')
if __name__ == '__main__':
    raise SystemExit(main())
