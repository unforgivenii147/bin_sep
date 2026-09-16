#!/data/data/com.termux/files/home/.local/bin/python
"""mkhtml.py – Mkhtml utilities.

This module provides functionality for mkhtml."""
from __future__ import annotations
import sys
from pathlib import Path
HTML_TEMPLATE = '<!doctype html>\n<html>\n  <head>\n    <link rel="stylesheet" href="style.css" />\n    <script src="script.js"></script>\n    <title>html template</title>\n  </head>\n  <body>\n    <div>\n      <h2>Heading2</h2>\n    </div>\n  </body>\n</html>\n'
if __name__ == '__main__':
    file_name = Path(sys.argv[1]) or Path('index.html')
    file_name.write_text(HTML_TEMPLATE, encoding='utf-8')
