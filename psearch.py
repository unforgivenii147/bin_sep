#!/data/data/com.termux/files/home/.local/bin/python
"""psearch.py – Psearch utilities.

This module provides functionality for psearch."""
from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass
import requests

@dataclass
class Package:
    """Package – Package."""
    name: str
    version: str
    summary: str
    url: str

    def __str__(self) -> str:
        """__str__ –   str  .

Returns:
    str: Description of return value."""
        return f'{self.name} ({self.version})\n  {self.summary}\n  {self.url}'

class PyPISearch:
    """PyPISearch – PyPISearch."""
    BASE_URL = 'https://pypi.org/pypi'
    SEARCH_URL = 'https://pypi.org/pypi/_/json'

    def __init__(self, timeout: int=10) -> None:
        """__init__ –   init  .

Args:
    timeout: Description of timeout."""
        self.timeout = timeout

    def search(self, query: str, limit: int | None=None) -> list[Package]:
        """search – search.

Args:
    query: Description of query.
    limit: Description of limit.

Returns:
    list[Package]: Description of return value."""
        try:
            response = requests.get(self.SEARCH_URL, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f'Error fetching PyPI data: {e}', file=sys.stderr)
            return []
        query_lower = query.lower()
        results = []
        for pkg_name, pkg_data in data.get('packages', {}).items():
            if query_lower in pkg_name.lower():
                info = pkg_data.get('latest', {})
                results.append(Package(name=pkg_name, version=info.get('version', 'unknown'), summary=info.get('summary', 'No description'), url=f'{self.BASE_URL}/{pkg_name}/'))
            if limit and len(results) >= limit:
                break
        return sorted(results, key=lambda p: p.name.lower())

    def search_json(self, query: str, limit: int | None=None) -> str:
        """search_json – search json.

Args:
    query: Description of query.
    limit: Description of limit.

Returns:
    str: Description of return value."""
        results = self.search(query, limit)
        return json.dumps([{'name': pkg.name, 'version': pkg.version, 'summary': pkg.summary, 'url': pkg.url} for pkg in results], indent=2)

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Search PyPI packages', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('query', help='Package name or keyword to search')
    parser.add_argument('-l', '--limit', type=int, default=None, help='Limit results (default: all matches)')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    args = parser.parse_args()
    searcher = PyPISearch(timeout=args.timeout)
    if args.json:
        print(searcher.search_json(args.query, args.limit))
    else:
        results = searcher.search(args.query, args.limit)
        if not results:
            print(f"No packages found for '{args.query}'", file=sys.stderr)
            sys.exit(1)
        print(f'Found {len(results)} package(s):\n')
        for pkg in results:
            print(pkg)
            print()
if __name__ == '__main__':
    raise SystemExit(main())
