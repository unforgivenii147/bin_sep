#!/data/data/com.termux/files/home/.local/bin/python
"""termimg0.py – Termimg0 utilities.

This module provides functionality for termimg0."""
from __future__ import annotations
from pathlib import Path
import sys
from shutil import get_terminal_size
from PIL import Image

def print_image(image_path: Path | str, width: int=40) -> None:
    """print_image – print image.

Args:
    image_path: Description of image_path.
    width: Description of width."""
    img = Image.open(image_path).convert('RGB')
    aspect_ratio = img.height / img.width
    width = get_terminal_size()[0]
    height = int(width * aspect_ratio * 0.55)
    img = img.resize((width, height))
    pixels = img.load()
    for y in range(0, height - 1, 2):
        for x in range(width):
            r1, g1, b1 = pixels[x, y]
            r2, g2, b2 = pixels[x, y + 1]
            print(f'\x1b[48;2;{r1};{g1};{b1}m\x1b[38;2;{r2};{g2};{b2}m▀', end='')
        print('\x1b[0m')
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python termimg.py <image_path>')
    else:
        print_image(sys.argv[1])
