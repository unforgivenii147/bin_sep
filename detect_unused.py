#!/data/data/com.termux/files/home/.local/bin/python
"""detect_unused.py – Detect Unused utilities.

This module provides functionality for detect unused."""
from __future__ import annotations
import argparse
import ast
import multiprocessing as mp
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Definition:
    """Definition – Definition."""
    name: str
    kind: str
    file: Path
    lineno: int
    end_lineno: int
    col_offset: int = 0

@dataclass
class FileAnalysis:
    """FileAnalysis – FileAnalysis."""
    file: Path
    defs: list[Definition] = field(default_factory=list)
    used_names: set[str] = field(default_factory=set)
    source: str = ''
    error: str | None = None

def _is_const_name(name: str) -> bool:
    """_is_const_name –  is const name.

Args:
    name: Description of name.

Returns:
    bool: Description of return value."""
    return name.isupper() and (not name.startswith('__'))

class DefinitionCollector(ast.NodeVisitor):
    """DefinitionCollector – DefinitionCollector."""

    def __init__(self, file: Path) -> None:
        """__init__ –   init  .

Args:
    file: Description of file."""
        self.file = file
        self.defs: list[Definition] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """visit_FunctionDef – visit FunctionDef.

Args:
    node: Description of node."""
        self.defs.append(Definition(node.name, 'func', self.file, node.lineno, getattr(node, 'end_lineno', node.lineno)))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """visit_AsyncFunctionDef – visit AsyncFunctionDef.

Args:
    node: Description of node."""
        self.defs.append(Definition(node.name, 'func', self.file, node.lineno, getattr(node, 'end_lineno', node.lineno)))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """visit_ClassDef – visit ClassDef.

Args:
    node: Description of node."""
        self.defs.append(Definition(node.name, 'class', self.file, node.lineno, getattr(node, 'end_lineno', node.lineno)))

    def visit_Assign(self, node: ast.Assign) -> None:
        """visit_Assign – visit Assign.

Args:
    node: Description of node."""
        for target in node.targets:
            if isinstance(target, ast.Name) and _is_const_name(target.id):
                self.defs.append(Definition(target.id, 'const', self.file, node.lineno, getattr(node, 'end_lineno', node.lineno)))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """visit_AnnAssign – visit AnnAssign.

Args:
    node: Description of node."""
        if isinstance(node.target, ast.Name) and _is_const_name(node.target.id):
            self.defs.append(Definition(node.target.id, 'const', self.file, node.lineno, getattr(node, 'end_lineno', node.lineno)))
        self.generic_visit(node)

class UsageCollector(ast.NodeVisitor):
    """UsageCollector – UsageCollector."""

    def __init__(self) -> None:
        """__init__ –   init  ."""
        self.used: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        """visit_Name – visit Name.

Args:
    node: Description of node."""
        self.used.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """visit_Attribute – visit Attribute.

Args:
    node: Description of node."""
        self.used.add(node.attr)
        self.generic_visit(node)

def analyze_file(file: Path) -> FileAnalysis:
    """analyze_file – analyze file.

Args:
    file: Description of file.

Returns:
    FileAnalysis: Description of return value."""
    try:
        source = file.read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(source, filename=str(file))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        return FileAnalysis(file=file, error=str(exc))
    def_collector = DefinitionCollector(file)
    def_collector.visit(tree)
    use_collector = UsageCollector()
    use_collector.visit(tree)
    return FileAnalysis(file=file, defs=def_collector.defs, used_names=use_collector.used, source=source)
DUNDER_SKIP = {'__all__', '__version__', '__author__'}

def find_unused(analyses: list[FileAnalysis]) -> list[Definition]:
    """find_unused – find unused.

Args:
    analyses: Description of analyses.

Returns:
    list[Definition]: Description of return value."""
    all_defs: list[Definition] = []
    global_used: set[str] = set()
    for fa in analyses:
        if fa.error:
            continue
        all_defs.extend(fa.defs)
        global_used |= fa.used_names
    unused: list[Definition] = []
    for d in all_defs:
        if d.name in DUNDER_SKIP:
            continue
        if d.name.startswith('_') and d.name.endswith('_') and d.name.startswith('__'):
            continue
        if d.name == 'main':
            continue
        occurrences = sum((1 for fa in analyses if not fa.error and d.name in fa.used_names))
        if occurrences == 0:
            unused.append(d)
    return unused
KIND_DIR = {'func': 'func', 'class': 'classes', 'const': 'const'}

def extract_definition(item: tuple[Definition, str]) -> str:
    """extract_definition – extract definition.

Args:
    item: Description of item.

Returns:
    str: Description of return value."""
    definition, out_root = item
    out_dir = Path(out_root) / KIND_DIR[definition.kind]
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = definition.file.read_text(encoding='utf-8', errors='replace').splitlines()
    snippet = '\n'.join(lines[definition.lineno - 1:definition.end_lineno])
    safe_stem = definition.file.stem.replace('.', '_')
    out_file = out_dir / f'{safe_stem}__{definition.name}.py'
    header = f"# Extracted: {definition.kind} '{definition.name}'\n# Source: {definition.file}\n# Lines: {definition.lineno}-{definition.end_lineno}\n\n"
    out_file.write_text(header + snippet + '\n', encoding='utf-8')
    return str(out_file)
WORKERS = 8

def gather_py_files(root: Path) -> list[Path]:
    """gather_py_files – gather py files.

Args:
    root: Description of root.

Returns:
    list[Path]: Description of return value."""
    excluded_dirs = {'.git', '__pycache__', 'venv', '.venv', 'output', 'node_modules'}
    return [p for p in root.rglob('*.py') if not any((part in excluded_dirs for part in p.parts))]

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Detect (and optionally extract) unused functions/classes/constants.')
    parser.add_argument('-c', '--extract', action='store_true', help='extract each unused object into ./output/{classes,func,const}/')
    parser.add_argument('-d', '--dir', default='.', help='root directory to scan recursively (default: current dir)')
    args = parser.parse_args()
    root = Path(args.dir).resolve()
    files = gather_py_files(root)
    if not files:
        print('No .py files found.')
        return
    print(f'Scanning {len(files)} file(s) with {WORKERS} workers...')
    with mp.Pool(processes=WORKERS) as pool:
        analyses = list(pool.imap_unordered(analyze_file, files))
    for fa in analyses:
        if fa.error:
            print(f'[WARN] Failed to parse {fa.file}: {fa.error}')
    unused = find_unused(analyses)
    if not unused:
        print('\nNo unused functions/classes/constants found.')
        return
    unused.sort(key=lambda d: (str(d.file), d.lineno))
    print(f'\nFound {len(unused)} unused object(s):\n')
    for d in unused:
        rel = d.file.relative_to(root) if d.file.is_relative_to(root) else d.file
        print(f'  [{d.kind:5}] {d.name:30} {rel}:{d.lineno}')
    if args.extract:
        out_root = root / 'output'
        print(f'\nExtracting {len(unused)} object(s) into {out_root} ...')
        work_items = [(d, str(out_root)) for d in unused]
        with mp.Pool(processes=WORKERS) as pool:
            written = list(pool.imap_unordered(extract_definition, work_items))
        for path in written:
            print(f'  wrote {path}')
        print('\nExtraction complete.')
if __name__ == '__main__':
    main()
