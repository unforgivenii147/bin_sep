#!/data/data/com.termux/files/home/.local/bin/python
"""txt2wav.py – Txt2Wav utilities.

This module provides functionality for txt2wav."""
from __future__ import annotations
from typing import Any
import subprocess
from pathlib import Path

def speak_text(text: str) -> None:
    """speak_text – speak text.

Args:
    text: Description of text."""
    subprocess.run(['termux-tts-speak', text], check=True)

def read_text_file(path: str) -> str:
    """read_text_file – read text file.

Args:
    path: Description of path.

Returns:
    str: Description of return value."""
    path = Path(path)
    if not path.exists():
        msg = 'error: file not found'
        raise FileNotFoundError(msg)
    return path.read_text(encoding='utf-8')

def chunk_text(text: str, max_chars: int=3000) -> Any:
    """chunk_text – chunk text.

Args:
    text: Description of text.
    max_chars: Description of max_chars."""
    chunks = []
    current = ''
    for paragraph in text.splitlines():
        if len(current) + len(paragraph) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
                current = paragraph
            else:
                chunks.append(paragraph[:max_chars])
                current = paragraph[max_chars:]
        else:
            current += paragraph + '\n'
    if current.strip():
        chunks.append(current.strip())
    return chunks

def text_file_to_speech(path: str) -> None:
    """text_file_to_speech – text file to speech.

Args:
    path: Description of path."""
    text = read_text_file(path)
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks, start=1):
        print(f'Speaking chunk {i}/{len(chunks)}...')
        speak_text(chunk)
if __name__ == '__main__':
    text_file_to_speech('/sdcard/Download/sample.txt')
