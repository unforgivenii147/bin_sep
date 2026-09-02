#!/data/data/com.termux/files/home/.local/bin/python
"""
Convert concurrent.futures ThreadPoolExecutor/ProcessPoolExecutor patterns
to multiprocessing.Pool.apply_async with fixed 8 workers.

This script processes Python files to replace concurrent.futures executor patterns
with multiprocessing.Pool.apply_async equivalents using a fixed pool of 8 workers.

Usage:
    python convert_executors.py [files/dirs...] [-a|--apply]

Features:
    - Accepts multiple files and directories as input
    - Recursively processes Python files in directories
    - Shows diff in dry-run mode (default)
    - Applies changes in-place with -a/--apply flag
    - Uses multiprocessing imap_unordered for parallel file processing
    - Fixed pool size of 8 workers
"""

import argparse
import difflib
import multiprocessing as mp
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Sequence, Tuple

# Fixed number of workers
WORKERS = 8

# Maximum file size to process (1MB) to avoid memory issues with huge files
MAX_FILE_SIZE = 1024 * 1024

# Python file extensions to process
PYTHON_EXTENSIONS = {'.py', '.pyw', '.pyi'}

# Patterns for concurrent.futures imports
IMPORT_PATTERNS = [
    # from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
    re.compile(
        r'^(\s*)from\s+concurrent\.futures\s+import\s+'
        r'([^#\n]*ThreadPoolExecutor[^#\n]*)$',
        re.MULTILINE
    ),
    re.compile(
        r'^(\s*)from\s+concurrent\.futures\s+import\s+'
        r'([^#\n]*ProcessPoolExecutor[^#\n]*)$',
        re.MULTILINE
    ),
    # import concurrent.futures
    re.compile(
        r'^(\s*)import\s+concurrent\.futures\s*$',
        re.MULTILINE
    ),
    # from concurrent.futures import as_completed, wait, etc.
    re.compile(
        r'^(\s*)from\s+concurrent\.futures\s+import\s+'
        r'([^#\n]*)(as_completed|wait|Future|Executor|ALL_COMPLETED|FIRST_COMPLETED)[^#\n]*$',
        re.MULTILINE
    ),
]

# Pattern for ThreadPoolExecutor instantiation
THREAD_POOL_PATTERN = re.compile(
    r'(\bThreadPoolExecutor\s*\()\s*'
    r'(?:max_workers\s*=\s*)?(\d+)?\s*\)?',
    re.MULTILINE
)

# Pattern for ProcessPoolExecutor instantiation
PROCESS_POOL_PATTERN = re.compile(
    r'(\bProcessPoolExecutor\s*\()\s*'
    r'(?:max_workers\s*=\s*)?(\d+)?\s*\)?',
    re.MULTILINE
)

# Pattern for executor.submit
SUBMIT_PATTERN = re.compile(
    r'(\w+)\s*\.\s*submit\s*\(\s*'
    r'([^,]+)\s*(?:,\s*([^)]*?))?\)',
    re.MULTILINE
)

# Pattern for executor.map
EXECUTOR_MAP_PATTERN = re.compile(
    r'(\w+)\s*\.\s*map\s*\(',
    re.MULTILINE
)

# Pattern for as_completed
AS_COMPLETED_PATTERN = re.compile(
    r'(\b)as_completed\s*\(',
    re.MULTILINE
)

# Pattern for context manager with executor
WITH_EXECUTOR_PATTERN = re.compile(
    r'with\s+(ThreadPoolExecutor|ProcessPoolExecutor)\s*\([^)]*\)\s+as\s+(\w+)\s*:',
    re.MULTILINE
)

# Pattern for executor.shutdown
SHUTDOWN_PATTERN = re.compile(
    r'(\w+)\s*\.\s*shutdown\s*\([^)]*\)\s*',
    re.MULTILINE
)

# Pattern for future.result()
FUTURE_RESULT_PATTERN = re.compile(
    r'(\w+)\s*\.\s*result\s*\(\s*\)',
    re.MULTILINE
)

# Pattern for future.done()
FUTURE_DONE_PATTERN = re.compile(
    r'(\w+)\s*\.\s*done\s*\(\s*\)',
    re.MULTILINE
)

