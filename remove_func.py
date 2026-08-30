#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import argparse
import ast
from multiprocessing import Pool
from pathlib import Path

from dh import cprint


TARGET_NAME = "fsz"
TARGET_ARG_COUNT = 1

TARGET_SRC = """
def fsz(num_bytes: int) -> str:
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:5.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:5.1f} PiB"
"""

TARGET_AST_DUMP = ast.dump(ast.parse(TARGET_SRC).body[0])


def is_target_func(node: ast.AST, inspect_only: bool) -> bool:
    if not isinstance(node, ast.FunctionDef):
        return False

    if inspect_only:
        return node.name == TARGET_NAME and len(node.args.args) == TARGET_ARG_COUNT

    return node.name == TARGET_NAME and ast.dump(node) == TARGET_AST_DUMP


def process_file(args: tuple[Path, bool]) -> tuple[Path, bool, str]:
    filepath, inspect_only = args

    if filepath.name in {"remove_func.py", "ll.py"}:
        return filepath, False, "Skipped by filename"

    try:
        source = filepath.read_text(encoding="utf-8")
    except Exception as error:
        return filepath, False, f"Read error: {error}"

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return filepath, False, "Original file has a syntax error"

    target_funcs = [node for node in tree.body if is_target_func(node, inspect_only)]

    if not target_funcs:
        return filepath, False, "Target function not found"

    lines_to_delete: set[int] = set()

    for func in target_funcs:
        start_line = func.lineno - 1

        if func.decorator_list:
            start_line = func.decorator_list[0].lineno - 1

        end_line = func.end_lineno
        lines_to_delete.update(range(start_line, end_line))

    last_import_idx = -1

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last_import_idx = max(last_import_idx, node.end_lineno - 1)

    insert_idx = 0

    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        insert_idx = tree.body[0].end_lineno

    lines = source.splitlines(keepends=True)
    new_lines: list[str] = []
    inserted = False

    for index, line in enumerate(lines):
        if index in lines_to_delete:
            continue

        new_lines.append(line)

        if inserted:
            continue

        if last_import_idx != -1 and index == last_import_idx:
            new_lines.append("from dh import fsz\n")
            inserted = True
        elif last_import_idx == -1 and index == insert_idx - 1:
            new_lines.append("from dh import fsz\n")
            inserted = True

    if not inserted:
        new_lines.insert(0, "from dh import fsz\n")

    new_source = "".join(new_lines)

    try:
        ast.parse(new_source)
    except SyntaxError as error:
        return filepath, False, f"Validation failed: {error}"

    try:
        filepath.write_text(new_source, encoding="utf-8")
    except Exception as error:
        return filepath, False, f"Write error: {error}"

    return filepath, True, "Successfully updated"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Replace matching Python functions. By default, the complete "
            "function body must match. Use -i to match only the function "
            "name and argument count."
        )
    )

    parser.add_argument(
        "-i",
        "--inspect",
        action="store_true",
        help=(
            "Match only a function named 'fsz' with exactly one argument. "
            "Changes are applied immediately."
        ),
    )

    args = parser.parse_args()

    files = [
        filepath
        for filepath in Path(".").rglob("*.py")
        if filepath.is_file() and filepath.resolve() != Path(__file__).resolve()
    ]

    if not files:
        print("No Python files found in the current directory.")
        return

    mode = "NAME/ARGUMENT CHECK" if args.inspect else "EXACT BODY CHECK"

    print(f"Mode: {mode}")
    print(f"Found {len(files)} Python files. Processing with 8 workers...")
    print("Changes will be applied automatically.")

    work_items = [(filepath, args.inspect) for filepath in files]

    with Pool(8) as pool:
        for filepath, success, message in pool.imap_unordered(
            process_file,
            work_items,
        ):
            if success:
                cprint(f"[UPDATED] {filepath}: {message}")
            elif message != "Target function not found":
                cprint(f"[SKIPPED] {filepath}: {message}")


if __name__ == "__main__":
    main()
