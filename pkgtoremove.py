#!/data/data/com.termux/files/home/.local/bin/python
"""pkgtoremove.py – Pkgtoremove utilities.

This module provides functionality for pkgtoremove."""
from __future__ import annotations
from typing import Any
import operator
import re
import subprocess
from pathlib import Path

def get_installed_packages() -> Any:
    """get_installed_packages – get installed packages."""
    installed_packages = []
    result = subprocess.run(['dpkg-query', '-W', '-f=${binary:Package} ${Installed-Size}\n'], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        pkg, size = line.split()
        installed_packages.append((pkg, int(size)))
    return installed_packages

def get_bash_history() -> Any:
    """get_bash_history – get bash history."""
    history_file = Path('~/.bash_history').expanduser()
    if not Path(history_file).exists():
        return []
    with Path(history_file).open(encoding='utf-8') as f:
        return f.read().splitlines()

def get_used_packages(history: Any, installed_packages: Any) -> Any:
    """get_used_packages – get used packages.

Args:
    history: Description of history.
    installed_packages: Description of installed_packages."""
    used_packages = set()
    package_names = dict(installed_packages)
    for line in history:
        for pkg in package_names:
            if re.search(f'\\b{pkg}\\b', line):
                used_packages.add(pkg)
    return used_packages

def exclude_build_packages(installed_packages: Any) -> Any:
    """exclude_build_packages – exclude build packages.

Args:
    installed_packages: Description of installed_packages."""
    build_essential_packages = {'build-essential', 'gcc', 'make', 'libc6-dev', 'pkg-config', 'libtool', 'dpkg-dev', 'autoconf', 'automake'}
    return [(pkg, size) for pkg, size in installed_packages if pkg not in build_essential_packages]

def suggest_unused_packages(installed_packages: Any, used_packages: Any, top_n: int=200) -> Any:
    """suggest_unused_packages – suggest unused packages.

Args:
    installed_packages: Description of installed_packages.
    used_packages: Description of used_packages.
    top_n: Description of top_n."""
    unused_packages = [pkg for pkg in installed_packages if pkg[0] not in used_packages]
    unused_packages = exclude_build_packages(unused_packages)
    unused_packages.sort(key=operator.itemgetter(1), reverse=True)
    return unused_packages[:top_n]

def main() -> None:
    """main – main."""
    installed_packages = get_installed_packages()
    history = get_bash_history()
    used_packages = get_used_packages(history, installed_packages)
    suggestions = suggest_unused_packages(installed_packages, used_packages, top_n=100)
    print('Top unused packages (sorted by size):')
    for pkg, size in suggestions:
        if 'python' not in str(pkg) and 'l8b' not in str(pkg) and ('static' not in str(pkg)):
            print(f'{pkg}: {size / 1024} MB')
if __name__ == '__main__':
    raise SystemExit(main())