# Pattern for future.cancelled()
FUTURE_CANCELLED_PATTERN = re.compile(
    r'(\w+)\s*\.\s*cancelled\s*\(\s*\)',
    re.MULTILINE
)

# Pattern for future.cancel()
FUTURE_CANCEL_PATTERN = re.compile(
    r'(\w+)\s*\.\s*cancel\s*\(\s*\)',
    re.MULTILINE
)

# Pattern for future.exception()
FUTURE_EXCEPTION_PATTERN = re.compile(
    r'(\w+)\s*\.\s*exception\s*\(\s*\)',
    re.MULTILINE
)


@dataclass
class FileResult:
    """Result of processing a single file."""
    path: Path
    original: str
    converted: str
    error: Optional[str] = None
    changed: bool = False

    @property
    def diff(self) -> str:
        """Generate unified diff between original and converted content."""
        if not self.changed:
            return ""
        return ''.join(difflib.unified_diff(
            self.original.splitlines(keepends=True),
            self.converted.splitlines(keepends=True),
            fromfile=str(self.path),
            tofile=f"{self.path} (converted)",
        ))


def collect_python_files(paths: Sequence[Path]) -> list[Path]:
    """
    Collect Python files from the given paths.

    If no paths are provided, scan the current directory recursively.

    Args:
        paths: Sequence of file/directory paths to scan.

    Returns:
        List of unique Python file paths.
    """
    files: set[Path] = set()

    if not paths:
        paths = [Path('.')]

    for path in paths:
        if path.is_file():
            if path.suffix.lower() in PYTHON_EXTENSIONS:
                files.add(path.resolve())
        elif path.is_dir():
            for ext in PYTHON_EXTENSIONS:
                files.update(
                    p.resolve() for p in path.rglob(f'*{ext}')
                )
        else:
            print(f"Warning: {path} does not exist", file=sys.stderr)

    return sorted(files)


def convert_imports(content: str) -> str:
    """
    Convert concurrent.futures import statements to multiprocessing.Pool imports.

    Args:
        content: Source code content.

    Returns:
        Content with converted imports.
    """
    lines = content.splitlines(keepends=True)
    new_lines = []
    has_futures_import = False

    for line in lines:
        stripped = line.strip()
        # Skip blank lines and comments
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue

        # Check if this is a concurrent.futures import
        is_futures_import = False
        for pattern in IMPORT_PATTERNS:
            if pattern.search(line):
                is_futures_import = True
                has_futures_import = True
                break

        if is_futures_import:
            # Replace with multiprocessing import if not already added
            if not any('multiprocessing' in l for l in new_lines):
                new_lines.append('import multiprocessing as mp\n')
            continue

        new_lines.append(line)

    result = ''.join(new_lines)

    # If we found futures imports but didn't add multiprocessing import
    if has_futures_import and 'multiprocessing' not in result:
        # Find first import line to add after it
        lines = result.splitlines(keepends=True)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_idx = i + 1
        lines.insert(insert_idx, 'import multiprocessing as mp\n')
        result = ''.join(lines)

    return result


def convert_executor_instantiation(content: str) -> str:
    """
    Convert ThreadPoolExecutor/ProcessPoolExecutor instantiation to mp.Pool.

    Args:
        content: Source code content.

    Returns:
        Content with converted executor instantiation.
    """
    def replace_pool(match: re.Match) -> str:
        """Replace executor instantiation with mp.Pool."""
        # Always use fixed 8 workers
        return f'{match.group(1)[:0]}mp.Pool(processes=8)'

    # Handle context manager pattern: with ThreadPoolExecutor(...) as executor:
    content = WITH_EXECUTOR_PATTERN.sub(
        lambda m: f'with mp.Pool(processes=8) as {m.group(2)}:',
        content
    )

    # Handle direct instantiation: executor = ThreadPoolExecutor(...)
    content = THREAD_POOL_PATTERN.sub(
        lambda m: 'mp.Pool(processes=8)',
        content
    )
    content = PROCESS_POOL_PATTERN.sub(
        lambda m: 'mp.Pool(processes=8)',
        content
    )

    return content


