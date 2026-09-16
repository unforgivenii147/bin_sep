#!/data/data/com.termux/files/home/.local/bin/python
"""pyfslint.py – Pyfslint utilities.

This module provides functionality for pyfslint."""
from __future__ import annotations
import argparse
import contextlib
import grp
import hashlib
import os
import pwd
import re
import stat
import subprocess
import sys
from collections import defaultdict
from collections.abc import Generator
from pathlib import Path
RESET = '\x1b[0m'
BOLD = '\x1b[1m'
RED = '\x1b[31m'
YELLOW = '\x1b[33m'
CYAN = '\x1b[36m'
GREEN = '\x1b[32m'
GREY = '\x1b[90m'

def _c(color: str, text: str) -> str:
    """_c –  c.

Args:
    color: Description of color.
    text: Description of text.

Returns:
    str: Description of return value."""
    if sys.stdout.isatty():
        return f'{color}{text}{RESET}'
    return text

def header(title: str) -> None:
    """header – header.

Args:
    title: Description of title."""
    width = 70
    print('\n' + _c(BOLD + CYAN, '━' * width))
    print(_c(BOLD + CYAN, f'  {title}'))
    print(_c(BOLD + CYAN, '━' * width))

def found(path: str | Path, note: str='') -> None:
    """found – found.

Args:
    path: Description of path.
    note: Description of note."""
    note_str = f'  {_c(GREY, note)}' if note else ''
    print(f'  {_c(YELLOW, str(path))}{note_str}')

def ok(msg: str) -> None:
    """ok – ok.

Args:
    msg: Description of msg."""
    print(_c(GREEN, f'  ✔  {msg}'))

def warn(msg: str) -> None:
    """warn – warn.

Args:
    msg: Description of msg."""
    print(_c(RED, f'  ✘  {msg}'), file=sys.stderr)

def walk(roots: list[Path], *, follow_symlinks: bool=False, yield_dirs: bool=True, yield_files: bool=True) -> Generator[Path, None, None]:
    """walk – walk.

Args:
    roots: Description of roots.
    follow_symlinks: Description of follow_symlinks.
    yield_dirs: Description of yield_dirs.
    yield_files: Description of yield_files.

Returns:
    Generator[Path, None, None]: Description of return value."""
    for root in roots:
        root = root.resolve() if follow_symlinks else root
        for dirpath, _dirnames, filenames in os.walk(root, followlinks=follow_symlinks, onerror=_walk_err):
            dp = Path(dirpath)
            if yield_dirs:
                yield dp
            if yield_files:
                for fn in filenames:
                    yield (dp / fn)

def _walk_err(exc: OSError) -> None:
    """_walk_err –  walk err.

Args:
    exc: Description of exc."""
    warn(f'walk error: {exc}')
CHUNK = 65536

def _file_hash(path: Path) -> str | None:
    """_file_hash –  file hash.

Args:
    path: Description of path.

Returns:
    str | None: Description of return value."""
    h = hashlib.sha256()
    try:
        with path.open('rb') as fh:
            while (chunk := fh.read(CHUNK)):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None

def findup(roots: list[Path]) -> int:
    """findup – findup.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findup — Duplicate Files')
    size_map: dict[int, list[Path]] = defaultdict(list)
    for p in walk(roots, yield_dirs=False):
        if p.is_symlink():
            continue
        with contextlib.suppress(OSError):
            size_map[p.stat().st_size].append(p)
    groups: dict[str, list[Path]] = defaultdict(list)
    for size, paths in size_map.items():
        if size == 0 or len(paths) < 2:
            continue
        for p in paths:
            h = _file_hash(p)
            if h:
                groups[h].append(p)
    total = 0
    for digest, paths in sorted(groups.items()):
        if len(paths) < 2:
            continue
        size = paths[0].stat().st_size
        print(f"\n  {_c(BOLD, 'Hash:')} {digest[:16]}…  {_c(GREY, f'({size:,} bytes × {len(paths)})')}")
        for p in paths:
            found(p)
        total += len(paths) - 1
    if total == 0:
        ok('No duplicate files found.')
    else:
        print(f"\n  {_c(RED, f'{total} redundant copy/copies found.r')}")
    return total
_NL_RULES: list[tuple[str, re.Pattern[str]]] = [('leading whitespace', re.compile('^\\s')), ('trailing whitespace', re.compile('\\s$')), ('consecutive spaces', re.compile('  ')), ('control character', re.compile('[\\x00-\\x1f\\x7f]')), ('shell-special character', re.compile('\\[\\;\\`\\$\\!\\&\\|\\<\\>\\\\\\]')), ('mixed case (CamelCase)', re.compile('(?<=[a-z])(?=[A-Z])')), ('starts with hyphen', re.compile('^-')), ('trailing dot', re.compile('\\.$'))]

def findnl(roots: list[Path]) -> int:
    """findnl – findnl.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findnl — Name Lint')
    total = 0
    for p in walk(roots):
        name = p.name
        if not name:
            continue
        issues = [label for label, rx in _NL_RULES if rx.search(name)]
        if issues:
            found(p, ' | '.join(issues))
            total += 1
    if total == 0:
        ok('All filenames look clean.')
    return total

