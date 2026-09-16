#!/data/data/com.termux/files/home/.local/bin/python
"""sort_quotes.py – Sort Quotes utilities.

This module provides functionality for sort quotes."""
from __future__ import annotations
from typing import Any
from pathlib import Path
import json
import os
import sys

def dedup_quotes(quotes: Any) -> Any:
    """dedup_quotes – dedup quotes.

Args:
    quotes: Description of quotes."""
    seen = set()
    unique = []
    for q in quotes:
        key = q['quote'].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique

def sort_quotes_by_author(path: Path | str) -> None:
    """sort_quotes_by_author – sort quotes by author.

Args:
    path: Description of path."""
    if not os.path.exists(path):
        print(f"Error: '{path}' could not be found.")
        return
    with open(path, 'r', encoding='utf-8') as f:
        try:
            quotes = json.load(f)
        except json.JSONDecodeError:
            print("Error: 'quotes.json' is empty or contains invalid formatting.")
            return
    uniques = dedup_quotes(quotes)
    uniques.sort(key=lambda item: item.get('author', '').lower())
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(uniques, f, indent=2, ensure_ascii=False)
    print('Success: Sorted')
if __name__ == '__main__':
    fn = sys.argv[1]
    sort_quotes_by_author(fn)
