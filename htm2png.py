#!/data/data/com.termux/files/home/.local/bin/python
"""htm2png.py – Htm2Png utilities.

This module provides functionality for htm2png."""
from __future__ import annotations
from pathlib import Path
import cairosvg
from weasyprint import HTML

def html_to_png_cairo(html_content: str, output_path: Path | str, width: int | None=None) -> None:
    """html_to_png_cairo – html to png cairo.

Args:
    html_content: Description of html_content.
    output_path: Description of output_path.
    width: Description of width."""
    if html_content.startswith(('<', '<!DOCTYPE')):
        html = HTML(string=html_content)
    else:
        html = HTML(filename=html_content)
    pdf_bytes = html.write_pdf()
    cairosvg.svg2png(bytestring=pdf_bytes, write_to=output_path, output_width=width, scale=2.0)
    print(f'PNG saved to: {output_path}')
