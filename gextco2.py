#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import ast
import os
import re
import sys
import tarfile
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Tuple

SKIP_DIRS = frozenset(
    {".git", "__pycache__", ".venv", "node_modules", ".env", ".pytest_cache"}
)
COMMON_IMPORTS = {
    "typing": {
        "List",
        "Dict",
        "Set",
        "Tuple",
        "Optional",
        "Union",
        "Any",
        "Callable",
        "Type",
        "Generic",
        "TypeVar",
        "cast",
        "overload",
        "Protocol",
        "Iterator",
        "Iterable",
        "Sequence",
        "Mapping",
    },
    "dataclasses": {
        "dataclass",
        "field",
        "InitVar",
        "FrozenInstanceError",
        "MISSING",
        "fields",
        "asdict",
        "astuple",
        "make_dataclass",
        "replace",
    },
    "functools": {
        "lru_cache",
        "wraps",
        "partial",
        "total_ordering",
        "reduce",
        "cmp_to_key",
        "singledispatch",
    },
    "itertools": {
        "combinations",
        "permutations",
        "product",
        "chain",
        "groupby",
        "repeat",
        "cycle",
        "islice",
        "takewhile",
        "dropwhile",
    },
    "pathlib": {
        "Path",
        "PurePath",
        "PureWindowsPath",
        "PurePosixPath",
        "WindowsPath",
        "PosixPath",
    },
    "datetime": {
        "datetime",
        "date",
        "time",
        "timedelta",
        "timezone",
        "tzinfo",
        "strptime",
        "now",
    },
    "json": {"dumps", "loads", "dump", "load", "JSONEncoder", "JSONDecoder"},
    "re": {
        "compile",
        "match",
        "search",
        "findall",
        "finditer",
        "sub",
        "split",
        "escape",
        "IGNORECASE",
        "MULTILINE",
        "DOTALL",
    },
    "collections": {
        "defaultdict",
        "OrderedDict",
        "Counter",
        "deque",
        "namedtuple",
        "ChainMap",
    },
    "enum": {"Enum", "IntEnum", "Flag", "IntFlag", "auto", "unique"},
    "abc": {
        "ABC",
        "abstractmethod",
        "abstractproperty",
        "ABCMeta",
        "abstractclassmethod",
    },
    "contextlib": {
        "contextmanager",
        "closing",
        "suppress",
        "redirect_stdout",
        "redirect_stderr",
    },
    "copy": {"copy", "deepcopy"},
    "pickle": {"dumps", "loads", "dump", "load"},
    "logging": {
        "getLogger",
        "debug",
        "info",
        "warning",
        "error",
        "critical",
        "basicConfig",
    },
    "os": {
        "path",
        "environ",
        "getcwd",
        "chdir",
        "listdir",
        "mkdir",
        "makedirs",
        "remove",
        "rmdir",
    },
    "sys": {"argv", "exit", "stdout", "stderr", "stdin", "path", "modules"},
    "subprocess": {"run", "Popen", "PIPE", "STDOUT", "CalledProcessError"},
    "threading": {"Thread", "Lock", "RLock", "Condition", "Semaphore", "Event"},
    "asyncio": {"run", "gather", "create_task", "sleep", "Queue", "Event", "Lock"},
    "urllib": {"request", "parse", "error"},
    "requests": {"get", "post", "put", "delete", "Session", "Response"},
    "numpy": {"array", "zeros", "ones", "arange", "linspace", "ndarray"},
    "pandas": {"DataFrame", "Series", "read_csv", "read_excel", "concat", "merge"},
}


@dataclass
class Entity:
    name: str
    type: str
    source: str
    full_name: str
    source_file: str
    line_number: int
    imports: set[str] = field(default_factory=set)
    decorators: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    filepath: str
    entities: list[Entity] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)


