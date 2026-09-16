#!/data/data/com.termux/files/home/.local/bin/python
"""random_quote.py – Random Quote utilities.

This module provides functionality for random quote."""
from __future__ import annotations
import json
import os
import random
from shutil import get_terminal_size
FILE_NAME = '/sdcard/data/quotes/quotes.json'

def display_random_quote() -> None:
    """display_random_quote – display random quote."""
    if not os.path.exists(FILE_NAME):
        return
    with open(FILE_NAME, 'r', encoding='utf-8') as f:
        try:
            quotes = json.load(f)
        except json.JSONDecodeError:
            return
    if not quotes:
        return
    selected = random.choice(quotes)
    quote_text = selected.get('quote', 'No quote content.')
    author_text = selected.get('author', 'Unknown Author')
    N = get_terminal_size()[0]
    print('\n' + '─' * N)
    print(f'\x1b[5;96m"{quote_text}"\x1b[0m')
    print(f'\x1b[5;94m  — {author_text}\x1b[0m')
    print('─' * N + '\n')
if __name__ == '__main__':
    display_random_quote()