def convert_submit_calls(content: str) -> str:
    """
    Convert executor.submit() calls to pool.apply_async().

    Args:
        content: Source code content.

    Returns:
        Content with converted submit calls.
    """
    def replace_submit(match: re.Match) -> str:
        executor_name = match.group(1)
        func_name = match.group(2).strip()
        args = match.group(3).strip() if match.group(3) else ''

        # Build the apply_async call
        if args:
            # Check if args are keyword arguments
            if '=' in args and ',' not in args:
                # Single keyword argument - this is tricky, need to convert
                # to a tuple or use args parameter
                return f'{executor_name}.apply_async({func_name}, kwds={{{args}}})'
            else:
                return f'{executor_name}.apply_async({func_name}, args=({args},))'
        else:
            return f'{executor_name}.apply_async({func_name})'

    return SUBMIT_PATTERN.sub(replace_submit, content)


def convert_map_calls(content: str) -> str:
    """
    Convert executor.map() calls to pool.map() or pool.imap_unordered().

    Args:
        content: Source code content.

    Returns:
        Content with converted map calls.
    """
    # Simple replacement: .map( -> .map( (multiprocessing Pool has map too)
    # But we need to handle the case where it's used with executor name
    content = EXECUTOR_MAP_PATTERN.sub(
        lambda m: f'{m.group(1)}.map(',
        content
    )
    return content


def convert_shutdown_calls(content: str) -> str:
    """
    Convert executor.shutdown() calls to pool.close() and pool.join().

    Args:
        content: Source code content.

    Returns:
        Content with converted shutdown calls.
    """
    def replace_shutdown(match: re.Match) -> str:
        pool_name = match.group(1)
        return f'{pool_name}.close()\n{pool_name}.join()'

    return SHUTDOWN_PATTERN.sub(replace_shutdown, content)


def convert_as_completed(content: str) -> str:
    """
    Convert as_completed() pattern to apply_async with callback.

    Args:
        content: Source code content.

    Returns:
        Content with converted as_completed pattern.
    """
    # For now, just add a comment indicating manual conversion needed
    if AS_COMPLETED_PATTERN.search(content):
        content = AS_COMPLETED_PATTERN.sub(
            lambda m: f'{m.group(1)}# TODO: Convert as_completed to apply_async with callback\nas_completed(',
            content
        )
    return content


def convert_future_methods(content: str) -> str:
    """
    Convert Future method calls to AsyncResult equivalents.

    Args:
        content: Source code content.

    Returns:
        Content with converted Future method calls.
    """
    # future.result() -> async_result.get()
    content = FUTURE_RESULT_PATTERN.sub(
        lambda m: f'{m.group(1)}.get()',
        content
    )

    # future.done() -> async_result.ready()
    content = FUTURE_DONE_PATTERN.sub(
        lambda m: f'{m.group(1)}.ready()',
        content
    )

    # future.cancelled() -> async_result.successful() is inverse, keep as comment
    content = FUTURE_CANCELLED_PATTERN.sub(
        lambda m: f'{m.group(1)}.successful()  # Note: successful() is inverse of cancelled()',
        content
    )

    # future.cancel() -> async_result.wait(timeout=0) is not equivalent, add comment
    content = FUTURE_CANCEL_PATTERN.sub(
        lambda m: f'{m.group(1)}.wait(timeout=0)  # Note: cancel() not supported in apply_async',
        content
    )

    # future.exception() -> async_result.get() with try/except
    content = FUTURE_EXCEPTION_PATTERN.sub(
        lambda m: f'{m.group(1)}.get()  # Note: will raise exception if task failed',
        content
    )

    return content


def convert_python_file(content: str) -> str:
    """
    Apply all conversions to a Python file's content.

    Args:
        content: Original file content.

    Returns:
        Converted file content.
    """
    result = content
    result = convert_imports(result)
    result = convert_executor_instantiation(result)
    result = convert_submit_calls(result)
    result = convert_map_calls(result)
    result = convert_shutdown_calls(result)
    result = convert_as_completed(result)
    result = convert_future_methods(result)
    return result


