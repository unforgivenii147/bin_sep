#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

from pathlib import Path

from dh import is_binary, is_python_file, should_skip, get_filez


def find_scripts_without_extension(directory: Path):
    swe = []
    for item in get_filez(directory):
        if should_skip(item):
            continue
        if item.is_file() and (not item.suffix):
            if is_binary(item):
                continue
            if is_python_file(item):
                swe.append(item)
    return swe


if __name__ == "__main__":
    cwd = Path.cwd()
    found_scripts = find_scripts_without_extension(cwd)
    if found_scripts:
        print("Found Python scripts without extension (relative paths):")
        for script_path in found_scripts:
            print(script_path.relative_to(cwd))
    else:
        print(
            "No Python scripts without extension found in the current directory or its subdirectories."
        )
