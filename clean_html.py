#!/data/data/com.termux/files/home/.local/bin/python

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tree_sitter import Language, Parser
import tree_sitter_css
import tree_sitter_html
import tree_sitter_javascript


WORKERS: Final = 4

HTML_LANGUAGE = Language(tree_sitter_html.language())
JS_LANGUAGE = Language(tree_sitter_javascript.language())
CSS_LANGUAGE = Language(tree_sitter_css.language())

HTML_SUFFIXES: Final = frozenset(
    {
        ".html",
        ".htm",
        ".xhtml",
        ".shtml",
    }
)

JS_TYPES: Final = frozenset(
    {
        "",
        "text/javascript",
        "application/javascript",
        "application/ecmascript",
        "text/ecmascript",
        "module",
    }
)

CSS_TYPES: Final = frozenset(
    {
        "",
        "text/css",
    }
)


@dataclass(slots=True, frozen=True)
class FileResult:
    path: Path
    changed: bool
    comments: int
    error: str | None = None


@dataclass(slots=True, frozen=True)
class ByteRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("range start cannot be negative")
        if self.end < self.start:
            raise ValueError("range end cannot precede start")


def make_parser(language: Language) -> Parser:
    return Parser(language)


def is_html_file(path: Path) -> bool:
    return path.suffix.lower() in HTML_SUFFIXES


def discover_files(inputs: list[str]) -> list[Path]:
    if not inputs:
        roots = [Path.cwd()]
    else:
        roots = [Path(item).expanduser() for item in inputs]

    found: set[Path] = set()

    for root in roots:
        try:
            root = root.resolve()
        except OSError:
            root = root.absolute()

        if root.is_file():
            if is_html_file(root):
                found.add(root)
            continue

        if not root.is_dir():
            print(f"warning: not found: {root}", file=sys.stderr)
            continue

        try:
            for path in root.rglob("*"):
                try:
                    if path.is_file() and not path.is_symlink() and is_html_file(path):
                        found.add(path)
                except OSError as exc:
                    print(
                        f"warning: cannot inspect {path}: {exc}",
                        file=sys.stderr,
                    )
        except OSError as exc:
            print(
                f"warning: cannot scan {root}: {exc}",
                file=sys.stderr,
            )

    return sorted(found)


def decode_html(data: bytes) -> tuple[str, str]:
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8"), "utf-8-sig"

    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le"), "utf-16-le"

    if data.startswith(b"\xfe\xff"):
        return data[2:].decode("utf-16-be"), "utf-16-be"

    return data.decode("utf-8"), "utf-8"


def node_text(source: bytes, node: object) -> bytes:
    return source[node.start_byte : node.end_byte]


def walk_tree(root: object):
    stack = [root]

    while stack:
        node = stack.pop()
        yield node

        children = node.children

        stack.extend(reversed(children))


def collect_html_comments(root: object) -> list[ByteRange]:
    ranges: list[ByteRange] = []

    for node in walk_tree(root):
        if node.type == "comment":
            ranges.append(ByteRange(node.start_byte, node.end_byte))

    return ranges


def find_embedded_ranges(
    root: object,
) -> tuple[list[ByteRange], list[ByteRange]]:
    js_ranges: list[ByteRange] = []
    css_ranges: list[ByteRange] = []

    for node in walk_tree(root):
        if node.type not in {"script_element", "style_element"}:
            continue

        raw_nodes = [child for child in node.children if child.type == "raw_text"]

        if not raw_nodes:
            continue

        if node.type == "script_element":
            js_ranges.extend(
                ByteRange(child.start_byte, child.end_byte)
                for child in raw_nodes
                if child.end_byte > child.start_byte
            )
        else:
            css_ranges.extend(
                ByteRange(child.start_byte, child.end_byte)
                for child in raw_nodes
                if child.end_byte > child.start_byte
            )

    return js_ranges, css_ranges


def parse_comments(
    source: bytes,
    ranges: list[ByteRange],
    language: Language,
) -> list[ByteRange]:
    if not ranges:
        return []

    parser = make_parser(language)
    comments: list[ByteRange] = []

    for byte_range in ranges:
        content = source[byte_range.start : byte_range.end]

        if not content:
            continue

        tree = parser.parse(content)

        for node in walk_tree(tree.root_node):
            if node.type != "comment":
                continue

            comments.append(
                ByteRange(
                    byte_range.start + node.start_byte,
                    byte_range.start + node.end_byte,
                )
            )

    return comments


def merge_ranges(ranges: list[ByteRange]) -> list[ByteRange]:
    if not ranges:
        return []

    ranges.sort(key=lambda item: (item.start, item.end))

    merged: list[ByteRange] = [ranges[0]]

    for current in ranges[1:]:
        previous = merged[-1]

        if current.start <= previous.end:
            merged[-1] = ByteRange(
                previous.start,
                max(previous.end, current.end),
            )
        else:
            merged.append(current)

    return merged


def replace_range_with_whitespace(
    output: bytearray,
    source: bytes,
    byte_range: ByteRange,
) -> None:
    start = byte_range.start
    end = byte_range.end

    i = start

    while i < end:
        byte = source[i]

        if byte == 0x0A:
            i += 1
            continue

        if byte == 0x0D:
            i += 1
            continue

        output[i] = 0x20
        i += 1


