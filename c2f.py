#!/data/data/com.termux/files/home/.local/bin/python
"""c2f.py – C2F utilities.

This module provides functionality for c2f."""
from __future__ import annotations
import sys
if __name__ == '__main__':
    celsius = int(sys.argv[1])
    farenheit = celsius * 9 / 5 + 32
    print(f'{farenheit:.2f}')
