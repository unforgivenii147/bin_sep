#!/data/data/com.termux/files/home/.local/bin/python
"""fix_html_md_broken_links.py – Fix Html Md Broken Links utilities.

This module provides functionality for fix html md broken links."""
from __future__ import annotations
import os
import re
from pathlib import Path
static_dir = '/sdcard/_static'

def fix_links(path: Path) -> None:
    """fix_links – fix links.

Args:
    path: Description of path."""
    content: str = path.read_text(encoding='utf-8', errors='replace')
    links = re.findall('href=[\\\'\\"]?([^\\\'\\" >]+)', content)
    for link in links:
        if not Path(link).exists():
            static_file = static_dir / link
            if static_file.exists():
                content = content.replace(link, str(static_file.resolve()))
    backup_path = path.with_suffix('.bak')
    Path(path).replace(backup_path)
    Path(path).write_text(content, encoding='utf-8')

def main() -> None:
    """main – main."""
    for root, _dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.md', '.html')):
                path = Path(root) / file
                fix_links(path)
if __name__ == '__main__':
    raise SystemExit(main())
