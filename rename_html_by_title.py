#!/data/data/com.termux/files/home/.local/bin/python

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Sequence


WORKERS = 8

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')

_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

_MAX_FILENAME_LENGTH = 240


@dataclass(slots=True, frozen=True)
class RenameResult:
    path: Path
    title: str | None
    error: str | None = None


class TitleParser(HTMLParser):
    __slots__ = ("_inside_title", "_parts", "title")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._inside_title = False
        self._parts: list[str] = []
        self.title: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title" and self.title is None:
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title" and self._inside_title:
            self._inside_title = False
            value = "".join(self._parts).strip()

            if value:
                self.title = value

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._parts.append(data)


def extract_title(path: Path) -> RenameResult:
    parser = TitleParser()

    try:
        with path.open("rb") as file:
            decoder = None

            import codecs

            decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

            while True:
                chunk = file.read(64 * 1024)
                if not chunk:
                    break

                parser.feed(decoder.decode(chunk))

                if parser.title is not None:
                    break

            if parser.title is None:
                parser.close()

    except OSError as exc:
        return RenameResult(path, None, f"{type(exc).__name__}: {exc}")
    except UnicodeError as exc:
        return RenameResult(path, None, f"{type(exc).__name__}: {exc}")
    except Exception as exc:
        return RenameResult(path, None, f"{type(exc).__name__}: {exc}")

    return RenameResult(path, parser.title)


def sanitize_filename(title: str) -> str:
    name = unicodedata.normalize("NFC", title)

    name = _INVALID_FILENAME_CHARS.sub("_", name)

    name = re.sub(r"\s+", " ", name).strip()

    name = name.rstrip(" .")

    if not name:
        return ""

    stem = name.split(".", 1)[0].upper()
    if stem in _WINDOWS_RESERVED_NAMES:
        name = f"_{name}"

    if len(name) > _MAX_FILENAME_LENGTH:
        name = name[:_MAX_FILENAME_LENGTH].rstrip(" .")

    return name


def discover_files(inputs: Sequence[str]) -> list[Path]:
    if not inputs:
        inputs = (".",)

    discovered: set[Path] = set()

    for raw in inputs:
        path = Path(raw)

        try:
            if path.is_file():
                if path.suffix.lower() in {".html", ".htm"}:
                    discovered.add(path)
                continue

            if path.is_dir():
                for candidate in path.rglob("*"):
                    try:
                        if candidate.is_file() and candidate.suffix.lower() in {
                            ".html",
                            ".htm",
                        }:
                            discovered.add(candidate)
                    except OSError:
                        continue
                continue

            print(f"warning: not found: {path}", file=sys.stderr)

        except OSError as exc:
            print(f"warning: cannot access {path}: {exc}", file=sys.stderr)

    return sorted(discovered, key=lambda p: str(p).casefold())


def unique_target(
    desired: Path,
    occupied: set[Path],
    original: Path,
) -> Path:
    if desired == original or (not desired.exists() and desired not in occupied):
        return desired

    parent = desired.parent
    stem = desired.stem
    suffix = desired.suffix

    counter = 1

    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"

        if candidate == original:
            return candidate

        if not candidate.exists() and candidate not in occupied:
            return candidate

        counter += 1


def build_operations(
    results: Iterable[RenameResult],
) -> list[tuple[Path, Path]]:
    operations: list[tuple[Path, Path]] = []

    valid = sorted(
        (result for result in results if result.error is None and result.title),
        key=lambda result: str(result.path).casefold(),
    )

    occupied_by_dir: dict[Path, set[Path]] = {}

    for result in valid:
        source = result.path
        title = result.title

        assert title is not None

        name = sanitize_filename(title)

        if not name:
            continue

        target = source.with_name(f"{name}{source.suffix}")

        if target == source:
            continue

        occupied = occupied_by_dir.setdefault(source.parent, set())

        target = unique_target(target, occupied, source)
        occupied.add(target)

        operations.append((source, target))

    return operations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename HTML files using their <title> element."
    )

    parser.add_argument(
        "paths",
        nargs="*",
        metavar="PATH",
        help=(
            "HTML files/directories to process. If omitted, the current directory is searched recursively."
        ),
    )

    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="actually rename files; default is dry-run",
    )

    return parser.parse_args()


def rename_file(source: Path, target: Path) -> tuple[bool, str | None]:
    try:
        if target.exists():
            return False, "target already exists"

        source.rename(target)
        return True, None

    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    args = parse_args()

    files = discover_files(args.paths)

    if not files:
        print("No HTML files found.")
        return 0

    print(f"Found {len(files):,} HTML file(s).")
    print(f"Parsing with {WORKERS} worker processes.")
    print()

    results: list[RenameResult] = []

    try:
        context = mp.get_context("spawn")
    except ValueError:
        context = mp.get_context()

    with context.Pool(processes=WORKERS) as pool:
        pending = [pool.apply_async(extract_title, (path,)) for path in files]

        for async_result in pending:
            try:
                results.append(async_result.get())
            except Exception as exc:
                results.append(
                    RenameResult(
                        Path("<unknown>"),
                        None,
                        f"worker failure: {type(exc).__name__}: {exc}",
                    )
                )

    errors = [result for result in results if result.error]
    operations = build_operations(results)

    for result in errors:
        print(f"ERROR  {result.path}: {result.error}", file=sys.stderr)

    if not operations:
        print("No files need renaming.")
        return 1 if errors else 0

    print(f"Planned renames: {len(operations):,}")
    print()

    if not args.apply:
        print("DRY-RUN (nothing will be changed):")
        print()

        for source, target in operations:
            print(f"{source} -> {target}")

        print()
        print("Use --apply to perform these renames.")
        return 0

    print("Applying renames:")
    print()

    success = 0
    failed = 0

    for source, target in operations:
        ok, error = rename_file(source, target)

        if ok:
            success += 1
            print(f"OK     {source} -> {target}")
        else:
            failed += 1
            print(
                f"FAILED {source} -> {target}: {error}",
                file=sys.stderr,
            )

    print()
    print(
        f"Completed: {success:,} renamed, {failed:,} failed, {len(errors):,} parse/read errors."
    )

    return 1 if failed or errors else 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
