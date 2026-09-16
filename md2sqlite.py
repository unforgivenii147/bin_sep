#!/data/data/com.termux/files/home/.local/bin/python
"""md2sqlite.py – Md2Sqlite utilities.

This module provides functionality for md2sqlite."""
from __future__ import annotations
from typing import Any
import re
import sqlite3
DB_NAME = 'ruff_rules.db'
MD_FILE = 'ruff.md'

def create_database() -> None:
    """create_database – create database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS ruff_rules (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            code TEXT UNIQUE,\n            name TEXT,\n            what_it_does TEXT,\n            why_it_bad TEXT,\n            example TEXT,\n            fix_safety TEXT,\n            options TEXT,\n            references_list TEXT\n        )\n    ')
    conn.commit()
    conn.close()

def parse_and_insert() -> Any:
    """parse_and_insert – parse and insert."""
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    rule_blocks = re.findall('^#\\s+(.*?)\\s+\\((.*?)\\)\\s*\\n(.*?)(?=\\n#\\s+|\\Z)', content, re.DOTALL | re.MULTILINE)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    inserted_count = 0
    for name, code, body in rule_blocks:

        def extract_section(header_title: str) -> Any:
            """extract_section – extract section.

Args:
    header_title: Description of header_title."""
            pattern = f'##\\s+{header_title}\\s*\\n(.*?)(?=\\n##\\s+|\\Z)'
            match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else None
        what_it_does = extract_section('What it does')
        why_it_bad = extract_section('Why is this bad\\??')
        example = extract_section('Example')
        fix_safety = extract_section('Fix safety')
        options = extract_section('Options')
        references = extract_section('References')
        try:
            cursor.execute('\n                INSERT OR REPLACE INTO ruff_rules\n                (code, name, what_it_does, why_it_bad, example, fix_safety, options, references_list)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ', (code.strip(), name.strip(), what_it_does, why_it_bad, example, fix_safety, options, references))
            inserted_count += 1
        except sqlite3.Error as e:
            print(f'Error inserting rule {code}: {e}')
    conn.commit()
    conn.close()
    print(f"Success! Successfully saved {inserted_count} rules into '{DB_NAME}'.")
if __name__ == '__main__':
    create_database()
    parse_and_insert()