def process_file(path: Path) -> FileResult:
    """
    Process a single Python file for conversion.

    Args:
        path: Path to the Python file.

    Returns:
        FileResult containing the processing result.
    """
    try:
        # Check file size
        if path.stat().st_size > MAX_FILE_SIZE:
            return FileResult(
                path=path,
                original='',
                converted='',
                error=f'File too large (> {MAX_FILE_SIZE} bytes)',
                changed=False
            )

        # Read file content
        content = path.read_text(encoding='utf-8')

        # Check if file contains concurrent.futures patterns
        if not any(
            'ThreadPoolExecutor' in content or
            'ProcessPoolExecutor' in content or
            'concurrent.futures' in content or
            'as_completed' in content
            for _ in [0]  # Single iteration for efficiency
        ):
            return FileResult(path=path, original=content, converted=content, changed=False)

        # Convert content
        converted = convert_python_file(content)

        return FileResult(
            path=path,
            original=content,
            converted=converted,
            changed=content != converted
        )
    except UnicodeDecodeError as e:
        return FileResult(
            path=path,
            original='',
            converted='',
            error=f'Unicode decode error: {e}',
            changed=False
        )
    except Exception as e:
        return FileResult(
            path=path,
            original='',
            converted='',
            error=f'Unexpected error: {e}',
            changed=False
        )


def process_file_wrapper(args: Tuple[Path, bool]) -> FileResult:
    """
    Wrapper for multiprocessing to process a file and optionally apply changes.

    Args:
        args: Tuple of (path, apply_flag).

    Returns:
        FileResult containing processing result.
    """
    path, apply_flag = args
    result = process_file(path)

    if apply_flag and result.changed and not result.error:
        try:
            path.write_text(result.converted, encoding='utf-8')
            print(f"✓ Converted: {path}", flush=True)
        except Exception as e:
            result.error = f'Failed to write file: {e}'

    return result


def print_diff(result: FileResult) -> None:
    """
    Print the diff for a file result.

    Args:
        result: FileResult to print diff for.
    """
    if result.error:
        print(f"✗ Error processing {result.path}: {result.error}", file=sys.stderr)
        return

    if result.changed:
        print(f"--- {result.path}")
        print(result.diff)
        print()


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description='Convert concurrent.futures patterns to multiprocessing.Pool.apply_async',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'paths',
        nargs='*',
        type=Path,
        help='Files or directories to process (default: current directory)'
    )
    parser.add_argument(
        '-a', '--apply',
        action='store_true',
        help='Apply changes in-place (default: dry-run with diff)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=WORKERS,
        help=f'Number of worker processes (default: {WORKERS})'
    )

    args = parser.parse_args()

    # Validate workers
    if args.workers < 1:
        print("Error: workers must be >= 1", file=sys.stderr)
        return 1
    if args.workers > mp.cpu_count() * 2:
        print(f"Warning: {args.workers} workers exceeds 2x CPU count ({mp.cpu_count()})",
              file=sys.stderr)

    # Collect files
    try:
        files = collect_python_files(args.paths)
    except Exception as e:
        print(f"Error collecting files: {e}", file=sys.stderr)
        return 1

    if not files:
        print("No Python files found to process.")
        return 0

    print(f"Processing {len(files)} Python file(s) with {args.workers} workers...")
    if not args.apply:
        print("Dry-run mode (use -a to apply changes)\n")

    # Prepare work items
    work_items = [(path, args.apply) for path in files]

    # Process files in parallel using imap_unordered
    results: list[FileResult] = []
    changed_count = 0
    error_count = 0

    try:
        with mp.Pool(processes=args.workers) as pool:
            for result in pool.imap_unordered(process_file_wrapper, work_items, chunksize=10):
                results.append(result)
                if result.error:
                    error_count += 1
                    print(f"✗ {result.path}: {result.error}", file=sys.stderr, flush=True)
                elif result.changed:
                    changed_count += 1
                    if not args.apply:
                        print_diff(result)
    except KeyboardInterrupt:
        print("\nInterrupted. Terminating...", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        return 1

    # Sort results by path for consistent output
    results.sort(key=lambda r: str(r.path))

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Total files processed: {len(results)}")
    print(f"  Files changed:         {changed_count}")
    print(f"  Files with errors:     {error_count}")
    if args.apply:
        print(f"  Changes applied:       ✓ (in-place)")
    else:
        print(f"  Changes applied:       ✗ (dry-run)")

    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
