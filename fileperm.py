#!/data/data/com.termux/files/home/.local/bin/python
"""fileperm.py – Fileperm utilities.

This module provides functionality for fileperm."""
from __future__ import annotations
from typing import Any, Iterator
from pathlib import Path
import argparse
import os
import stat
from tqdm import tqdm
SKIP_DIRS = {'.git', '.ruff_cache', '__pycache__'}

def should_skip_dir(dirname: Path | str) -> bool:
    """should_skip_dir – should skip dir.

Args:
    dirname: Description of dirname."""
    return dirname in SKIP_DIRS

def walk_files(root_path: str='.') -> Iterator[Any]:
    """walk_files – walk files.

Args:
    root_path: Description of root_path."""
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if os.path.islink(path):
                continue
            yield path

def has_shebang(path: Path | str) -> bool:
    """has_shebang – has shebang.

Args:
    path: Description of path."""
    try:
        with open(path, 'rb') as f:
            first_line = f.readline()
            return first_line.startswith(b'#!')
    except OSError:
        return False

def is_executable(path: Path | str) -> bool:
    """is_executable – is executable.

Args:
    path: Description of path."""
    try:
        return os.access(path, os.X_OK)
    except:
        return False

def get_current_mode(path: Path | str) -> Any:
    """get_current_mode – get current mode.

Args:
    path: Description of path."""
    try:
        return stat.S_IMODE(os.stat(path).st_mode)
    except:
        return None

def determine_target_mode(path: Path | str) -> int:
    """determine_target_mode – determine target mode.

Args:
    path: Description of path."""
    if is_executable(path):
        return None
    parent_dir = os.path.basename(os.path.dirname(path))
    if has_shebang(path) or parent_dir == 'bin':
        return 493
    return 420

def analyze_file(path: Path | str) -> Any:
    """analyze_file – analyze file.

Args:
    path: Description of path."""
    target_mode = determine_target_mode(path)
    if target_mode is None:
        return ('skip_executable', path, None, None)
    current_mode = get_current_mode(path)
    if current_mode is None:
        return ('error', path, None, None)
    if current_mode != target_mode:
        return ('change', path, current_mode, target_mode)
    else:
        return ('skip_correct', path, current_mode, target_mode)

def process_file(path: Path | str, target_mode: Any, dry_run: bool=False) -> bool:
    """process_file – process file.

Args:
    path: Description of path.
    target_mode: Description of target_mode.
    dry_run: Description of dry_run."""
    if dry_run:
        return True
    try:
        os.chmod(path, target_mode)
        return True
    except Exception as e:
        print(f'Error: {path}: {e}')
        return False

def scan_and_report(root_path: str='.') -> Any:
    """scan_and_report – scan and report.

Args:
    root_path: Description of root_path."""
    stats = {'total': 0, 'skip_executable': [], 'skip_correct': [], 'make_executable': [], 'set_standard': [], 'errors': []}
    print('Scanning files...')
    file_generator = walk_files(root_path)
    for path in tqdm(file_generator, desc='Analyzing', unit='files'):
        stats['total'] += 1
        status, path, current, target = analyze_file(path)
        if status == 'skip_executable':
            stats['skip_executable'].append(path)
        elif status == 'skip_correct':
            stats['skip_correct'].append(path)
        elif status == 'change':
            if target == 493:
                stats['make_executable'].append((path, current, target))
            else:
                stats['set_standard'].append((path, current, target))
        elif status == 'error':
            stats['errors'].append(path)
    return stats

def apply_changes(stats: Any, dry_run: bool=False) -> Any:
    """apply_changes – apply changes.

Args:
    stats: Description of stats.
    dry_run: Description of dry_run."""
    changes = stats['make_executable'] + stats['set_standard']
    if not changes:
        print('\nNo changes needed!')
        return
    print(f'\nApplying changes to {len(changes)} files...')
    success = 0
    failed = 0
    for path, _current, target in tqdm(changes, desc='Changing permissions', unit='files'):
        if process_file(path, target, dry_run):
            success += 1
        else:
            failed += 1
    return (success, failed)

