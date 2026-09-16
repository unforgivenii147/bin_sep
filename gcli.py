#!/data/data/com.termux/files/home/.local/bin/python
"""gcli.py – Gcli utilities.

This module provides functionality for gcli."""
from __future__ import annotations
import sys
from googlesearch import search
if __name__ == '__main__':
    tts = sys.argv[1]
    for result in search(tts):
        print(result)
