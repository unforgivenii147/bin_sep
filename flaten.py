#!/data/data/com.termux/files/home/.local/bin/python
"""
Flatten current directory: move all files from subdirectories to current directory
and remove empty folders.
"""

from pathlib import Path
import shutil
import sys


def flatten_directory(directory="."):
    """
    Move all files from subdirectories to the current directory and remove empty folders.

    Args:
        directory: Path to the directory to flatten (default: current directory)
    """
    root = Path(directory).resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a valid directory")
        return

    print(f"Flattening directory: {root}")

    # Collect all files in subdirectories (non-recursive walk)
    files_to_move = []
    for subdir in root.iterdir():
        if subdir.is_dir():
            for file_path in subdir.iterdir():
                if file_path.is_file():
                    files_to_move.append(file_path)

    if not files_to_move:
        print("No files found in subdirectories.")
        return

    print(f"Found {len(files_to_move)} file(s) to move")

    # Move files to root
    moved_count = 0
    skipped_count = 0

    for file_path in files_to_move:
        target_path = root / file_path.name

        # Check if file already exists
        if target_path.exists():
            print(f"Skipping: {file_path} -> {target_path} (file already exists)")
            skipped_count += 1
            continue

        try:
            shutil.move(str(file_path), str(target_path))
            print(f"Moved: {file_path} -> {target_path}")
            moved_count += 1
        except Exception as e:
            print(f"Error moving {file_path}: {e}")

    print(f"\nMoved {moved_count} file(s), skipped {skipped_count} file(s)")

    # Remove empty subdirectories
    removed_dirs = 0
    for subdir in root.iterdir():
        if subdir.is_dir():
            try:
                # Check if directory is empty
                if not any(subdir.iterdir()):
                    subdir.rmdir()
                    print(f"Removed empty directory: {subdir}")
                    removed_dirs += 1
                else:
                    print(f"Directory not empty (skipping): {subdir}")
            except Exception as e:
                print(f"Error removing {subdir}: {e}")

    print(f"\nRemoved {removed_dirs} empty directory(ies)")
    print("Flattening complete!")


def main():
    # Use current directory by default, or accept a path as argument
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    flatten_directory(target_dir)


if __name__ == "__main__":
    main()
