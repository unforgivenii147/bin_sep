#!/data/data/com.termux/files/home/.local/bin/python
"""transocr.py – Transocr utilities.

This module provides functionality for transocr."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Final
import pytesseract
from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, detect
from PIL import Image, ImageEnhance, ImageFilter
CHUNK_SIZE = 1024 * 1024
DetectorFactory.seed = 0
TEXT_EXT: Final[set[str]] = {'.txt', '.md', '.csv', '.json', '.py'}
IMAGE_EXT: Final[set[str]] = {'.jpg', '.jpeg', '.png'}
CHUNK_SIZE: Final[int] = 2000

def detect_lang_from_text(text: str) -> str:
    """detect_lang_from_text – detect lang from text.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""
    if not (stripped := text.strip()):
        return 'unknown'
    try:
        return detect(stripped[:500])
    except Exception:
        return 'unknown'

def read_text_file(path: Path) -> str:
    """read_text_file – read text file.

Args:
    path: Description of path.

Returns:
    str: Description of return value."""
    if path.suffix.lower() not in TEXT_EXT:
        raise ValueError(f'Unsupported text file extension: {path.suffix}')
    return path.read_text(encoding='utf-8')

def preprocess_image(img: Image.Image) -> Image.Image:
    """preprocess_image – preprocess image.

Args:
    img: Description of img.

Returns:
    Image.Image: Description of return value."""
    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.point(lambda x: 0 if x < 160 else 255)
    return img.filter(ImageFilter.MedianFilter(size=3))

def read_image_ocr(path: Path) -> str:
    """read_image_ocr – read image ocr.

Args:
    path: Description of path.

Returns:
    str: Description of return value."""
    try:
        with Image.open(path) as img:
            processed_img = preprocess_image(img)
            return pytesseract.image_to_string(processed_img)
    except Exception as e:
        raise RuntimeError(f'OCR failed for {path}: {e}') from e

def chunk_text(text: str, size: int=32768) -> list[str]:
    """chunk_text – chunk text.

Args:
    text: Description of text.
    size: Description of size.

Returns:
    list[str]: Description of return value."""
    return [text[i:i + size] for i in range(0, len(text), size)]

def translate_chunks(chunks: list[str], src_lang: str) -> str:
    """translate_chunks – translate chunks.

Args:
    chunks: Description of chunks.
    src_lang: Description of src_lang.

Returns:
    str: Description of return value."""
    translator = GoogleTranslator(source=src_lang, target='en')
    return ''.join((translator.translate(chunk) for chunk in chunks))

def build_output_paths(input_path: Path) -> tuple[Path, Path | None]:
    """build_output_paths – build output paths.

Args:
    input_path: Description of input_path.

Returns:
    tuple[Path, Path | None]: Description of return value."""
    suffix = input_path.suffix.lower()
    if suffix in IMAGE_EXT:
        translated = input_path.with_name(f'{input_path.stem}_eng.txt')
        raw_ocr = input_path.with_name(f'{input_path.stem}_ocr.txt')
        return (translated, raw_ocr)
    translated = input_path.with_name(f'{input_path.stem}_eng{suffix}')
    return (translated, None)

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Translate text or image to English.')
    parser.add_argument('input_path', type=Path, help='Path to the input file.')
    parser.add_argument('--lang', default='auto', help="Source language code or 'auto'")
    args = parser.parse_args()
    in_path: Path = args.input_path
    if not in_path.exists():
        print(f'Error: File not found: {in_path}', file=sys.stderr)
        sys.exit(1)
    try:
        suffix = in_path.suffix.lower()
        raw_ocr_path: Path | None = None
        if suffix in TEXT_EXT:
            text = read_text_file(in_path)
        elif suffix in IMAGE_EXT:
            text = read_image_ocr(in_path)
            _, raw_ocr_path = build_output_paths(in_path)
            if raw_ocr_path:
                raw_ocr_path.write_text(text, encoding='utf-8')
        else:
            print(f'Unsupported file type: {suffix}. Use text or common image formats.')
            sys.exit(0)
        src_lang = args.lang
        if src_lang == 'auto':
            src_lang = detect_lang_from_text(text)
        chunks = chunk_text(text)
        translated = translate_chunks(chunks, src_lang)
        out_path, _ = build_output_paths(in_path)
        out_path.write_text(translated, encoding='utf-8')
        print(f'✓ Translated output saved to {out_path}')
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    raise SystemExit(main())
