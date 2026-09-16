#!/data/data/com.termux/files/home/.local/bin/python
"""remove_image_refrences.py – Remove Image Refrences utilities.

This module provides functionality for remove image refrences."""
from __future__ import annotations
from typing import Any
import re
from pathlib import Path
REMOTE_PREFIXES = ('http://', 'https://', '//')
IMG_TAG_RE = re.compile('<img\\b[^>]*\\bsrc\\s*=\\s*[\\"\']([^\\"\']+)[\\"\'][^>]*>', re.IGNORECASE)

def remove_remote_html_images(text: str) -> str:
    """remove_remote_html_images – remove remote html images.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""

    def repl(match: Any) -> Any:
        """repl – repl.

Args:
    match: Description of match."""
        src = match.group(1)
        if src.startswith(REMOTE_PREFIXES):
            return ''
        return match.group(0)
    return IMG_TAG_RE.sub(repl, text)
MD_INLINE_IMG_RE = re.compile('!\\[.*?\\]\\((.*?)\\)', re.IGNORECASE)
MD_REF_IMG_RE = re.compile('!\\[.*?\\]\\[(.*?)\\]', re.IGNORECASE)
MD_REF_DEF_RE = re.compile('^\\s*\\[(.*?)\\]:\\s*(\\S+)', re.MULTILINE)
RST_IMG_RE = re.compile('^\\s*\\.\\. \\|[^|]+\\| image:: https?://[^\\s]+.*$', re.MULTILINE)

def remove_remote_md_images(text: str) -> str:
    """remove_remote_md_images – remove remote md images.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""

    def inline_repl(match: Any) -> Any:
        """inline_repl – inline repl.

Args:
    match: Description of match."""
        url = match.group(1)
        if url.startswith(REMOTE_PREFIXES):
            return ''
        return match.group(0)
    text = MD_INLINE_IMG_RE.sub(inline_repl, text)
    remote_ids = set()
    for m in MD_REF_DEF_RE.finditer(text):
        ref_id, url = m.groups()
        if url.startswith(REMOTE_PREFIXES):
            remote_ids.add(ref_id)

    def ref_repl(match: Any) -> Any:
        """ref_repl – ref repl.

Args:
    match: Description of match."""
        ref_id = match.group(1)
        if ref_id in remote_ids:
            return ''
        return match.group(0)
    text = MD_REF_IMG_RE.sub(ref_repl, text)

    def def_repl(match: Any) -> Any:
        """def_repl – def repl.

Args:
    match: Description of match."""
        ref_id, _url = match.groups()
        if ref_id in remote_ids:
            return ''
        return match.group(0)
    return MD_REF_DEF_RE.sub(def_repl, text)

def remove_remote_rst_images(text: str) -> str:
    """remove_remote_rst_images – remove remote rst images.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""
    return RST_IMG_RE.sub('', text)

def process_file(path: Path) -> None:
    """process_file – process file.

Args:
    path: Description of path."""
    path = Path(path)
    original = path.read_text(encoding='utf-8', errors='ignore')
    modified = original
    if path.suffix.lower() in {'.html', '.htm'}:
        modified = remove_remote_html_images(original)
    elif path.suffix.lower() == '.md':
        modified = remove_remote_md_images(original)
    elif path.suffix.lower() in {'.rst', '.txt'}:
        modified = remove_remote_rst_images(original)
        modified = remove_remote_md_images(modified)
    if modified != original:
        path.write_text(modified, encoding='utf-8')
        print(f'Modified: {path}')

def main() -> None:
    """main – main."""
    extensions = {'.html', '.htm', '.md', '.rst', '.txt'}
    for file in Path().rglob('*'):
        if file.is_file() and file.suffix.lower() in extensions:
            process_file(file)
if __name__ == '__main__':
    raise SystemExit(main())
