#!/data/data/com.termux/files/home/.local/bin/python
"""rmcst.py – Rmcst utilities.

This module provides functionality for rmcst."""
from __future__ import annotations
import os
import sys
from pathlib import Path
import libcst as cst
from dh import get_files, mpf_async
from libcst import EmptyLine, Pass, SimpleStatementLine
from libcst.metadata import MetadataWrapper, PositionProvider

class StripTransformer(cst.CSTTransformer):
    """StripTransformer – StripTransformer."""
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self) -> None:
        """__init__ –   init  ."""
        self.comments_removed = 0
        self.docstrings_removed = 0

    @staticmethod
    def _is_docstring_statement(stmt: cst.BaseStatement) -> bool:
        """_is_docstring_statement –  is docstring statement.

Args:
    stmt: Description of stmt.

Returns:
    bool: Description of return value."""
        if not isinstance(stmt, cst.SimpleStatementLine):
            return False
        if len(stmt.body) != 1:
            return False
        expr = stmt.body[0]
        if not isinstance(expr, cst.Expr):
            return False
        return isinstance(expr.value, cst.SimpleString)

    @staticmethod
    def _is_preserved_comment(value: str) -> bool:
        """_is_preserved_comment –  is preserved comment.

Args:
    value: Description of value.

Returns:
    bool: Description of return value."""
        stripped = value.lstrip()
        return stripped.startswith(('#!', '# fmt', '# type'))

    def leave_Comment(self, original_node: cst.Comment, updated_node: cst.Comment) -> cst.Comment | cst.RemovalSentinel:
        """leave_Comment – leave Comment.

Args:
    original_node: Description of original_node.
    updated_node: Description of updated_node.

Returns:
    cst.Comment | cst.RemovalSentinel: Description of return value."""
        if self._is_preserved_comment(original_node.value):
            return updated_node
        self.comments_removed += 1
        return cst.RemoveFromParent()

    def leave_EmptyLine(self, original_node: EmptyLine, updated_node: EmptyLine) -> EmptyLine:
        """leave_EmptyLine – leave EmptyLine.

Args:
    original_node: Description of original_node.
    updated_node: Description of updated_node.

Returns:
    EmptyLine: Description of return value."""
        if updated_node.comment is None:
            return updated_node
        comment = updated_node.comment
        if self._is_preserved_comment(comment.value):
            return updated_node
        self.comments_removed += 1
        return updated_node.with_changes(comment=None)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """leave_Module – leave Module.

Args:
    original_node: Description of original_node.
    updated_node: Description of updated_node.

Returns:
    cst.Module: Description of return value."""
        body = list(updated_node.body)
        start = 1 if body and self._is_docstring_statement(body[0]) else 0
        new_body = body[:start]
        for stmt in body[start:]:
            if self._is_docstring_statement(stmt):
                self.docstrings_removed += 1
            else:
                new_body.append(stmt)
        return updated_node.with_changes(body=new_body)

    def _strip_suite(self, body: tuple[cst.BaseStatement, ...]) -> tuple[cst.BaseStatement, ...]:
        """_strip_suite –  strip suite.

Args:
    body: Description of body.

Returns:
    tuple[cst.BaseStatement, ...]: Description of return value."""
        statements = list(body)
        if statements and self._is_docstring_statement(statements[0]):
            self.docstrings_removed += 1
            statements = statements[1:]
        if not statements:
            statements = [SimpleStatementLine(body=[Pass()])]
        return tuple(statements)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """leave_FunctionDef – leave FunctionDef.

Args:
    original_node: Description of original_node.
    updated_node: Description of updated_node.

Returns:
    cst.FunctionDef: Description of return value."""
        body = updated_node.body
        if isinstance(body, cst.IndentedBlock):
            return updated_node.with_changes(body=body.with_changes(body=self._strip_suite(body.body)))
        return updated_node

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """leave_ClassDef – leave ClassDef.

Args:
    original_node: Description of original_node.
    updated_node: Description of updated_node.

Returns:
    cst.ClassDef: Description of return value."""
        body = updated_node.body
        if isinstance(body, cst.IndentedBlock):
            return updated_node.with_changes(body=body.with_changes(body=self._strip_suite(body.body)))
        return updated_node

def process_file(path: Path) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    source = path.read_text(encoding='utf-8')
    ROOT = path.parent
    try:
        module = cst.parse_module(source)
    except Exception as exc:
        print(f'SKIP {path}: parse failed: {exc}')
        return
    wrapper = MetadataWrapper(module)
    transformer = StripTransformer()
    try:
        updated = wrapper.visit(transformer)
    except Exception as exc:
        print(f'SKIP {path}: transform failed: {exc}')
        return
    code = updated.code
    try:
        cst.parse_module(code)
    except SyntaxError as exc:
        print(f'ERROR {path}: transformed code is invalid: {exc}')
        return
    if code != source:
        path.write_text(code, encoding='utf-8')
    rel = os.path.relpath(path, ROOT)
    if transformer.comments_removed and transformer.docstrings_removed:
        print(f'{rel}: {transformer.comments_removed}/{transformer.docstrings_removed}')
    if transformer.comments_removed and (not transformer.docstrings_removed):
        print(f'{rel}: {transformer.comments_removed}/0')
    if not transformer.comments_removed and transformer.docstrings_removed:
        print(f'{rel}: 0/{transformer.docstrings_removed}')

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=['.py'])
    if len(files) == 1:
        process_file(files[0])
        sys.exit(0)
    mpf_async(process_file, files)
if __name__ == '__main__':
    raise SystemExit(main())