def findu8(roots: list[Path]) -> int:
    """findu8 – findu8.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findu8 — Non-UTF-8 Filenames')
    total = 0
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root, onerror=_walk_err):
            all_names = dirnames + filenames
            for raw in all_names:
                try:
                    raw.encode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    found(Path(dirpath) / raw, 'not valid UTF-8')
                    total += 1
    if total == 0:
        ok('All filenames are valid UTF-8.')
    return total

def _symlink_is_cyclic(path: Path, visited: set[Path] | None=None) -> bool:
    """_symlink_is_cyclic –  symlink is cyclic.

Args:
    path: Description of path.
    visited: Description of visited.

Returns:
    bool: Description of return value."""
    if visited is None:
        visited = set()
    try:
        real = path.resolve(strict=False)
    except OSError:
        return False
    if real in visited:
        return True
    visited.add(real)
    if real.is_symlink():
        return _symlink_is_cyclic(real, visited)
    return False

def findbl(roots: list[Path]) -> int:
    """findbl – findbl.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findbl — Bad Symlinks')
    total = 0
    for p in walk(roots, yield_files=True, yield_dirs=True):
        if not p.is_symlink():
            continue
        target = Path(os.readlink(p))
        if not target.is_absolute():
            target = p.parent / target
        if _symlink_is_cyclic(p):
            found(p, f'cyclic → {os.readlink(p)}')
            total += 1
        elif not target.exists():
            found(p, f'dangling → {os.readlink(p)}')
            total += 1
    if total == 0:
        ok('No bad symlinks found.')
    return total

def findem(roots: list[Path]) -> int:
    """findem – findem.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findem — Empty Directories')
    total = 0
    all_dirs: list[Path] = []
    for p in walk(roots, yield_files=False, yield_dirs=True):
        all_dirs.append(p)
    all_dirs.sort(key=lambda p: len(p.parts), reverse=True)
    reported: set[Path] = set()
    for d in all_dirs:
        if d in reported:
            continue
        try:
            entries = list(d.iterdir())
        except PermissionError:
            continue
        if len(entries) == 0:
            found(d)
            reported.add(d)
            total += 1
    if total == 0:
        ok('No empty directories found.')
    return total

def _valid_uids() -> set[int]:
    """_valid_uids –  valid uids.

Returns:
    set[int]: Description of return value."""
    return {entry.pw_uid for entry in pwd.getpwall()}

def _valid_gids() -> set[int]:
    """_valid_gids –  valid gids.

Returns:
    set[int]: Description of return value."""
    return {entry.gr_gid for entry in grp.getgrall()}

def findid(roots: list[Path]) -> int:
    """findid – findid.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findid — Bad UID/GID Ownership')
    valid_uids = _valid_uids()
    valid_gids = _valid_gids()
    total = 0
    for p in walk(roots):
        try:
            st = p.lstat()
        except OSError:
            continue
        issues = []
        if st.st_uid not in valid_uids:
            issues.append(f'unknown uid={st.st_uid}')
        if st.st_gid not in valid_gids:
            issues.append(f'unknown gid={st.st_gid}')
        if issues:
            found(p, ' | '.join(issues))
            total += 1
    if total == 0:
        ok('All files have valid UID/GID.')
    return total
ELF_MAGIC = b'\x7fELF'