def print_report(stats: Any, success: bool | None=None, failed: bool | None=None) -> None:
    """print_report – print report.

Args:
    stats: Description of stats.
    success: Description of success.
    failed: Description of failed."""
    print(f"\n{'=' * 40}")
    print('Scan Results:')
    print(f"  Total files scanned: {stats['total']}")
    print(f"  ⊘ Already executable (skipped): {len(stats['skip_executable'])}")
    print(f"  ✓ Already correct: {len(stats['skip_correct'])}")
    print(f"  → Will make executable (+x): {len(stats['make_executable'])}")
    print(f"  → Will set to standard (0644): {len(stats['set_standard'])}")
    if stats['errors']:
        print(f"  ✗ Errors during analysis: {len(stats['errors'])}")
    if success is not None:
        print('\nResults:')
        print(f'  ✓ Changes successful: {success}')
        if failed:
            print(f'  ✗ Changes failed: {failed}')
    print(f"{'=' * 40}")

def show_examples(stats: Any, num: int=5) -> None:
    """show_examples – show examples.

Args:
    stats: Description of stats.
    num: Description of num."""
    if stats['make_executable']:
        print('\nExamples of files to make executable (+x):')
        for path, current, target in stats['make_executable'][:num]:
            print(f'  {oct(current)} -> {oct(target)}  {path}')
        if len(stats['make_executable']) > num:
            print(f"  ... and {len(stats['make_executable']) - num} more")
    if stats['set_standard']:
        print('\nExamples of files to set to 0644:')
        for path, current, target in stats['set_standard'][:num]:
            print(f'  {oct(current)} -> {oct(target)}  {path}')
        if len(stats['set_standard']) > num:
            print(f"  ... and {len(stats['set_standard']) - num} more")
    if stats['skip_executable']:
        print('\nExamples of skipped files (already executable):')
        for path in stats['skip_executable'][:num]:
            print(f'  {path}')
        if len(stats['skip_executable']) > num:
            print(f"  ... and {len(stats['skip_executable']) - num} more")

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Fix file permissions with smart rules using generator-based scanning', formatter_class=argparse.RawDescriptionHelpFormatter, epilog=f"\nRules:\n  - Files that are already executable: no changes\n  - Files with shebang (#!) or in 'bin' directory: set to 0755\n  - All other files: set to 0644\n\nSkipped directories: {', '.join(sorted(SKIP_DIRS))}\n\nExamples:\n  %(prog)s                    # Process current directory\n  %(prog)s /path/to/project   # Process specific path\n  %(prog)s . --dry-run        # Preview changes\n  %(prog)s . --show-examples  # Show examples of changes\n        ")
    parser.add_argument('path', nargs='?', default='.', help='Root path to start from (default: current directory)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually changing permissions')
    parser.add_argument('--show-examples', action='store_true', help='Show example files that would be changed')
    args = parser.parse_args()
    print(f"Skip directories: {', '.join(sorted(SKIP_DIRS))}")
    if args.dry_run:
        print('DRY RUN - No changes will be made\n')
    stats = scan_and_report(args.path)
    print_report(stats)
    if args.show_examples:
        show_examples(stats)
    if not args.dry_run:
        success, failed = apply_changes(stats, dry_run=False)
        if success is not None:
            print(f"\n{'=' * 40}")
            print('Final Results:')
            print(f'  ✓ Changes applied successfully: {success}')
            if failed:
                print(f'  ✗ Failed changes: {failed}')
            print(f"{'=' * 40}")
    else:
        total_changes = len(stats['make_executable']) + len(stats['set_standard'])
        if total_changes > 0:
            print(f'\nWould apply {total_changes} changes')
            if args.show_examples:
                show_examples(stats)
if __name__ == '__main__':
    raise SystemExit(main())
