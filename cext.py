#!/data/data/com.termux/files/home/.local/bin/python
"""
Python Code Entity Extractor

This script extracts Python code entities (classes, functions, and constants)
from Python source files and archives (ZIP, TAR, etc.). It uses AST parsing
to identify entities and provides parallel processing for efficiency.

The extracted entities are written as individual Python files to an output
directory, with appropriate imports and source attribution.
"""

import argparse
import ast
import io
import os
import re
import sys
import tarfile
import zipfile
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Callable, NamedTuple, Sequence

from loguru import logger

try:
    import tree_sitter
    import tree_sitter_python as tspython

    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

try:
    import zstd

    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False


class Entity(NamedTuple):
    """Represents a Python code entity (class, function, or constant)."""

    name: str
    full_name: str
    entity_type: str
    source: str
    imports: list[str]
    source_path: str


CONST_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
IMPORT_HINTS: dict[str, str] = {
    "List": "from typing import List",
    "Dict": "from typing import Dict",
    "Optional": "from typing import Optional",
    "Tuple": "from typing import Tuple",
    "Set": "from typing import Set",
    "Any": "from typing import Any",
    "Union": "from typing import Union",
    "Callable": "from typing import Callable",
    "Type": "from typing import Type",
    "ClassVar": "from typing import ClassVar",
    "Final": "from typing import Final",
    "Literal": "from typing import Literal",
    "Generator": "from typing import Generator",
    "Iterator": "from typing import Iterator",
    "Iterable": "from typing import Iterable",
    "Sequence": "from typing import Sequence",
    "Mapping": "from typing import Mapping",
    "TypeVar": "from typing import TypeVar",
    "overload": "from typing import overload",
    "cast": "from typing import cast",
    "TYPE_CHECKING": "from typing import TYPE_CHECKING",
    "dataclass": "from dataclasses import dataclass",
    "field": "from dataclasses import field",
    "Path": "from pathlib import Path",
    "datetime": "from datetime import datetime",
    "date": "from datetime import date",
    "timedelta": "from datetime import timedelta",
    "re": "import re",
    "json": "import json",
    "os": "import os",
    "sys": "import sys",
    "math": "import math",
    "time": "import time",
    "copy": "import copy",
    "abc": "import abc",
    "ABC": "from abc import ABC",
    "abstractmethod": "from abc import abstractmethod",
    "functools": "import functools",
    "itertools": "import itertools",
    "collections": "import collections",
    "defaultdict": "from collections import defaultdict",
    "OrderedDict": "from collections import OrderedDict",
    "Counter": "from collections import Counter",
    "deque": "from collections import deque",
    "namedtuple": "from collections import namedtuple",
    "contextmanager": "from contextlib import contextmanager",
    "asynccontextmanager": "from contextlib import asynccontextmanager",
    "partial": "from functools import partial",
    "wraps": "from functools import wraps",
    "lru_cache": "from functools import lru_cache",
    "cached_property": "from functools import cached_property",
    "Enum": "from enum import Enum",
    "auto": "from enum import auto",
    "IntEnum": "from enum import IntEnum",
    "logging": "import logging",
    "getLogger": "import logging",
    "traceback": "import traceback",
    "threading": "import threading",
    "asyncio": "import asyncio",
    "subprocess": "import subprocess",
    "tempfile": "import tempfile",
    "hashlib": "import hashlib",
    "base64": "import base64",
    "struct": "import struct",
    "io": "import io",
    "StringIO": "from io import StringIO",
    "BytesIO": "from io import BytesIO",
    "socket": "import socket",
    "uuid": "import uuid",
    "warnings": "import warnings",
    "weakref": "import weakref",
    "inspect": "import inspect",
    "textwrap": "import textwrap",
    "string": "import string",
    "random": "import random",
    "heapq": "import heapq",
    "bisect": "import bisect",
    "array": "import array",
    "pickle": "import pickle",
    "shelve": "import shelve",
    "sqlite3": "import sqlite3",
    "csv": "import csv",
    "configparser": "import configparser",
    "argparse": "import argparse",
    "shutil": "import shutil",
    "glob": "import glob",
    "fnmatch": "import fnmatch",
    "stat": "import stat",
    "platform": "import platform",
    "signal": "import signal",
    "atexit": "import atexit",
    "pprint": "import pprint",
    "unittest": "import unittest",
    "pytest": "import pytest",
    "dataclasses": "import dataclasses",
    "typing_extensions": "import typing_extensions",
    "Protocol": "from typing import Protocol",
    "runtime_checkable": "from typing import runtime_checkable",
}