class ImportAnalyzer:
    @staticmethod
    def extract_imports_from_source(source: str) -> set[str]:
        imports = set()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join((alias.name for alias in node.names))
                    if node.level > 0:
                        module = "." * node.level + module
                    imports.add(f"from {module} import {names}")
        except SyntaxError:
            pass
        return imports

    @staticmethod
    def detect_needed_imports(source: str) -> set[str]:
        needed = set()
        source_lower = source.lower()
        for module, symbols in COMMON_IMPORTS.items():
            for symbol in symbols:
                if re.search(f"\\b{re.escape(symbol)}\\b", source):
                    if module == "typing":
                        needed.add(f"from typing import {symbol}")
                    elif module == "dataclasses":
                        needed.add(f"from dataclasses import {symbol}")
                    elif module == "abc":
                        needed.add(f"from abc import {symbol}")
                    elif module == "functools":
                        needed.add(f"from functools import {symbol}")
                    elif module == "enum":
                        needed.add(f"from enum import {symbol}")
                    else:
                        needed.add(f"from {module} import {symbol}")
        if "@property" in source:
            pass
        if "@" in source and "staticmethod" in source:
            pass
        if "Path(" in source or "PurePath(" in source:
            needed.add("from pathlib import Path")
        if "datetime(" in source or "date(" in source:
            needed.add("from datetime import datetime, date")
        if "logging.getLogger" in source or "logger =" in source:
            needed.add("import logging")
        return needed

    @staticmethod
    def consolidate_imports(existing: set[str], needed: set[str]) -> list[str]:
        all_imports = existing | needed
        organized = []
        stdlib_imports = []
        thirdparty_imports = []
        local_imports = []
        for imp in sorted(all_imports):
            if imp.startswith("from .") or imp.startswith("import ."):
                local_imports.append(imp)
            elif imp.startswith("from typing") or imp.startswith("import typing"):
                stdlib_imports.insert(0, imp)
            elif any(
                (
                    imp.startswith(f"from {mod}") or imp.startswith(f"import {mod}")
                    for mod in [
                        "os",
                        "sys",
                        "json",
                        "re",
                        "pathlib",
                        "datetime",
                        "asyncio",
                        "subprocess",
                        "threading",
                        "logging",
                    ]
                )
            ):
                stdlib_imports.append(imp)
            else:
                thirdparty_imports.append(imp)
        organized.extend(sorted(stdlib_imports))
        if thirdparty_imports:
            organized.extend([""] + sorted(thirdparty_imports))
        if local_imports:
            organized.extend([""] + sorted(local_imports))
        return [imp for imp in organized if imp]


class EntityVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: list[str], filepath: str):
        self.source_lines = source_lines
        self.filepath = filepath
        self.entities: list[Entity] = []
        self.current_class: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        source = self._get_source_slice(node)
        self.entities.append(
            Entity(
                name=node.name,
                type="class",
                source=source,
                full_name=node.name,
                source_file=self.filepath,
                line_number=node.lineno,
                decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            )
        )
        old_class = self.current_class
        self.current_class = node.name
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function(
                    item, is_async=isinstance(item, ast.AsyncFunctionDef), in_class=True
                )
            self.visit(item)
        self.current_class = old_class

    def visit_Assign(self, node: ast.Assign):
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name) and self._is_constant_name(target.id):
                    source = self._get_source_slice(node)
                    self.entities.append(
                        Entity(
                            name=target.id,
                            type="constant",
                            source=source,
                            full_name=target.id,
                            source_file=self.filepath,
                            line_number=node.lineno,
                        )
                    )
        self.generic_visit(node)

    def _process_function(self, node, is_async: bool = False, in_class: bool = False):
        source = self._get_source_slice(node)
        entity_type = "method" if in_class else "function"
        full_name = f"{self.current_class}_{node.name}" if in_class else node.name
        self.entities.append(
            Entity(
                name=node.name,
                type=entity_type,
                source=source,
                full_name=full_name,
                source_file=self.filepath,
                line_number=node.lineno,
                decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            )
        )

    def _get_source_slice(self, node: ast.stmt) -> str:
        if not self.source_lines:
            return ""
        start_line = node.lineno - 1
        end_line = node.end_lineno or node.lineno
        start_line = max(0, start_line)
        end_line = min(len(self.source_lines), end_line)
        lines = self.source_lines[start_line:end_line]
        return "".join(lines)

    @staticmethod
    def _get_decorator_name(decorator: ast.expr) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""

    @staticmethod
    def _is_constant_name(name: str) -> bool:
        return bool(re.match("^[A-Z_][A-Z0-9_]*$", name))