def _is_elf(path: Path) -> bool:
    """_is_elf –  is elf.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    try:
        with path.open('rb') as fh:
            return fh.read(4) == ELF_MAGIC
    except OSError:
        return False

def _has_debug_symbols(path: Path) -> bool:
    """_has_debug_symbols –  has debug symbols.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    try:
        result = subprocess.run(['readelf', '--sections', '--wide', str(path)], capture_output=True, text=True, timeout=10)
        output = result.stdout
        return '.symtab' in output or '.debug_info' in output
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        data = path.read_bytes()
        return b'.symtab' in data or b'.debug_info' in data
    except OSError:
        return False

def findns(roots: list[Path]) -> int:
    """findns – findns.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findns — Non-Stripped Binaries')
    total = 0
    for p in walk(roots, yield_dirs=False):
        if p.is_symlink():
            continue
        if not _is_elf(p):
            continue
        if _has_debug_symbols(p):
            try:
                size_kb = p.stat().st_size // 1024
            except OSError:
                size_kb = 0
            found(p, f'{size_kb:,} KB, has debug symbols')
            total += 1
    if total == 0:
        ok('No non-stripped binaries found.')
    return total

def findsn(_roots: list[Path] | None=None) -> int:
    """findsn – findsn.

Args:
    _roots: Description of _roots.

Returns:
    int: Description of return value."""
    header('findsn — Shadowed PATH Executables')
    path_env = os.environ.get('PATH', '')
    path_dirs = [Path(d) for d in path_env.split(os.pathsep) if d]
    seen: dict[str, list[Path]] = defaultdict(list)
    for d in path_dirs:
        if not d.is_dir():
            continue
        try:
            for entry in d.iterdir():
                if entry.is_file() and os.access(entry, os.X_OK):
                    seen[entry.name].append(entry)
        except PermissionError:
            pass
    total = 0
    for name, paths in sorted(seen.items()):
        if len(paths) < 2:
            continue
        print(f'\n  {_c(BOLD, name)}')
        for i, p in enumerate(paths):
            label = 'active' if i == 0 else 'shadowed'
            color = GREEN if i == 0 else RED
            print(f'    {_c(color, label):<20} {p}')
        total += len(paths) - 1
    if total == 0:
        ok('No shadowed PATH executables found.')
    return total
_TF_PATTERNS: list[re.Pattern[str]] = [re.compile('~$'), re.compile('^#.*#$'), re.compile('\\.bak$', re.IGNORECASE), re.compile('\\.tmp$', re.IGNORECASE), re.compile('\\.temp$', re.IGNORECASE), re.compile('\\.swp$', re.IGNORECASE), re.compile('\\.swo$', re.IGNORECASE), re.compile('^\\.DS_Store$'), re.compile('^Thumbs\\.db$', re.IGNORECASE), re.compile('^desktop\\.ini$', re.IGNORECASE), re.compile('\\.orig$', re.IGNORECASE), re.compile('\\.rej$', re.IGNORECASE), re.compile('core\\.\\d+$'), re.compile('^core$'), re.compile('\\.log$', re.IGNORECASE), re.compile('\\.pid$', re.IGNORECASE), re.compile('__pycache__'), re.compile('\\.pyc$'), re.compile('\\.pyo$'), re.compile('node_modules'), re.compile('\\.class$'), re.compile('\\.o$'), re.compile('\\.a$')]

def findtf(roots: list[Path]) -> int:
    """findtf – findtf.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findtf — Temporary / Junk Files')
    total = 0
    for p in walk(roots):
        name = p.name
        for rx in _TF_PATTERNS:
            if rx.search(name):
                found(p, f'matches pattern: {rx.pattern!r}')
                total += 1
                break
    if total == 0:
        ok('No temporary files found.')
    return total

def findwd(roots: list[Path]) -> int:
    """findwd – findwd.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findwd — World-Writable Items')
    total = 0
    for p in walk(roots):
        try:
            mode = p.lstat().st_mode
        except OSError:
            continue
        if mode & stat.S_IWOTH:
            kind = 'dir' if stat.S_ISDIR(mode) else 'file'
            perms = oct(stat.S_IMODE(mode))
            found(p, f'{kind}, mode={perms}')
            total += 1
    if total == 0:
        ok('No world-writable items found.')
    return total
_RS_RE = re.compile('  |^\\s|\\s$|\\t')

def findrs(roots: list[Path]) -> int:
    """findrs – findrs.