def detect_needed_imports(source: str) -> list[str]:
    """Detect import statements needed based on the source code content.

    Args:
        source: Python source code to analyze

    Returns:
        List of import statements needed for the source
    """
    needed: list[str] = []
    seen: set[str] = set()
    for name, stmt in IMPORT_HINTS.items():
        if re.search(f"\\b{re.escape(name)}\\b", source) and stmt not in seen:
            needed.append(stmt)
            seen.add(stmt)
    return needed


class EntityVisitor(ast.NodeVisitor):
    """AST visitor that extracts code entities from Python source."""

    def __init__(self, source_lines: list[str], source_path: str) -> None:
        """Initialize the entity visitor.

        Args:
            source_lines: Source code split into lines
            source_path: Path to the source file
        """
        self.source_lines = source_lines
        self.source_path = source_path
        self.entities: list[Entity] = []
        self.imports: list[str] = []
        self._class_stack: list[str] = []

    def _slice(self, node: ast.AST) -> str:
        """Extract source code for a given AST node.

        Args:
            node: AST node to extract source for

        Returns:
            Source code string for the node
        """
        start = node.lineno - 1
        end = node.end_lineno
        lines = self.source_lines[start:end]
        col = node.col_offset
        stripped = [l[col:] if len(l) > col else l for l in lines]
        return "".join(stripped)

    def _record_import(self, node: ast.Import | ast.ImportFrom) -> None:
        """Record an import statement.

        Args:
            node: Import node to record
        """
        src = ast.unparse(node)
        if src not in self.imports:
            self.imports.append(src)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit an import statement.

        Args:
            node: Import node
        """
        self._record_import(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit a from-import statement.

        Args:
            node: ImportFrom node
        """
        self._record_import(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition and extract it as an entity.

        Args:
            node: ClassDef node
        """
        self._class_stack.append(node.name)
        class_source = self._slice(node)
        imports_in_class = detect_needed_imports(class_source)
        entity = Entity(
            name=node.name,
            full_name=node.name,
            entity_type="class",
            source=class_source,
            imports=imports_in_class,
            source_path=self.source_path,
        )
        self.entities.append(entity)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_method(child, node.name)
            elif isinstance(child, ast.ClassDef):
                self.visit_ClassDef(child)
        self._class_stack.pop()

    def _visit_method(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, class_name: str
    ) -> None:
        """Visit a method within a class.

        Args:
            node: FunctionDef or AsyncFunctionDef node
            class_name: Name of the containing class
        """
        method_source = self._slice(node)
        full_name = f"{class_name}_{node.name}"
        imports_for_method = detect_needed_imports(method_source)
        entity = Entity(
            name=node.name,
            full_name=full_name,
            entity_type="function",
            source=method_source,
            imports=imports_for_method,
            source_path=self.source_path,
        )
        self.entities.append(entity)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition and extract it as an entity.

        Args:
            node: FunctionDef node
        """
        if self._class_stack:
            return
        func_source = self._slice(node)
        imports_for_func = detect_needed_imports(func_source)
        entity = Entity(
            name=node.name,
            full_name=node.name,
            entity_type="function",
            source=func_source,
            imports=imports_for_func,
            source_path=self.source_path,
        )
        self.entities.append(entity)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit an assignment and extract constants.

        Args:
            node: Assign node
        """
        if self._class_stack:
            return
        for target in node.targets:
            if isinstance(target, ast.Name) and CONST_RE.match(target.id):
                const_source = self._slice(node)
                entity = Entity(
                    name=target.id,
                    full_name=target.id,
                    entity_type="const",
                    source=const_source,
                    imports=[],
                    source_path=self.source_path,
                )
                self.entities.append(entity)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit an annotated assignment and extract constants.

        Args:
            node: AnnAssign node
        """
        if self._class_stack:
            return
        target = node.target
        if isinstance(target, ast.Name) and CONST_RE.match(target.id):
            const_source = self._slice(node)
            entity = Entity(
                name=target.id,
                full_name=target.id,
                entity_type="const",
                source=const_source,
                imports=[],
                source_path=self.source_path,
            )
            self.entities.append(entity)


def extract_imports_tree_sitter(source: str) -> list[str]:
    """Extract import statements using tree-sitter parser.

    Args:
        source: Python source code

    Returns:
        List of import statements
    """
    if not HAS_TREE_SITTER:
        return []
    try:
        PY_LANGUAGE = tree_sitter.Language(tspython.language())
        parser = tree_sitter.Parser(PY_LANGUAGE)
        tree = parser.parse(source.encode())
        imports: list[str] = []
        tree.walk()

        def _walk(node: tree_sitter.Node) -> None:
            if node.type in ("import_statement", "import_from_statement"):
                imports.append(node.text.decode(errors="replace"))
            for child in node.children:
                _walk(child)

        _walk(tree.root_node)
        return imports
    except Exception:
        return []


def parse_python_source(
    source: str, virtual_path: str
) -> tuple[list[Entity], list[str]]:
    """Parse Python source and extract entities and imports.

    Args:
        source: Python source code
        virtual_path: Virtual path for the source

    Returns:
        Tuple of entities and imports
    """
    try:
        tree = ast.parse(source, filename=virtual_path)
    except SyntaxError as exc:
        logger.warning(f"Syntax error in {virtual_path}: {exc}")
        return ([], [])
    lines = [l + "\n" for l in source.splitlines()]
    visitor = EntityVisitor(lines, virtual_path)
    visitor.visit(tree)
    ts_imports = extract_imports_tree_sitter(source)
    all_imports = ts_imports if ts_imports else visitor.imports
    return (visitor.entities, all_imports)


PYTHON_EXTENSIONS = {".py"}
ARCHIVE_EXTENSIONS = {".zip", ".whl", ".tar", ".gz", ".tgz", ".zst", ".xz"}
SKIP_DIRS = {".git", "__pycache__"}


def _looks_like_python(data: bytes) -> bool:
    """Check if data looks like Python source code.

    Args:
        data: Binary data to check

    Returns:
        True if data looks like Python source
    """
    head = data[:512]
    if b"#!/usr/bin/env python" in head or b"#!/usr/bin/python" in head:
        return True
    return any(kw in head for kw in (b"import ", b"def ", b"class ", b"if __name__"))


def read_py_file(path: Path) -> str | None:
    """Read a Python file.

    Args:
        path: Path to the file

    Returns:
        File contents or None if error
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError) as exc:
        logger.error(f"Cannot read {path}: {exc}")
        return None


def process_python_file(
    path: Path, virtual_path: str | None = None, source_override: str | None = None
) -> tuple[list[Entity], list[str]]:
    """Process a Python file and extract entities.

    Args:
        path: Path to the file
        virtual_path: Virtual path for the file
        source_override: Source code override

    Returns:
        Tuple of entities and imports
    """
    vpath = virtual_path or str(path)
    source = source_override if source_override is not None else read_py_file(path)
    if source is None:
        return ([], [])
    if not source.strip():
        return ([], [])
    return parse_python_source(source, vpath)


def process_zip_archive(archive_path: Path) -> list[tuple[list[Entity], list[str]]]:
    """Process a ZIP archive containing Python files.

    Args:
        archive_path: Path to the ZIP archive

    Returns:
        List of entity and import tuples
    """
    results: list[tuple[list[Entity], list[str]]] = []
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.infolist():
                name = member.filename
                if name.endswith("/"):
                    continue
                p = Path(name)
                is_py = p.suffix == ".py"
                if not is_py:
                    try:
                        data = zf.read(member)
                        is_py = _looks_like_python(data)
                        source = (
                            data.decode("utf-8", errors="replace") if is_py else None
                        )
                    except Exception:
                        continue
                else:
                    try:
                        source = zf.read(member).decode("utf-8", errors="replace")
                    except Exception:
                        continue
                if is_py and source:
                    vpath = f"{archive_path.name}::{name}"
                    results.append(parse_python_source(source, vpath))
    except (zipfile.BadZipFile, OSError) as exc:
        logger.error(f"Bad zip {archive_path}: {exc}")
    return results


def _open_tar(archive_path: Path) -> tarfile.TarFile | None:
    """Open a TAR archive, handling zstd compression if needed.

    Args:
        archive_path: Path to the TAR archive

    Returns:
        TarFile object or None if error
    """
    suffix = "".join(archive_path.suffixes).lower()
    try:
        if suffix.endswith((".zst", ".tar.zst")):
            if not HAS_ZSTD:
                logger.warning(f"zstd not available, skipping {archive_path}")
                return None
            raw = zstd.decompress(archive_path.read_bytes())
            return tarfile.open(fileobj=io.BytesIO(raw))
        return tarfile.open(archive_path, mode="r:*")
    except (tarfile.TarError, OSError) as exc:
        logger.error(f"Cannot open tar {archive_path}: {exc}")
        return None


def process_tar_archive(archive_path: Path) -> list[tuple[list[Entity], list[str]]]:
    """Process a TAR archive containing Python files.

    Args:
        archive_path: Path to the TAR archive

    Returns:
        List of entity and import tuples
    """
    results: list[tuple[list[Entity], list[str]]] = []
    tf = _open_tar(archive_path)
    if tf is None:
        return results
    with tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            name = member.name
            p = Path(name)
            is_py = p.suffix == ".py"
            try:
                fobj = tf.extractfile(member)
                if fobj is None:
                    continue
                data = fobj.read()
            except Exception:
                continue
            if not is_py:
                is_py = _looks_like_python(data)
            if is_py:
                source = data.decode("utf-8", errors="replace")
                vpath = f"{archive_path.name}::{name}"
                results.append(parse_python_source(source, vpath))
    return results


def process_archive(archive_path: Path) -> list[tuple[list[Entity], list[str]]]:
    """Process an archive (ZIP or TAR) containing Python files.

    Args:
        archive_path: Path to the archive

    Returns:
        List of entity and import tuples
    """
    name = archive_path.name.lower()
    if name.endswith((".whl", ".zip")):
        return process_zip_archive(archive_path)
    return process_tar_archive(archive_path)


def _is_archive(path: Path) -> bool:
    """Check if a path is an archive file.

    Args:
        path: Path to check

    Returns:
        True if path is an archive
    """
    name = path.name.lower()
    return any(
        name.endswith(ext)
        for ext in (".whl", ".zip", ".tar.gz", ".tgz", ".tar.zst", ".tar.xz", ".tar")
    )


def discover_files(root: Path) -> tuple[list[Path], list[Path]]:
    """Discover Python files and archives in a directory tree.

    Args:
        root: Root directory to scan

    Returns:
        Tuple of Python files and archives
    """
    py_files: list[Path] = []
    archives: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in SKIP_DIRS and (not Path(dirpath, d).is_symlink())
        ]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            if fpath.suffix == ".py":
                py_files.append(fpath)
            elif _is_archive(fpath):
                archives.append(fpath)
            else:
                try:
                    if fpath.stat().st_size < 1000000:
                        data = fpath.read_bytes()
                        if _looks_like_python(data):
                            py_files.append(fpath)
                except (OSError, PermissionError):
                    pass
    return (py_files, archives)


def _worker_py(path: Path) -> tuple[list[Entity], list[str], str]:
    """Worker function for processing Python files.

    Args:
        path: Path to the file

    Returns:
        Tuple of entities, imports, and label
    """
    entities, imports = process_python_file(path)
    return (entities, imports, str(path))


def _worker_archive(path: Path) -> tuple[list[Entity], list[str], str]:
    """Worker function for processing archives.

    Args:
        path: Path to the archive

    Returns:
        Tuple of entities, imports, and label
    """
    all_entities: list[Entity] = []
    all_imports: list[str] = []
    for entities, imports in process_archive(path):
        all_entities.extend(entities)
        all_imports.extend(imports)
    return (all_entities, all_imports, str(path))


TYPE_SUBDIR = {"function": "function", "class": "class", "const": "const"}


def _safe_filename(base: str) -> str:
    """Create a safe filename from a string.

    Args:
        base: Original filename

    Returns:
        Safe filename
    """
    return re.sub(r"[^\w\-.]", "_", base)


def _unique_path(directory: Path, stem: str, suffix: str = ".py") -> Path:
    """Generate a unique path in a directory.

    Args:
        directory: Target directory
        stem: Filename stem
        suffix: Filename suffix

    Returns:
        Unique path
    """
    candidate = directory / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def write_entity(entity: Entity, output_dir: Path) -> Path | None:
    """Write an entity to a file.

    Args:
        entity: Entity to write
        output_dir: Output directory

    Returns:
        Path to written file or None if error
    """
    subdir = output_dir / TYPE_SUBDIR.get(entity.entity_type, "other")
    subdir.mkdir(parents=True, exist_ok=True)
    stem = _safe_filename(entity.full_name)
    out_path = _unique_path(subdir, stem)
    header = f"# Source: {entity.source_path}\n\n"
    all_imports = sorted(
        set(entity.imports),
        key=lambda s: 0 if s.startswith(("import ", "from ")) else 1,
    )
    import_block = "\n".join(all_imports)
    if import_block:
        import_block += "\n\n"
    content = header + import_block + entity.source
    if not content.endswith("\n"):
        content += "\n"
    try:
        out_path.write_text(content, encoding="utf-8")
        return out_path
    except OSError as exc:
        logger.error(f"Cannot write {out_path}: {exc}")
        return None


def write_global_imports(imports: list[str], output_dir: Path) -> None:
    """Write global imports to a file.

    Args:
        imports: List of import statements
        output_dir: Output directory
    """
    unique = sorted(set(imports))
    content = "# Global imports collected from all processed files\n\n"
    content += "\n".join(unique) + "\n"
    out = output_dir / "global_imports.py"
    try:
        out.write_text(content, encoding="utf-8")
        logger.info(f"Global imports saved → {out}")
    except OSError as exc:
        logger.error(f"Cannot write global imports: {exc}")


def report(entities: list[Entity], all_imports: list[str], saved_count: int) -> None:
    """Print extraction summary report.

    Args:
        entities: List of extracted entities
        all_imports: List of all imports
        saved_count: Number of entities saved
    """
    logger.info("\n" + "=" * 40)
    logger.info("EXTRACTION SUMMARY")
    logger.info("-" * 40)
    by_type: dict[str, int] = defaultdict(int)
    for e in entities:
        by_type[e.entity_type] += 1
    for etype, count in sorted(by_type.items()):
        logger.info(f"  {etype:<12}: {count}")
    logger.info(f"  {'total':<12}: {len(entities)}")
    logger.info(f"  {'saved':<12}: {saved_count}")
    module_counts: dict[str, int] = defaultdict(int)
    for stmt in all_imports:
        m = re.match(r"(?:from|import)\s+([\w.]+)", stmt)
        if m:
            module_counts[m.group(1)] += 1
    if module_counts:
        logger.info("\nTop imported modules:")
        for mod, cnt in sorted(module_counts.items(), key=lambda x: -x[1])[:15]:
            logger.info(f"  {mod:<30} {cnt}")
    logger.info("-" * 40)


def _process_batch(
    task: tuple[Callable[[Path], tuple[list[Entity], list[str], str]], Path]
) -> tuple[list[Entity], list[str], str]:
    """Process a batch task.

    Args:
        task: Tuple of worker function and path

    Returns:
        Result tuple
    """
    fn, path = task
    return fn(path)


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Extract Python code entities from files and archives."
    )
    parser.add_argument(
        "-t",
        "--tmp",
        action="store_true",
        help="Write output to ~/tmp/output/ instead of ./output/",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=8,
        help="Number of parallel workers (default: 8)",
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)",
    )
    args = parser.parse_args(argv)

    # Configure loguru
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    output_dir: Path = (
        Path.home() / "tmp" / "output" if args.tmp else Path.cwd() / "output"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    root: Path = args.dir.resolve()
    logger.info(f"Scanning: {root}")
    logger.info("\nDiscovering files…")
    py_files, archives = discover_files(root)
    logger.info(f"  Found {len(py_files)} Python files and {len(archives)} archive(s).")
    if not py_files and not archives:
        logger.info("Nothing to process.")
        return 0

    all_entities: list[Entity] = []
    all_imports: list[str] = []
    tasks: list[tuple[Callable[[Path], tuple[list[Entity], list[str], str]], Path]] = [
        (_worker_py, p) for p in py_files
    ] + [(_worker_archive, p) for p in archives]

    logger.info(f"\nProcessing {len(tasks)} file(s) with {args.workers} worker(s)…")

    # Use multiprocessing.Pool with apply_async
    with Pool(processes=args.workers) as pool:
        results: list[Any] = []
        for task in tasks:
            results.append(pool.apply_async(_process_batch, (task,)))

        for i, result in enumerate(results):
            try:
                entities, imports, label = result.get()
                logger.info(f"  ✓ {label}  ({len(entities)} entities)")
                all_entities.extend(entities)
                all_imports.extend(imports)
            except Exception as exc:
                logger.error(f"  ✗ {tasks[i][1]}: {exc}")

    logger.info(f"\nWriting {len(all_entities)} entities…")
    saved = 0
    for entity in all_entities:
        if write_entity(entity, output_dir):
            saved += 1

    write_global_imports(all_imports, output_dir)
    report(all_entities, all_imports, saved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
