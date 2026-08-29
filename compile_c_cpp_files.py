#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path


def compile_file(args):
    file_path, compiler, output_path = args
    try:
        cmd = [compiler, str(file_path), "-o", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return (
                str(file_path),
                True,
                f"✓ Compiled: {file_path.name} -> {output_path.name}",
            )
        else:
            return (
                str(file_path),
                False,
                f"✗ Failed: {file_path.name}\n{result.stderr}",
            )
    except subprocess.TimeoutExpired:
        return (str(file_path), False, f"✗ Timeout: {file_path.name}")
    except Exception as e:
        return (str(file_path), False, f"✗ Error: {file_path.name} - {e!s}")


def main():
    root_dir = Path.cwd()
    print(f"Scanning directory: {root_dir}\n")
    c_files = list(root_dir.rglob("*.c"))
    cpp_files = list(root_dir.rglob("*.cpp"))
    tasks = []
    for c_file in c_files:
        output_path = c_file.with_suffix("")
        tasks.append((c_file, "clang", output_path))
    for cpp_file in cpp_files:
        output_path = cpp_file.with_suffix("")
        tasks.append((cpp_file, "clang++", output_path))
    if not tasks:
        print("No .c or .cpp files found.")
        return
    print(f"Found {len(c_files)} .c file(s) and {len(cpp_files)} .cpp file(s)")
    print(f"Starting compilation with 4 workers...\n")
    with Pool(processes=4) as pool:
        results = pool.map(compile_file, tasks)
    print("\n" + "=" * 60)
    print("Compilation Results:")
    print("=" * 60 + "\n")
    successful = 0
    failed = 0
    for _file_path, success, message in results:
        print(message)
        if success:
            successful += 1
        else:
            failed += 1
    print("\n" + "=" * 60)
    print(f"Summary: {successful} successful, {failed} failed")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    raise SystemExit(main())
