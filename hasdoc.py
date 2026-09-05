#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import argparse
import tokenize
from ast import Module, parse
from pathlib import Path


def check_py_files(
    root: Path = Path("."),
    allow_all: bool = False,
) -> list[Path]:
    violations: list[Path] = []
    for py_file in root.rglob("*.py"):
        try:
            print(f"checking {py_file}")
            source = py_file.read_text(encoding="utf-8")
            lines = source.splitlines()
            tree = parse(source)
            if allow_all:
                allowed_lines = _get_allowed_lines_in_all_mode(tree, lines)
                has_violation = any(
                    "#" in line
                    and line_number not in allowed_lines
                    and not _is_comment_in_string(line)
                    for line_number, line in enumerate(lines, 1)
                )
            else:
                docstring_lines = _get_docstring_lines(tree)
                argparse_lines = _find_argparse_lines(lines)
                has_violation = False
                for line_number, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if (
                        stripped.startswith("#!")
                        or stripped.startswith("# type:")
                        or stripped.startswith("# fmt:")
                    ):
                        continue
                    if line_number in docstring_lines:
                        continue
                    if line_number in argparse_lines:
                        continue
                    if "#" in line and not _is_comment_in_string(line):
                        has_violation = True
                        break
            if has_violation:
                violations.append(py_file)
        except (OSError, SyntaxError, UnicodeError):
            continue
    return violations


def _get_allowed_lines_in_all_mode(
    tree: Module,
    lines: list[str],
) -> set[int]:
    allowed_lines: set[int] = set()
    if lines and lines[0].startswith("#!"):
        allowed_lines.add(1)
    module_docstring = _get_module_docstring_node(tree)
    if module_docstring is not None:
        start = module_docstring.lineno
        end = getattr(module_docstring, "end_lineno", start)
        allowed_lines.update(range(start, end + 1))
    return allowed_lines


def _get_module_docstring_node(tree: Module):
    if not tree.body:
        return None
    first_node = tree.body[0]
    if isinstance(first_node.value, str) if hasattr(first_node, "value") else False:
        return first_node.value
    return None


def _get_docstring_lines(tree: Module) -> set[int]:
    docstring_lines: set[int] = set()
    module_docstring = _get_module_docstring_node(tree)
    if module_docstring is not None:
        start = module_docstring.lineno
        end = getattr(module_docstring, "end_lineno", start)
        docstring_lines.update(range(start, end + 1))
    for node in tree.body:
        if not hasattr(node, "body") or not node.body:
            continue
        first_node = node.body[0]
        if hasattr(first_node, "value") and isinstance(first_node.value, str):
            start = first_node.value.lineno
            end = getattr(first_node.value, "end_lineno", start)
            docstring_lines.update(range(start, end + 1))
    return docstring_lines


def _find_argparse_lines(lines: list[str]) -> set[int]:
    argparse_lines: set[int] = set()
    in_argparse = False
    paren_depth = 0
    start_line = 0
    for line_number, line in enumerate(lines, 1):
        if "ArgumentParser(" in line:
            in_argparse = True
            start_line = line_number
            paren_depth = line.count("(") - line.count(")")
            if paren_depth <= 0:
                argparse_lines.add(line_number)
                in_argparse = False
        elif in_argparse:
            argparse_lines.add(line_number)
            paren_depth += line.count("(") - line.count(")")
            if paren_depth <= 0:
                argparse_lines.update(range(start_line, line_number + 1))
                in_argparse = False
                paren_depth = 0
    return argparse_lines


def _is_comment_in_string(line: str) -> bool:
    try:
        tokens = tokenize.generate_tokens(iter([line]).__next__)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                return False
    except tokenize.TokenError:
        pass
    return "#" in line and (
        line.find("#") > line.find('"') or line.find("#") > line.find("'")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Python files for comments.")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        dest="allow_all",
        help=("Remove all restrictions except the shebang and module docstring."),
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Directory to scan. Defaults to the current directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    violations = check_py_files(args.root, allow_all=args.allow_all)
    if violations:
        print(f"❌ Found comments in {len(violations)} file(s):")
        for file in sorted(violations):
            print(f"  {file}")
        return 1
    print("✅ All .py files are clean!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
