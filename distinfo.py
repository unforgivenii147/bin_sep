#!/data/data/com.termux/files/home/.local/bin/python
"""distinfo.py – Distinfo utilities.

This module provides functionality for distinfo."""
from __future__ import annotations
from typing import Any
import contextlib
import re
import site
from collections import defaultdict
from pathlib import Path

def get_site_packages_dirs() -> Any:
    """get_site_packages_dirs – get site packages dirs."""
    dirs = []
    with contextlib.suppress(Exception):
        dirs.extend(site.getsitepackages())
    dirs.append(site.getusersitepackages())
    return list(dict.fromkeys(dirs))

def parse_pkg_info(dirname: Path | str) -> Any:
    """parse_pkg_info – parse pkg info.

Args:
    dirname: Description of dirname."""
    m = re.match('(.+)-(\\d+.*?)(\\.dist-info|\\.egg-info)$', dirname)
    if m:
        return (m.group(1).lower(), m.group(2))
    return (None, None)

def find_multiple_versions() -> None:
    """find_multiple_versions – find multiple versions."""
    pkg_versions = defaultdict(set)
    for sp_dir in get_site_packages_dirs():
        sp_path = Path(sp_dir)
        if not sp_path.is_dir():
            continue
        for entry in sp_path.iterdir():
            if entry.name.endswith(('.dist-info', '.egg-info')):
                name, version = parse_pkg_info(entry.name)
                if name:
                    pkg_versions[name].add(version)
    for pkg, versions in sorted(pkg_versions.items()):
        if len(versions) > 1:
            print(f'\nPackage: {pkg}')
            for v in sorted(versions):
                print(f'  - Version: {v}')
    print('\nDone.')
if __name__ == '__main__':
    find_multiple_versions()
