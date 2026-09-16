#!/data/data/com.termux/files/home/.local/bin/python
"""rmpyc_entries.py – Rmpyc Entries utilities.

This module provides functionality for rmpyc entries."""
from __future__ import annotations
import sysconfig
from pathlib import Path

def clean_record_file(record_path: Path) -> None:
    """clean_record_file – clean record file.

Args:
    record_path: Description of record_path."""
    lines = record_path.read_text(encoding='utf-8').splitlines()
    cleaned = [line for line in lines if '.pyc' not in line]
    cleaned = [line for line in cleaned if 'licenses' not in line]
    cleaned = [line for line in cleaned if 'license.md' not in line.lower()]
    cleaned = [line for line in cleaned if 'license.txt' not in line.lower()]
    record_path.write_text('\n'.join(cleaned) + '\n', encoding='utf-8')
    print(f'{record_path.name} in {record_path.parent.name} cleaned')

def remove_pyc_entries() -> None:
    """remove_pyc_entries – remove pyc entries."""
    site_packages = Path(sysconfig.get_paths()['purelib'])
    for dist_info in site_packages.glob('*.dist-info'):
        record = dist_info / 'RECORD'
        if record.exists():
            clean_record_file(record)
if __name__ == '__main__':
    remove_pyc_entries()
    print('Removed .pyc references from all RECORD files.')
