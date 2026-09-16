#!/data/data/com.termux/files/home/.local/bin/python
"""mdview_simple.py – Mdview Simple utilities.

This module provides functionality for mdview simple."""
from __future__ import annotations
import re
import sys
from pathlib import Path

def render_markdown(text: str) -> str:
    """render_markdown – render markdown.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""
    lines = text.splitlines()
    output = []
    in_code = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            output.append('\x1b[90m' + line + '\x1b[0m')
            continue
        if in_code:
            output.append('\x1b[90m' + line + '\x1b[0m')
            continue
        heading_match = re.match('^(#{1,6})\\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            output.append(f"\x1b[1;4m{'#' * level} {text}\x1b[0m")
            continue
        line = re.sub('\\*\\*(.+?)\\*\\*', '\\033[1m\\1\\033[0m', line)
        line = re.sub('\\*(.+?)\\*', '\\033[3m\\1\\033[0m', line)
        line = re.sub('`(.+?)`', '\\033[36m\\1\\033[0m', line)
        if re.match('^\\s*[-*]\\s+', line):
            output.append('\x1b[33m•\x1b[0m ' + re.sub('^\\s*[-*]\\s+', '', line))
            continue
        if re.match('^\\s*\\d+\\.\\s+', line):
            output.append('\x1b[33m' + line + '\x1b[0m')
            continue
        output.append(line)
    return '\n'.join(output)

def main() -> None:
    """main – main."""
    if len(sys.argv) < 2:
        print('Usage: python mdview.py <file.md>')
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f'Error: {path} does not exist.')
        sys.exit(1)
    content = path.read_text(encoding='utf-8')
    print(render_markdown(content))
if __name__ == '__main__':
    main()
