#!/data/data/com.termux/files/home/.local/bin/python
"""gen_s_expr.py – Gen S Expr utilities.

This module provides functionality for gen s expr."""
from __future__ import annotations
from typing import Any
import tree_sitter_python as tsp
from tree_sitter import Language, Parser
PY_LANGUAGE = Language(tsp.language())
parser = Parser(PY_LANGUAGE)

def get_ast_sexp(node: Any, source: bytes, depth: int=0) -> str:
    """get_ast_sexp – get ast sexp.

Args:
    node: Description of node.
    source: Description of source.
    depth: Description of depth.

Returns:
    str: Description of return value."""
    if node.child_count == 0:
        token = source[node.start_byte:node.end_byte].decode('utf-8')
        return f'({node.type} "{token}")'
    children_sexp = ' '.join((get_ast_sexp(child, source, depth + 1) for child in node.children))
    return f'({node.type} {children_sexp})'

def parse_and_generate(code: str) -> str:
    """parse_and_generate – parse and generate.

Args:
    code: Description of code.

Returns:
    str: Description of return value."""
    tree = parser.parse(code.encode('utf-8'))
    return get_ast_sexp(tree.root_node, code.encode('utf-8'))
result = parse_and_generate(code)
print(result)