def is_python_file(path: Path) -> bool:
    if path.suffix == ".py":
        return True
    try:
        with open(path, "rb") as f:
            first_line = f.readline()
            if first_line.startswith(b"#!"):
                return b"python" in first_line
    except (OSError, IOError):
        pass
    return False


def extract_from_file(filepath: Path) -> ExtractionResult:
    result = ExtractionResult(str(filepath))
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            result.errors.append(f"Syntax error: {e}")
            return result
        result.imports = ImportAnalyzer.extract_imports_from_source(source)
        source_lines = source.split("\n")
        visitor = EntityVisitor(source_lines, str(filepath))
        visitor.visit(tree)
        result.entities = visitor.entities
    except Exception as e:
        result.errors.append(f"Error processing file: {e}")
    return result


def extract_from_archive(
    archive_path: Path, archive_type: str
) -> list[tuple[str, str]]:
    results = []
    if archive_type == ".zip" or archive_type == ".whl":
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                for member in zf.namelist():
                    if member.endswith(".py"):
                        try:
                            content = zf.read(member).decode("utf-8", errors="ignore")
                            virtual_path = f"{archive_path.name}::{member}"
                            results.append((virtual_path, content))
                        except Exception:
                            pass
        except Exception:
            pass
    elif archive_type in {".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar"}:
        try:
            with tarfile.open(archive_path, "r:*") as tf:
                for member in tf.getmembers():
                    if member.name.endswith(".py") and member.isfile():
                        try:
                            f = tf.extractfile(member)
                            if f:
                                content = f.read().decode("utf-8", errors="ignore")
                                virtual_path = f"{archive_path.name}::{member.name}"
                                results.append((virtual_path, content))
                        except Exception:
                            pass
        except Exception:
            pass
    elif archive_type == ".tar.zst":
        if not HAS_ZSTD:
            return results
        try:
            with open(archive_path, "rb") as f:
                dctx = zstd.ZstdDecompressor()
                with (
                    dctx.stream_reader(f) as reader,
                    tarfile.open(fileobj=reader, mode="r|") as tf,
                ):
                    for member in tf:
                        if member.name.endswith(".py") and member.isfile():
                            try:
                                f_obj = tf.extractfile(member)
                                if f_obj:
                                    content = f_obj.read().decode(
                                        "utf-8", errors="ignore"
                                    )
                                    virtual_path = f"{archive_path.name}::{member.name}"
                                    results.append((virtual_path, content))
                            except Exception:
                                pass
        except Exception:
            pass
    return results


def extract_from_archive_member(virtual_path: str, source: str) -> ExtractionResult:
    result = ExtractionResult(virtual_path)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        result.errors.append(f"Syntax error: {e}")
        return result
    result.imports = ImportAnalyzer.extract_imports_from_source(source)
    source_lines = source.split("\n")
    visitor = EntityVisitor(source_lines, virtual_path)
    visitor.visit(tree)
    result.entities = visitor.entities
    return result


def process_file_worker(filepath: Path) -> ExtractionResult:
    return extract_from_file(filepath)


def process_archive_member_worker(args: tuple[str, str]) -> ExtractionResult:
    virtual_path, source = args
    return extract_from_archive_member(virtual_path, source)


def scan_directory(directory: str) -> tuple[list[Path], list[tuple[str, str]]]:
    base_dir = Path(directory).resolve()
    python_files = []
    archive_members = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for filename in files:
            filepath = root_path / filename
            if filepath.is_symlink():
                continue
            if is_python_file(filepath):
                python_files.append(filepath)
            elif filepath.suffix in {".zip", ".whl"}:
                members = extract_from_archive(filepath, filepath.suffix)
                archive_members.extend(members)
            elif filepath.suffix in {".gz", ".bz2", ".xz", ".zst"}:
                name = filepath.name
                if name.endswith(".tar.gz") or name.endswith(".tgz"):
                    archive_type = ".tar.gz"
                elif name.endswith(".tar.bz2"):
                    archive_type = ".tar.bz2"
                elif name.endswith(".tar.xz"):
                    archive_type = ".tar.xz"
                elif name.endswith(".tar.zst"):
                    archive_type = ".tar.zst"
                else:
                    continue
                members = extract_from_archive(filepath, archive_type)
                archive_members.extend(members)
            elif filepath.suffix == ".tar":
                members = extract_from_archive(filepath, ".tar")
                archive_members.extend(members)
    return (python_files, archive_members)


