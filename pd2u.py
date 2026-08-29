#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import sys
from pathlib import Path
from dh import get_nobinary, mpf_async


def process_file(path: Path) -> None:
    data = path.read_text(encoding="utf-8")
    new_data = data.replace("\n\r", "\n")
    if data != new_data:
        path.write_text(new_data, encoding="utf-8")


def main():
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_nobinary(cwd)
    mpf_async(process_file, files)


if __name__ == "__main__":
    raise SystemExit(main())