Args:
    roots: Description of roots.

Returns:
    int: Description of return value."""
    header('findrs — Redundant Whitespace in Filenames')
    total = 0
    for p in walk(roots):
        if _RS_RE.search(p.name):
            visible = repr(p.name)
            found(p, f'name repr: {visible}')
            total += 1
    if total == 0:
        ok('No redundant whitespace in filenames found.')
    return total
ALL_CHECKS: dict[str, tuple[str, callable]] = {'findup': ('Duplicate files', findup), 'findnl': ('Name lint', findnl), 'findu8': ('Non-UTF-8 filenames', findu8), 'findbl': ('Bad symlinks', findbl), 'findem': ('Empty directories', findem), 'findid': ('Bad UID/GID ownership', findid), 'findns': ('Non-stripped binaries', findns), 'findsn': ('Shadowed PATH executables', findsn), 'findtf': ('Temporary / junk files', findtf), 'findwd': ('World-writable items', findwd), 'findrs': ('Redundant whitespace names', findrs)}

def build_parser() -> argparse.ArgumentParser:
    """build_parser – build parser.

Returns:
    argparse.ArgumentParser: Description of return value."""
    p = argparse.ArgumentParser(prog='fslint', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('paths', nargs='*', type=Path, default=[Path.cwd()], metavar='PATH', help='Directory/directories to scan (default: current directory)')
    p.add_argument('--all', '-a', action='store_true', dest='run_all', help='Run all checks (default when no check flag is given)')
    p.add_argument('--summary', '-s', action='store_true', help='Print a one-line summary table at the end')
    group = p.add_argument_group('checks')
    for flag, (desc, _fn) in ALL_CHECKS.items():
        group.add_argument(f'--{flag}', action='store_true', default=False, help=desc)
    return p

def print_summary(results: dict[str, int]) -> None:
    """print_summary – print summary.

Args:
    results: Description of results."""
    width = 42
    print('\n' + _c(BOLD, '┌' + '─' * width + '┐'))
    print(_c(BOLD, f"│{'SUMMARY':^{width}}│"))
    print(_c(BOLD, '├' + '─' * 28 + '┬' + '─' * (width - 29) + '┤'))
    for flag, count in results.items():
        desc = ALL_CHECKS[flag][0]
        color = RED if count > 0 else GREEN
        count_str = _c(color, str(count).rjust(6))
        print(f'│ {_c(BOLD, flag):<18} {desc:<22} │ {count_str} │')
    print(_c(BOLD, '└' + '─' * 28 + '┴' + '─' * (width - 29) + '┘'))

def main(argv: list[str] | None=None) -> int:
    """main – main.

Args:
    argv: Description of argv.

Returns:
    int: Description of return value."""
    parser = build_parser()
    args = parser.parse_args(argv)
    roots: list[Path] = []
    for p in args.paths:
        if not p.exists():
            warn(f'Path does not exist: {p}')
            continue
        if not p.is_dir():
            warn(f'Not a directory: {p}')
            continue
        roots.append(p.resolve())
    if not roots:
        if not args.findsn:
            warn('No valid paths to scan.')
            return 1
        roots = [Path.cwd()]
    requested = [flag for flag in ALL_CHECKS if getattr(args, flag, False)]
    if args.run_all or not requested:
        requested = list(ALL_CHECKS.keys())
    print(_c(BOLD + CYAN, '\nFSLint — Filesystem Lint Tool'))
    print(_c(GREY, f"Scanning: {', '.join((str(r) for r in roots))}"))
    print(_c(GREY, f"Checks:   {', '.join(requested)}"))
    results: dict[str, int] = {}
    exit_code = 0
    for flag in requested:
        _desc, fn = ALL_CHECKS[flag]
        try:
            count = fn(roots) if flag != 'findsn' else fn()
        except KeyboardInterrupt:
            print('\nInterrupted.', file=sys.stderr)
            return 130
        except Exception as exc:
            warn(f'{flag} failed: {exc}')
            count = -1
        results[flag] = count
        if count > 0:
            exit_code = 1
    if args.summary or len(requested) > 1:
        print_summary(results)
    return exit_code
if __name__ == '__main__':
    raise SystemExit(main())
