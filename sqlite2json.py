#!/data/data/com.termux/files/home/.local/bin/python
"""
SQLite to JSON Converter
Converts all tables in a SQLite database to separate JSON files.
Auto-detects tables and continues on errors.
"""

import json
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


def json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="ignore")
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Type {type(obj)} not serializable")


def get_tables(conn: sqlite3.Connection) -> list[str]:
    """Get all table names from the SQLite database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def table_to_json(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """Convert a table to a list of dictionaries (JSON format)"""
    cursor = conn.cursor()

    # Get column names
    cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 1')
    columns = [description[0] for description in cursor.description]

    # Fetch all rows
    cursor.execute(f'SELECT * FROM "{table_name}"')
    rows = cursor.fetchall()

    # Convert to list of dictionaries
    result = []
    for row in rows:
        row_dict = {}
        for i, column in enumerate(columns):
            row_dict[column] = row[i]
        result.append(row_dict)

    return result


def save_json(
    data: list[dict],
    table_name: str,
    output_dir: Path,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> Path:
    """Save data as JSON file"""
    output_file = output_dir / f"{table_name}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            data, f, indent=indent, ensure_ascii=ensure_ascii, default=json_serializer
        )

    return output_file


def convert_sqlite_to_json(
    db_path: str, output_dir: str | None = None, indent: int = 2, verbose: bool = True
) -> dict:
    """
    Convert SQLite database to JSON files

    Args:
        db_path: Path to SQLite database file
        output_dir: Directory to save JSON files (default: same as database name)
        indent: JSON indentation (default: 2)
        verbose: Print progress information

    Returns:
        Dictionary with conversion statistics
    """
    # Validate database file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # Set up output directory
    if output_dir is None:
        db_stem = Path(db_path).stem
        output_dir = Path(f"{db_stem}_json")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "database": db_path,
        "output_directory": str(output_dir),
        "tables_found": 0,
        "tables_converted": 0,
        "tables_failed": 0,
        "total_rows": 0,
        "errors": [],
    }

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)

        if verbose:
            print(f"📁 Database: {db_path}")
            print(f"📂 Output directory: {output_dir}")
            print("-" * 50)

        # Get all tables
        tables = get_tables(conn)
        stats["tables_found"] = len(tables)

        if verbose:
            print(f"Found {len(tables)} tables")

        # Convert each table
        for table_name in tables:
            try:
                if verbose:
                    print(f"\n🔄 Converting table: '{table_name}'...")

                # Convert table to JSON
                data = table_to_json(conn, table_name)

                # Save to file
                output_file = save_json(data, table_name, output_dir, indent)

                stats["tables_converted"] += 1
                stats["total_rows"] += len(data)

                if verbose:
                    print(f"  ✅ Saved {len(data)} rows to {output_file.name}")

            except Exception as e:
                stats["tables_failed"] += 1
                error_msg = f"Error converting table '{table_name}': {e!s}"
                stats["errors"].append(error_msg)

                if verbose:
                    print(f"  ❌ {error_msg}")
                continue

        conn.close()

    except Exception as e:
        error_msg = f"Database connection error: {e!s}"
        stats["errors"].append(error_msg)
        if verbose:
            print(f"❌ {error_msg}")

    # Print summary
    if verbose:
        print("\n" + "=" * 50)
        print("📊 Conversion Summary:")
        print(f"  Tables found: {stats['tables_found']}")
        print(f"  Tables converted: {stats['tables_converted']}")
        print(f"  Tables failed: {stats['tables_failed']}")
        print(f"  Total rows converted: {stats['total_rows']}")
        if stats["errors"]:
            print(f"  Errors: {len(stats['errors'])}")
            for error in stats["errors"]:
                print(f"    - {error}")

    return stats


def main():
    """Main function with command-line argument parsing"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert SQLite database tables to JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s database.db
  %(prog)s database.db -o output_folder
  %(prog)s database.db --indent 4 --no-verbose
        """,
    )

    parser.add_argument("database", help="Path to SQLite database file")
    parser.add_argument("-o", "--output", help="Output directory for JSON files")
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON indentation (default: 2)"
    )
    parser.add_argument(
        "--no-verbose", action="store_true", help="Suppress progress output"
    )
    parser.add_argument(
        "--compact", action="store_true", help="Output compact JSON (no indentation)"
    )

    args = parser.parse_args()

    try:
        indent = 0 if args.compact else args.indent
        stats = convert_sqlite_to_json(
            args.database, args.output, indent, verbose=not args.no_verbose
        )

        # Exit with error code if any table failed
        if stats["tables_failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