def write_entity(output_dir: Path, entity: Entity) -> Optional[Path]:
    entity_dir = output_dir / entity.type
    entity_dir.mkdir(parents=True, exist_ok=True)
    base_filename = entity.full_name.replace("::", "_").replace("/", "_")
    filename = f"{base_filename}.py"
    filepath = entity_dir / filename
    counter = 1
    while filepath.exists():
        counter += 1
        filepath = entity_dir / f"{base_filename}_{counter}.py"
    existing_imports = ImportAnalyzer.extract_imports_from_source(entity.source)
    needed_imports = ImportAnalyzer.detect_needed_imports(entity.source)
    imports = ImportAnalyzer.consolidate_imports(existing_imports, needed_imports)
    lines = []
    lines.append(f"# Extracted from: {entity.source_file}:{entity.line_number}\n")
    if imports:
        lines.extend([imp + "\n" for imp in imports])
        lines.append("\n")
    lines.append(entity.source)
    if not entity.source.endswith("\n"):
        lines.append("\n")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return filepath
    except Exception as e:
        print(f"Error writing entity: {e}", file=sys.stderr)
        return None


def write_imports_file(output_dir: Path, all_imports: set[str]):
    organized = ImportAnalyzer.consolidate_imports(all_imports, set())
    filepath = output_dir / "imports.py"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Aggregated imports from extracted entities\n\n")
        for imp in organized:
            f.write(imp + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Python code entities from files and archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\nExamples:\n\n  python extract_entities.py\n\n\n  python extract_entities.py -t\n\n\n  python extract_entities.py --workers 16\n        ",
    )
    parser.add_argument(
        "-t",
        "--temp",
        action="store_true",
        help="Save to ~/tmp/output/ instead of ./output/",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(os.cpu_count() or 4, 8),
        help="Number of worker processes",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    args = parser.parse_args()
    if args.temp:
        output_dir = Path.home() / "tmp" / "output"
    else:
        output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Scanning directory: {Path(args.directory).resolve()}")
    print(f"Output directory: {output_dir.resolve()}\n")
    python_files, archive_members = scan_directory(args.directory)
    print(
        f"Found {len(python_files):,} Python files and {len(archive_members):,} archive members"
    )
    print()
    all_entities: list[Entity] = []
    all_imports: set[str] = set()
    entity_count = {"function": 0, "class": 0, "method": 0, "constant": 0}
    error_count = 0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_file_worker, fpath): ("file", str(fpath))
            for fpath in python_files
        }
        for virtual_path, source in archive_members:
            futures[
                executor.submit(process_archive_member_worker, (virtual_path, source))
            ] = ("archive", virtual_path)
        processed = 0
        for future in as_completed(futures):
            _source_type, source_path = futures[future]
            processed += 1
            try:
                result = future.result()
                all_entities.extend(result.entities)
                all_imports.update(result.imports)
                for entity in result.entities:
                    entity_count[entity.type] += 1
                if result.errors:
                    error_count += len(result.errors)
                    for error in result.errors:
                        print(f"  Error in {source_path}: {error}", file=sys.stderr)
                if processed % 50 == 0:
                    print(f"  Processed: {processed}/{len(futures)}", end="\r")
            except Exception as e:
                error_count += 1
                print(f"  Error processing {source_path}: {e}", file=sys.stderr)
    print(f"\n\nExtracted {len(all_entities):,} entities:")
    for etype, count in entity_count.items():
        if count > 0:
            print(f"  {etype}: {count}")
    print("\nWriting entities to output directory...")
    written_count = 0
    for entity in all_entities:
        if write_entity(output_dir, entity):
            written_count += 1
    print(f"Saved {written_count}/{len(all_entities)} entities\n")
    write_imports_file(output_dir, all_imports)
    print("Saved aggregated imports to imports.py")
    print(f"\nTotal unique imports: {len(all_imports)}")
    if error_count > 0:
        print(f"Errors encountered: {error_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
