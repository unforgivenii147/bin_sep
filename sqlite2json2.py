#!/data/data/com.termux/files/home/.local/bin/python
"""sqlite2json2.py – Sqlite2Json2 utilities.

This module provides functionality for sqlite2json2."""
from __future__ import annotations
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

def json_safe(value: Any) -> Any:
    """json_safe – json safe.

Args:
    value: Description of value.

Returns:
    Any: Description of return value."""
    if isinstance(value, bytes):
        return value.hex()
    return value

def sqlite_to_json(input_path: Path) -> Path:
    """sqlite_to_json – sqlite to json.

Args:
    input_path: Description of input_path.

Returns:
    Path: Description of return value."""
    output_path = input_path.with_suffix('.json')
    with sqlite3.connect(input_path) as connection:
        connection.row_factory = sqlite3.Row
        tables = connection.execute("\n            SELECT name\n            FROM sqlite_master\n            WHERE type = 'table'\n              AND name NOT LIKE 'sqlite_%'\n            ORDER BY name\n            ").fetchall()
        database_data: dict[str, list[dict[str, Any]]] = {}
        for table_row in tables:
            table_name = table_row['name']
            rows = connection.execute(f'SELECT * FROM "{table_name.replace(chr(34), chr(34) * 2)}"').fetchall()
            database_data[table_name] = [{column_name: json_safe(row[column_name]) for column_name in row} for row in rows]
    output_path.write_text(json.dumps(database_data, indent=2, ensure_ascii=False), encoding='utf-8')
    return output_path

def main() -> None:
    """main – main."""
    if len(sys.argv) != 2:
        print(f'Usage: {Path(sys.argv[0]).name} DATABASE_FILE')
        sys.exit(1)
    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f'Error: database file not found: {input_path}', file=sys.stderr)
        sys.exit(1)
    try:
        output_path = sqlite_to_json(input_path)
    except sqlite3.Error as error:
        print(f'SQLite error: {error}', file=sys.stderr)
        sys.exit(1)
    print(f'Converted {input_path} to {output_path}')
if __name__ == '__main__':
    main()
