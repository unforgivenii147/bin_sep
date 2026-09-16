#!/data/data/com.termux/files/home/.local/bin/python
"""html2pdf.py – Html2Pdf utilities.

This module provides functionality for html2pdf."""
from __future__ import annotations
from typing import Any
import sys
from pathlib import Path
from weasyprint import CSS, HTML

def html2pdf(pdf_path: Path | str, html_path: Path | str | None=None, css_path: str='/sdcard/_static/css/markdown.css', base_url: Any | None=None) -> None:
    """html2pdf – html2pdf.

Args:
    pdf_path: Description of pdf_path.
    html_path: Description of html_path.
    css_path: Description of css_path.
    base_url: Description of base_url."""
    raw_html = ''
    if html_path:
        raw_html = html_path.read_text(encoding='utf8')
    html = HTML(string=raw_html, base_url=base_url)
    css = []
    if css_path:
        css.append(CSS(filename=css_path))
    html.write_pdf(pdf_path, stylesheets=css)
if __name__ == '__main__':
    html_file = Path(sys.argv[1])
    pdf_file = html_file.with_suffix('.pdf')
    html2pdf(pdf_path=pdf_file, html_path=html_file)
