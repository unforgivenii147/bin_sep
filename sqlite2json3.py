#!/data/data/com.termux/files/home/.local/bin/python
import sqlite3
import json
import sys
from pathlib import Path


def convert_sqlite_to_json(db_path: Path):
    # TODO:
    # 1. Connect to the sqlite3 database
    # 2. Query 'sqlite_master' to find all table names
    # 3. For each table:
    #    a. Fetch all rows
    #    b. Convert rows to a list of dictionaries (using cursor.description for keys)
    # 4. Save the final dictionary {table_name: data} to the .json output path
    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <database.db>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".json")

    try:
        convert_sqlite_to_json(input_path)
        print(f"Successfully converted {input_path} to {output_path}")
    except Exception as e:
        print(f"Error: {e}")
