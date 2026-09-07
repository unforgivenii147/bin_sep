#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import tree_sitter_python as tsp
from tree_sitter import Language, Parser, Tree
from typing import Any

parser: Any = Parser()
parser.language = Language(tsp.language())
OUT_DIR: Any = Path("output")
OUT_DIR.mkdir(exist_ok=True)
VALID: Any = {"function_docstrings", "class_docstrings"}


def extract_file(src: bytes, tree: Tree) -> list[str]:
    root = tree.root_node
    return [
        src[node.start_byte : node.end_byte].decode()
        for node in root.children
        if node.type in VALID
    ]


folder_imports: Any = defaultdict(list)
for py in Path().rglob("*.py"):
    if any(part.startswith(".") for part in py.parts) or "site-packages" in py.parts:
        continue
    if OUT_DIR in py.parents:
        continue
    src: Any = py.read_bytes()
    tree: Any = parser.parse(src)
    imports: Any = extract_file(src, tree)
    if imports:
        folder_path: Any = py.parent
        relative_folder: Any = folder_path.relative_to(".")
        folder_imports[relative_folder].append("\n".join(imports))
for folder, imports_list in folder_imports.items():
    if not imports_list:
        continue
    out_file: Any = OUT_DIR / folder / "imports.py"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    content: Any = "\n\n".join(imports_list)
    out_file.write_text(content)
print(f"""
✨ Done! Processed {len(folder_imports)} folder(s)""")
