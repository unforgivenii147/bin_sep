#!/data/data/com.termux/files/home/.local/bin/python
"""ww.py – Ww utilities.

This module provides functionality for ww."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
if __name__ == '__main__':
    target_dir = Path.cwd().resolve()
    os.chdir(target_dir.parent)
    subprocess.run(['wheel', 'pack', str(target_dir), '-d', '/sdcard/whl'], check=False)
