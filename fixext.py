#!/data/data/com.termux/files/home/.local/bin/python
"""fixext.py – Fixext utilities.

This module provides functionality for fixext."""
from __future__ import annotations
import argparse
import logging
import multiprocessing as mp
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from dh import MIME2EXT, SHEBANG_MAP, get_files
LOGGER = logging.getLogger(__name__)
PROTECTED_EXTENSIONS = {'.css', '.js', '.min.js', '.min.css', '.md', '.json', '.yaml', '.yml', '.xml'}

def configure_logging(debug: bool=False) -> None:
    """configure_logging – configure logging.

Args:
    debug: Description of debug."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.WARNING, format='%(levelname)s | %(message)s')

def _mime_to_ext(mime_type: str) -> str | None:
    """_mime_to_ext –  mime to ext.

Args:
    mime_type: Description of mime_type.

Returns:
    str | None: Description of return value."""
    extensions = MIME2EXT.get(mime_type)
    if isinstance(extensions, list):
        return extensions[0] if extensions else None
    return extensions

def detect_with_pure_magic(path: Path) -> str | None:
    """detect_with_pure_magic – detect with pure magic.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    try:
        import magic
        mime = magic.Magic(mime=True)
        return _mime_to_ext(mime.from_file(str(path)))
    except Exception as exc:
        LOGGER.debug('pure-magic failed for %s: %s', path, exc)
        return None

def detect_with_python_magic(path: Path) -> str | None:
    """detect_with_python_magic – detect with python magic.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    try:
        import magic
        mime_type = magic.from_file(str(path), mime=True)
        return _mime_to_ext(mime_type)
    except Exception as exc:
        LOGGER.debug('python-magic failed for %s: %s', path, exc)
        return None

def detect_with_filetype(path: Path) -> str | None:
    """detect_with_filetype – detect with filetype.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    try:
        import filetype
        kind = filetype.guess(str(path))
        return f'.{kind.extension}' if kind else None
    except Exception as exc:
        LOGGER.debug('filetype failed for %s: %s', path, exc)
        return None

def detect_with_file_command(path: Path) -> str | None:
    """detect_with_file_command – detect with file command.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    try:
        result = subprocess.run(['file', '--brief', '--mime-type', str(path)], capture_output=True, text=True, timeout=5, check=False)
        if result.returncode == 0:
            return _mime_to_ext(result.stdout.strip())
    except Exception as exc:
        LOGGER.debug('file command failed for %s: %s', path, exc)
    return None

def detect_shebang_ext(path: Path) -> str | None:
    """detect_shebang_ext – detect shebang ext.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    try:
        with path.open('rb') as file:
            first_line = file.readline()
        if not first_line.startswith(b'#!'):
            return None
        shebang = first_line.decode('utf-8', errors='ignore').strip()
        for key, extension in SHEBANG_MAP.items():
            if key in shebang:
                return extension
    except Exception as exc:
        LOGGER.debug('shebang detection failed for %s: %s', path, exc)
    return None

def detect_extension(path: Path) -> str | None:
    """detect_extension – detect extension.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    detectors = (detect_shebang_ext, detect_with_pure_magic, detect_with_python_magic, detect_with_filetype, detect_with_file_command)
    for detector in detectors:
        extension = detector(path)
        if extension:
            if not extension.startswith('.'):
                extension = f'.{extension}'
            return extension.lower()
    return None

def get_current_extension(path: Path) -> str:
    """get_current_extension – get current extension.

Args:
    path: Description of path.

Returns:
    str: Description of return value."""
    name = path.name.lower()
    for extension in sorted(PROTECTED_EXTENSIONS, key=len, reverse=True):
        if name.endswith(extension):
            return extension
    return path.suffix.lower()

def is_protected_extension(extension: str) -> bool:
    """is_protected_extension – is protected extension.

Args:
    extension: Description of extension.

Returns:
    bool: Description of return value."""
    return extension.lower() in PROTECTED_EXTENSIONS

def rename_with_extension(path: Path, detected_ext: str) -> tuple[Path, bool]:
    """rename_with_extension – rename with extension.

Args:
    path: Description of path.
    detected_ext: Description of detected_ext.

Returns:
    tuple[Path, bool]: Description of return value."""
    new_name = path.with_suffix(detected_ext)
    if new_name == path:
        return (path, False)
    if new_name.exists():
        LOGGER.debug('Destination already exists; skipping: %s', new_name)
        return (path, False)
    try:
        path.rename(new_name)
        return (new_name, True)
    except OSError as exc:
        LOGGER.debug('Could not rename %s: %s', path, exc)
        return (path, False)

def check_file(path: Path, auto_fix: bool=False) -> tuple[Path, bool, str | None, str | None]:
    """check_file – check file.

Args:
    path: Description of path.
    auto_fix: Description of auto_fix.

Returns:
    tuple[Path, bool, str | None, str | None]: Description of return value."""
    if not path.is_file():
        return (path, False, None, None)
    current_ext = get_current_extension(path)
    detected_ext = detect_extension(path)
    if not detected_ext:
        return (path, False, current_ext or None, None)
    if current_ext == detected_ext:
        return (path, False, current_ext or None, detected_ext)
    if is_protected_extension(current_ext) and detected_ext == '.txt':
        LOGGER.debug('Protected extension; skipping %s', path)
        return (path, False, current_ext, detected_ext)
    if not auto_fix:
        return (path, True, current_ext or None, detected_ext)
    renamed_path, renamed = rename_with_extension(path, detected_ext)
    return (renamed_path, renamed, current_ext or None, detected_ext)

def collect_files(inputs: Iterable[Path]) -> list[Path]:
    """collect_files – collect files.

Args:
    inputs: Description of inputs.

Returns:
    list[Path]: Description of return value."""
    files: list[Path] = []
    for input_path in inputs:
        input_path = input_path.expanduser()
        if input_path.is_file():
            files.append(input_path)
        elif input_path.is_dir():
            files.extend((path for path in input_path.rglob('*') if path.is_file()))
        else:
            print(f'Warning: not found or unsupported: {input_path}', file=sys.stderr)
    return list(dict.fromkeys(files))

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Detect and optionally fix file extension mismatches.')
    parser.add_argument('inputs', nargs='*', type=Path, help='Files or directories to scan. Defaults to the current directory.')
    parser.add_argument('-a', '--auto-fix', action='store_true', help='Rename files to their detected extensions.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    args = parser.parse_args()
    configure_logging(args.debug)
    cwd = Path.cwd()
    files = collect_files(args.inputs) or get_files(cwd)
    if not files:
        print('No files found.', file=sys.stderr)
        return
    mismatches = 0
    fixed = 0
    with mp.Pool(processes=8) as pool:
        jobs = [pool.apply_async(check_file, (path, args.auto_fix)) for path in files]
        for path, job in zip(files, jobs, strict=False):
            try:
                result_path, is_mismatch, old_ext, new_ext = job.get()
                if args.auto_fix:
                    if is_mismatch and result_path != path:
                        fixed += 1
                        print(f'renamed: {path} -> {result_path}')
                elif is_mismatch:
                    mismatches += 1
                    print(f"{path}: {old_ext or 'none'} -> {new_ext}")
            except Exception as exc:
                LOGGER.debug('Error processing %s: %s', path, exc)
                print(f'{path} -> error: {exc}', file=sys.stderr)
    if not args.auto_fix:
        print()
        print(f'Total files scanned: {len(files)}')
        print(f'Mismatches found: {mismatches}')
    elif fixed:
        print()
        print(f'Files fixed: {fixed}')
if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
