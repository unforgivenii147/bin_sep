#!/data/data/com.termux/files/home/.local/bin/python
from collections import Counter
from pathlib import Path
from collections.abc import Generator
from typing import Any


def walk_files(directory) -> Generator[Any, Any]:
    """Generator that yields all regular files recursively, skipping symlinks and .git"""
    for entry in directory.iterdir():
        # Skip symlinks
        if entry.is_symlink():
            continue

        # Skip .git directory
        if entry.name == ".git":
            continue

        # If it's a file, yield it
        if entry.is_file():
            yield entry
        # If it's a directory, recurse into it
        elif entry.is_dir():
            yield from walk_files(entry)


def main() -> None:
    current_dir = Path.cwd()
    extension_counter = Counter()

    # Collect extensions
    for file_path in walk_files(current_dir):
        # Get extension or '.no_ext' for files without extension
        ext = file_path.suffix if file_path.suffix else ".no_ext"
        extension_counter[ext] += 1

    # Calculate column widths for alignment
    if extension_counter:
        max_ext_len = max(len(ext) for ext in extension_counter)
        max_count_len = max(len(str(count)) for count in extension_counter.values())

        print("extensions found:")
        # Sort by extension name
        for ext, count in sorted(extension_counter.items()):
            print(f" {ext:<{max_ext_len}}  {count:>{max_count_len}} files")
    else:
        print("No files found.")


if __name__ == "__main__":
    main()
