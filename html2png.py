#!/data/data/com.termux/files/home/.local/bin/python
"""html2png.py – Html2Png utilities.

This module provides functionality for html2png."""
from __future__ import annotations
import os
from pathlib import Path

def html_to_png(html_content: str, output_path: Path | str, dpi: int=150) -> None:
    """html_to_png – html to png.

Args:
    html_content: Description of html_content.
    output_path: Description of output_path.
    dpi: Description of dpi."""
    if html_content.startswith(('<', '<!DOCTYPE')):
        html = HTML(string=html_content)
    else:
        html = HTML(filename=html_content)
    pdf_bytes = html.write_pdf()
    from pdf2image import convert_from_bytes
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    if len(images) > 1:
        total_height = sum((img.height for img in images))
        max_width = max((img.width for img in images))
        combined = Image.new('RGB', (max_width, total_height), (255, 255, 255))
        y_offset = 0
        for img in images:
            combined.paste(img, (0, y_offset))
            y_offset += img.height
        combined.save(output_path, 'PNG')
    else:
        images[0].save(output_path, 'PNG')
    print(f'Full page PNG saved to: {output_path}')

def batch_convert(input_dir: Path | str, output_dir: Path | str, width: int=1200) -> None:
    """batch_convert – batch convert.

Args:
    input_dir: Description of input_dir.
    output_dir: Description of output_dir.
    width: Description of width."""
    os.makedirs(output_dir, exist_ok=True)
    for html_file in Path(input_dir).glob('*.html'):
        output_name = html_file.stem + '.png'
        output_path = os.path.join(output_dir, output_name)
        html_to_png(str(html_file), output_path, width=width)
batch_convert('html_files/', 'png_output/', width=1600)
