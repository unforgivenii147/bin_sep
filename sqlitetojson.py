#!/data/data/com.termux/files/home/.local/bin/python
import sqlite3
import json
import sys
from pathlib import Path


def convert_sqlite_to_json(db_path: Path):
    # Define the output path based on the input filename
    output_path = db_path.with_suffix(".json")

    # Use a context manager to ensure the connection closes automatically
    with sqlite3.connect(db_path) as conn:
        # row_factory = sqlite3.Row allows us to access columns by name
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query the sqlite_master table to find all user-defined tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]

        db_content = {}

        for table_name in tables:
            # Fetch all data from the current table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Convert sqlite3.Row objects into standard Python dictionaries
            # This creates a list of dicts: [{"col1": val1, "col2": val2}, ...]
            db_content[table_name] = [dict(row) for row in rows]

    # Write the aggregated data to the JSON file
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(db_content, f, indent=4)


if __name__ == "__main__":
    # Validate command line arguments
    if len(sys.argv) < 2:
        print("Usage: python script.py <database.db>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"Error: File {input_file} not found.")
        sys.exit(1)

    try:
        convert_sqlite_to_json(input_file)
        print(
            f"Successfully converted {input_file} to {input_file.with_suffix('.json')}"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
