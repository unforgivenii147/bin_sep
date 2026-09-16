#!/data/data/com.termux/files/home/.local/bin/python
"""showcolor.py – Showcolor utilities.

This module provides functionality for showcolor."""
from __future__ import annotations
from secrets import randbelow

def show_random_color() -> None:
    """show_random_color – show random color."""
    red = randbelow(256)
    green = randbelow(256)
    blue = randbelow(256)
    print(f'\x1b[48;2;{red};{green};{blue}m        \x1b[0m {red!s} {green!s} {blue!s}')
if __name__ == '__main__':
    for _i in range(1, randbelow(1000)):
        show_random_color()