def strip_comments(source: bytes) -> tuple[bytes, int]:
    html_parser = make_parser(HTML_LANGUAGE)
    html_tree = html_parser.parse(source)

    ranges = collect_html_comments(html_tree)

    js_ranges, css_ranges = find_embedded_ranges(html_tree)

    ranges.extend(
        parse_comments(
            source,
            js_ranges,
            JS_LANGUAGE,
        )
    )

    ranges.extend(
        parse_comments(
            source,
            css_ranges,
            CSS_LANGUAGE,
        )
    )

    ranges = merge_ranges(ranges)

    if not ranges:
        return source, 0

    output = bytearray(source)

    for byte_range in ranges:
        replace_range_with_whitespace(
            output,
            source,
            byte_range,
        )

    return bytes(output), len(ranges)


def atomic_write(path: Path, data: bytes, original_stat: os.stat_result) -> None:
    directory = path.parent

    fd: int | None = None
    temporary: Path | None = None

    try:
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=directory,
        )
        temporary = Path(temporary_name)

        with os.fdopen(fd, "wb") as file:
            fd = None

            file.write(data)
            file.flush()
            os.fsync(file.fileno())

        os.chmod(temporary, original_stat.st_mode & 0o7777)

        try:
            os.chown(
                temporary,
                original_stat.st_uid,
                original_stat.st_gid,
            )
        except (AttributeError, PermissionError, OSError):
            pass

        os.replace(temporary, path)
        temporary = None

    finally:
        if fd is not None:
            os.close(fd)

        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def process_file(path: Path) -> FileResult:
    try:
        original_stat = path.stat()

        if not path.is_file():
            return FileResult(
                path=path,
                changed=False,
                comments=0,
                error="not a regular file",
            )

        source = path.read_bytes()

        if not source:
            return FileResult(
                path=path,
                changed=False,
                comments=0,
            )

        text, encoding = decode_html(source)

        if encoding != "utf-8":
            source = text.encode("utf-8")

        modified, comments = strip_comments(source)

        if comments == 0:
            return FileResult(
                path=path,
                changed=False,
                comments=0,
            )

        if encoding == "utf-16-le":
            modified = b"\xff\xfe" + modified.decode("utf-8").encode("utf-16-le")
        elif encoding == "utf-16-be":
            modified = b"\xfe\xff" + modified.decode("utf-8").encode("utf-16-be")
        elif encoding == "utf-8-sig":
            modified = b"\xef\xbb\xbf" + modified

        atomic_write(
            path,
            modified,
            original_stat,
        )

        return FileResult(
            path=path,
            changed=True,
            comments=comments,
        )

    except UnicodeDecodeError as exc:
        return FileResult(
            path=path,
            changed=False,
            comments=0,
            error=f"decode error: {exc}",
        )
    except PermissionError as exc:
        return FileResult(
            path=path,
            changed=False,
            comments=0,
            error=f"permission denied: {exc}",
        )
    except OSError as exc:
        return FileResult(
            path=path,
            changed=False,
            comments=0,
            error=f"I/O error: {exc}",
        )
    except Exception as exc:
        return FileResult(
            path=path,
            changed=False,
            comments=0,
            error=f"{type(exc).__name__}: {exc}",
        )


def print_result(result: FileResult) -> None:
    if result.error:
        print(
            f"ERROR   {result.path}: {result.error}",
            file=sys.stderr,
        )
        return

    if result.changed:
        print(
            f"STRIPPED {result.path} "
            f"({result.comments} comment"
            f"{'' if result.comments == 1 else 's'})"
        )
    else:
        print(f"OK      {result.path} (no comments)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Strip HTML, inline JavaScript, and inline CSS comments using Tree-sitter."
        ),
    )

    parser.add_argument(
        "paths",
        nargs="*",
        metavar="PATH",
        help=(
            "HTML files and/or directories. Directories are searched "
            "recursively. If omitted, the current directory is searched."
        ),
    )

    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=WORKERS,
        metavar="N",
        help=f"number of worker processes (default: {WORKERS})",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.workers < 1:
        print(
            "error: --workers must be >= 1",
            file=sys.stderr,
        )
        return 2

    files = discover_files(args.paths)

    if not files:
        print("No HTML files found.", file=sys.stderr)
        return 0

    print(
        f"Processing {len(files)} HTML file"
        f"{'' if len(files) == 1 else 's'} "
        f"with {args.workers} workers..."
    )

    ctx = mp.get_context("spawn")

    processed = 0
    changed = 0
    comment_count = 0
    errors = 0

    with ctx.Pool(processes=args.workers) as pool:
        pending = [pool.apply_async(process_file, (path,)) for path in files]

        for job in pending:
            try:
                result = job.get()
            except Exception as exc:
                print(
                    f"ERROR   worker failure: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                errors += 1
                continue

            processed += 1
            comment_count += result.comments

            if result.changed:
                changed += 1

            if result.error:
                errors += 1

            print_result(result)

    print(
        "\nSummary:"
        f"\n  files processed : {processed}"
        f"\n  files changed   : {changed}"
        f"\n  comments stripped: {comment_count}"
        f"\n  errors          : {errors}"
    )

    return 1 if errors else 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
