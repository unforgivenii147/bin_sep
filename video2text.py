#!/data/data/com.termux/files/home/.local/bin/python
"""video2text.py – Video2Text utilities.

This module provides functionality for video2text."""
from __future__ import annotations
from typing import Any
import sys
from pathlib import Path
import cv2
import pytesseract
from dh import cprint
from PIL import Image
video = sys.argv[1]
txtfile = Path(video).with_suffix('.txt')

def process_frame(frame_id: int, frame: Any) -> None:
    """process_frame – process frame.

Args:
    frame_id: Description of frame_id.
    frame: Description of frame."""
    frame = cv2.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = 255 - gray
    text = pytesseract.image_to_string(Image.fromarray(gray), lang='eng', config='--oem 3 --psm 6')
    if text and len(text.strip()) > 5:
        cprint(f'frame {frame_id} --> {text}', 'cyan')
        txtfile.open('a', encoding='utf-8').write(text + '\n')
    else:
        cprint(f'frame {frame_id} --> no text', 'blue')

def main() -> None:
    """main – main."""
    cap = cv2.VideoCapture(video)
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        process_frame(frame_id, frame)
        frame_id += 1
if __name__ == '__main__':
    raise SystemExit(main())
