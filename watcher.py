#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

from watchfiles import watch
from pathlib import Path


if __name__ == "__main__":
    cwd = Path.cwd().resolve()
    print(f"watching {cwd} for changes ...")
    for change in watch(str(cwd)):
        print(change)
