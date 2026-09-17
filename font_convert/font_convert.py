#!/data/data/com.termux/files/home/.local/bin/python
"""Convert font files between TTF / OTF / WOFF / WOFF2 using fontTools.

This consolidates four template scripts that were ~99% identical and differed
only in the extension they scanned and the flavour they wrote:

    otf2woff2.py     .otf          -> .woff2   (TTFont flavour, keeps source)
    ttf2woff2.py     .ttf/.otf     -> .woff2   (woff2.compress, deletes source)
    woff2woff2.py    .woff         -> .woff2   (TTFont flavour, deletes source)
    woff22woff.py    .ttf/.otf     -> .woff    (TTFont flavour, deletes source)

One script now covers every direction: it scans all font extensions, skips files
that are already in the target format, and only deletes the source when you ask
for it with --rm.

Usage:
    python font_convert.py --to woff2              # every .ttf/.otf/.woff under cwd
    python font_convert.py --to woff font.woff2    # explicit files
    python font_convert.py --to ttf fonts/ --rm    # decompress, then delete source

Note: only the container flavour changes (woff/woff2 compression on or off).
Outlines are never re-generated, so a CFF font written with --to ttf keeps its
CFF outlines.
"""
from __future__ import annotations

import argparse
import sys
from functools import partial
from pathlib import Path

from dh import cprint, get_files, mpf3, unique_path
from fontTools.ttLib import TTFont

FONT_EXTS = [".ttf", ".otf", ".woff", ".woff2"]
# target extension -> fontTools flavour (None = uncompressed sfnt)
FLAVORS: dict[str, str | None] = {"woff": "woff", "woff2": "woff2", "ttf": None}


def convert(path: Path, to: str = "woff2", remove_source: bool = False) -> None:
    path = Path(path)
    target = path.with_suffix(f".{to}")
    if target.exists() and target.stat().st_size:
        target = unique_path(target)
    try:
        font = TTFont(path)
        font.flavor = FLAVORS[to]
        font.save(target)
    except Exception as exc:  # noqa: BLE001 - report and keep going
        cprint(f"error converting {path.name}: {exc}")
        return
    print(f"{path.name} -> {target.name}")
    if remove_source and path.exists():
        path.unlink()


def collect(paths: list[Path], to: str) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(get_files(p, ext=FONT_EXTS))
        elif p.exists():
            files.append(p)
        else:
            cprint(f"not found: {p}")
    if not files:
        files = get_files(Path.cwd(), ext=FONT_EXTS)
    # nothing to do for files already in the target format
    return [f for f in files if f.suffix.lower() != f".{to}"]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert TTF/OTF/WOFF/WOFF2 fonts to another container flavour."
    )
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="font files or directories (default: scan the current directory)",
    )
    ap.add_argument(
        "--to",
        required=True,
        choices=sorted(FLAVORS),
        help="target format/extension",
    )
    ap.add_argument(
        "-r",
        "--rm",
        action="store_true",
        help="delete the source file after a successful conversion",
    )
    args = ap.parse_args()

    files = collect(args.paths, args.to)
    if not files:
        cprint(f"no font files to convert to .{args.to}")
        return sys.exit(1)

    worker = partial(convert, to=args.to, remove_source=args.rm)
    if len(files) == 1:
        worker(files[0])
        return
    mpf3(worker, files)


if __name__ == "__main__":
    raise SystemExit(main())
