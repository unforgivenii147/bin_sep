#!/data/data/com.termux/files/home/.local/bin/python
"""strip_html_tags.py – Strip Html Tags utilities.

This module provides functionality for strip html tags."""
from __future__ import annotations
from typing import Any
import multiprocessing as mp
import os
import sys
from html.parser import HTMLParser
from pathlib import Path
from tempfile import NamedTemporaryFile
SKIP_CONTENT_TAGS = {'script', 'style', 'noscript', 'template', 'head'}
BLOCK_TAGS = {'address', 'article', 'aside', 'blockquote', 'br', 'dd', 'div', 'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main', 'nav', 'ol', 'p', 'pre', 'section', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'ul'}
RAWTEXT_TAGS = {'script', 'style', 'textarea', 'title'}

def _find_safe_splits(path: Path, n: int) -> list[int]:
    """Return n-1 byte offsets that are safe places to split the file.

    A safe split is a position that is NOT inside a tag and NOT inside a
    raw-text element (script/style/textarea/title). We scan bytes once.
    """
    size = path.stat().st_size
    if n <= 1 or size == 0:
        return []
    targets = [size * i // n for i in range(1, n)]
    splits: list[int] = []
    in_tag = False
    raw_until_close: bytes | None = None
    pos = 0
    ti = 0
    CHUNK = 1 << 20
    with path.open('rb') as f:
        buf = b''
        buf_start = 0
        while ti < len(targets):
            if pos >= buf_start + len(buf):
                buf_start = pos
                buf = f.read(CHUNK)
                if not buf:
                    break
            b = buf[pos - buf_start]
            pos += 1
            if raw_until_close is not None:
                if b == ord('<'):
                    end = buf_start + len(buf)
                    window = buf[pos - 1 - buf_start:pos - 1 - buf_start + 16]
                    if window.lower().startswith(raw_until_close):
                        raw_until_close = None
                        in_tag = True
                continue
            if in_tag:
                if b == ord('>'):
                    in_tag = False
                continue
            if b == ord('<'):
                end = buf_start + len(buf)
                window = buf[pos - 1 - buf_start:pos - 1 - buf_start + 16]
                if window.startswith(b'</'):
                    j = 2
                    name = bytearray()
                    while j < len(window) and window[j:j + 1].isalpha():
                        name += window[j:j + 1]
                        j += 1
                    in_tag = True
                else:
                    j = 1
                    name = bytearray()
                    while j < len(window) and window[j:j + 1].isalpha():
                        name += window[j:j + 1]
                        j += 1
                    tagname = bytes(name).lower()
                    if tagname in RAWTEXT_TAGS:
                        raw_until_close = b'</' + tagname
                    in_tag = True
                continue
            while ti < len(targets) and pos >= targets[ti]:
                splits.append(pos)
                ti += 1
    while len(splits) < n - 1:
        splits.append(size)
    return splits

class _TextExtractor(HTMLParser):
    """_TextExtractor –  TextExtractor."""

    def __init__(self) -> None:
        """__init__ –   init  ."""
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []
        self._pending_space = False

    def handle_starttag(self, tag: Any, attrs: Any) -> None:
        """handle_starttag – handle starttag.

Args:
    tag: Description of tag.
    attrs: Description of attrs."""
        if tag in SKIP_CONTENT_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self._pending_space = True

    def handle_startendtag(self, tag: Any, attrs: Any) -> None:
        """handle_startendtag – handle startendtag.

Args:
    tag: Description of tag.
    attrs: Description of attrs."""
        if tag in BLOCK_TAGS:
            self._pending_space = True

    def handle_endtag(self, tag: Any) -> None:
        """handle_endtag – handle endtag.

Args:
    tag: Description of tag."""
        if tag in SKIP_CONTENT_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag in BLOCK_TAGS:
            self._pending_space = True

    def handle_data(self, data: str) -> None:
        """handle_data – handle data.

Args:
    data: Description of data."""
        if self._skip_depth:
            return
        if self._pending_space:
            self._chunks.append(' ')
            self._pending_space = False
        self._chunks.append(data)

    def get_text(self) -> str:
        """get_text – get text.

Returns:
    str: Description of return value."""
        return ' '.join(''.join(self._chunks).split())

def _parse_slice(args: tuple[str, int, int]) -> str:
    """_parse_slice –  parse slice.

Args:
    args: Description of args.

Returns:
    str: Description of return value."""
    path_str, start, end = args
    parser = _TextExtractor()
    CHUNK = 1 << 16
    with open(path_str, 'rb') as f:
        f.seek(start)
        remaining = end - start
        while remaining > 0:
            data = f.read(min(CHUNK, remaining))
            if not data:
                break
            remaining -= len(data)
            parser.feed(data.decode('utf-8', errors='replace'))
    parser.close()
    return parser.get_text()

def process_file(path: Path, workers: int | None=None) -> bool:
    """process_file – process file.

Args:
    path: Description of path.
    workers: Description of workers.

Returns:
    bool: Description of return value."""
    if workers is None:
        workers = min(4, os.cpu_count() or 1)
    size = path.stat().st_size
    if size == 0:
        return True
    splits = _find_safe_splits(path, workers)
    bounds = [0, *splits, size]
    ranges = [(str(path), bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    try:
        try:
            ctx = mp.get_context('fork')
        except ValueError:
            ctx = mp.get_context()
        with ctx.Pool(processes=workers) as pool:
            pieces = pool.map(_parse_slice, ranges)
        text = ' '.join((p for p in pieces if p))
        with NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False, prefix=path.name + '.', suffix='.tmp') as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(text)
        os.replace(tmp_path, path)
        return True
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return False

def main() -> None:
    """main – main."""
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} FILE [workers]', file=sys.stderr)
        raise SystemExit(2)
    path = Path(sys.argv[1])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else None
    raise SystemExit(0 if process_file(path, workers) else 1)
if __name__ == '__main__':
    raise SystemExit(main())
