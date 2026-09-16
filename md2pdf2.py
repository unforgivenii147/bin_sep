#!/data/data/com.termux/files/home/.local/bin/python
"""md2pdf2.py – Md2Pdf2 utilities.

This module provides functionality for md2pdf2."""
from __future__ import annotations
from typing import Any
from pathlib import Path
import re
import sys
from markdown2 import markdown_path
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from weasyprint import CSS, HTML

class ValidationError(Exception):
    """ValidationError – ValidationError."""
    pass
TOC_HTML = '\n<nav class="toc">\n<h1>Contents</h1>\n<ul></ul>\n</nav>\n'

def pygments_highlight(html: str) -> str:
    """pygments_highlight – pygments highlight.

Args:
    html: Description of html.

Returns:
    str: Description of return value."""
    formatter = HtmlFormatter(cssclass='highlight')
    code_block_re = re.compile('<pre><code class="language-(\\w+)">(.*?)</code></pre>', re.DOTALL)

    def repl(match: Any) -> str:
        """repl – repl.

Args:
    match: Description of match.

Returns:
    str: Description of return value."""
        lang = match.group(1)
        code = match.group(2)
        code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        try:
            lexer = get_lexer_by_name(lang)
        except Exception:
            lexer = TextLexer()
        return highlight(code, lexer, formatter)
    return code_block_re.sub(repl, html)

def md2pdf(pdf_path: Path | str, md_path: Path | str, css_path: Path | str | None=None, base_url: Any | None=None) -> None:
    """md2pdf – md2pdf.

Args:
    pdf_path: Description of pdf_path.
    md_path: Description of md_path.
    css_path: Description of css_path.
    base_url: Description of base_url."""
    extras = ['header-ids', 'fenced-code-blocks', 'tables', 'cuddled-lists']
    html = markdown_path(md_path, extras=extras)
    if not html.strip():
        raise ValidationError(msg)
    html = pygments_highlight(html)
    html = TOC_HTML + html
    html_doc = HTML(string=html, base_url=base_url)
    stylesheets = []
    if css_path:
        stylesheets.append(CSS(filename=css_path))
    html_doc.write_pdf(pdf_path, stylesheets=stylesheets)
if __name__ == '__main__':
    md_file = sys.argv[1]
    pdf_file = md_file.replace('.md', '.pdf')
    md2pdf(pdf_path=pdf_file, md_path=md_file, css_path='/sdcard/_static/css/book.css', base_url='.')
