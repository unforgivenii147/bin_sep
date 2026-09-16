#!/data/data/com.termux/files/home/.local/bin/python
"""md2pdf.py – Md2Pdf utilities.

This module provides functionality for md2pdf."""
from __future__ import annotations
from typing import Any
from pathlib import Path
import sys
from markdown2 import markdown, markdown_path
from weasyprint import CSS, HTML

def md2pdf(pdf_path: Path | str, md_content: Any | None=None, md_path: Path | str | None=None, css_path: str='/sdcard/_static/css/markdown.css', base_url: Any | None=None) -> None:
    """md2pdf – md2pdf.

Args:
    pdf_path: Description of pdf_path.
    md_content: Description of md_content.
    md_path: Description of md_path.
    css_path: Description of css_path.
    base_url: Description of base_url."""
    raw_html = ''
    extras = ['cuddled-lists', 'tables']
    if md_path:
        raw_html = markdown_path(md_path, extras=extras)
    elif md_content:
        raw_html = markdown(md_content, extras=extras)
    if not len(raw_html):
        msg = 'Input markdown seems empty'
        raise ValidationError(msg)
    html = HTML(string=raw_html, base_url=base_url)
    css = []
    if css_path:
        css.append(CSS(filename=css_path))
    html.write_pdf(pdf_path, stylesheets=css)
if __name__ == '__main__':
    md_file = sys.argv[1]
    pdf_file = md_file.replace('.md', '.pdf')
    md2pdf(pdf_path=pdf_file, md_path=md_file)
