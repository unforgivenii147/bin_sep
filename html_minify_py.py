#!/data/data/com.termux/files/home/.local/bin/python
"""html_minify_py.py – Html Minify Py utilities.

This module provides functionality for html minify py."""
from __future__ import annotations
from typing import Any
import re
import sys
from pathlib import Path
from dh import get_files, mpf_async
from lxml import html as lxml_html
from lxml.html import HtmlElement

class HTMLMinifier:
    """HTMLMinifier – HTMLMinifier."""

    def __init__(self, remove_comments: bool=True, collapse_whitespace: bool=True, remove_empty_attributes: bool=True, remove_optional_tags: bool=False, minify_css: bool=False, minify_js: bool=False) -> None:
        """__init__ –   init  .

Args:
    remove_comments: Description of remove_comments.
    collapse_whitespace: Description of collapse_whitespace.
    remove_empty_attributes: Description of remove_empty_attributes.
    remove_optional_tags: Description of remove_optional_tags.
    minify_css: Description of minify_css.
    minify_js: Description of minify_js."""
        self.remove_comments = remove_comments
        self.collapse_whitespace = collapse_whitespace
        self.remove_empty_attributes = remove_empty_attributes
        self.remove_optional_tags = remove_optional_tags
        self.minify_css = minify_css
        self.minify_js = minify_js
        self._preserve_tags = {'pre', 'textarea', 'code', 'script', 'style'}

    def minify(self, html_str: str) -> str:
        """minify – minify.

Args:
    html_str: Description of html_str.

Returns:
    str: Description of return value."""
        try:
            doc = lxml_html.fromstring(html_str)
        except lxml_html.ParserError:
            doc = lxml_html.fragment_fromstring(html_str, create_parent=True)
        self._process_node(doc)
        result = lxml_html.tostring(doc, encoding='unicode', method='html')
        return self._post_process(result)

    def _process_node(self, node: HtmlElement) -> None:
        """_process_node –  process node.

Args:
    node: Description of node."""
        if node.tag in self._preserve_tags:
            return
        if node.text and self.collapse_whitespace:
            node.text = self._collapse_whitespace(node.text)
        if self.remove_empty_attributes and node.attrib:
            attrs_to_remove = [k for k, v in node.attrib.items() if not v or v.isspace()]
            for attr in attrs_to_remove:
                del node.attrib[attr]
        for child in list(node):
            self._process_node(child)
            if child.tail and self.collapse_whitespace:
                child.tail = self._collapse_whitespace(child.tail)

    def _collapse_whitespace(self, text: str) -> str:
        """_collapse_whitespace –  collapse whitespace.

Args:
    text: Description of text.

Returns:
    str: Description of return value."""
        text = re.sub('\\s+', ' ', text)
        return text.strip()

    def _post_process(self, html_str: str) -> str:
        """_post_process –  post process.

Args:
    html_str: Description of html_str.

Returns:
    str: Description of return value."""
        if self.remove_comments:
            html_str = re.sub('<!--.*?-->', '', html_str, flags=re.DOTALL)
        if self.minify_css:
            html_str = self._minify_style_tags(html_str)
        if self.minify_js:
            html_str = self._minify_script_tags(html_str)
        html_str = re.sub('>\\s+<', '><', html_str)
        html_str = re.sub('\\s+', ' ', html_str).strip()
        return html_str

    def _minify_style_tags(self, html_str: str) -> str:
        """_minify_style_tags –  minify style tags.

Args:
    html_str: Description of html_str.

Returns:
    str: Description of return value."""

        def minify_css(match: Any) -> Any:
            """minify_css – minify css.

Args:
    match: Description of match."""
            css = match.group(1)
            css = re.sub('/\\*.*?\\*/', '', css, flags=re.DOTALL)
            css = re.sub('\\s*([{};:,])\\s*', '\\1', css)
            css = re.sub(';\\s*}', '}', css)
            return f'<style>{css.strip()}</style>'
        return re.sub('<style[^>]*>(.*?)</style>', minify_css, html_str, flags=re.DOTALL)

    def _minify_script_tags(self, html_str: str) -> str:
        """_minify_script_tags –  minify script tags.

Args:
    html_str: Description of html_str.

Returns:
    str: Description of return value."""

        def minify_js(match: Any) -> Any:
            """minify_js – minify js.

Args:
    match: Description of match."""
            js = match.group(1)
            js = re.sub('//.*?$', '', js, flags=re.MULTILINE)
            js = re.sub('/\\*.*?\\*/', '', js, flags=re.DOTALL)
            js = re.sub('\\s+', ' ', js)
            return f'<script>{js.strip()}</script>'
        return re.sub('<script[^>]*>(.*?)</script>', minify_js, html_str, flags=re.DOTALL)

def minify(html_str: str, remove_comments: bool=True, collapse_whitespace: bool=True, **options: Any) -> str:
    """minify – minify.

Args:
    html_str: Description of html_str.
    remove_comments: Description of remove_comments.
    collapse_whitespace: Description of collapse_whitespace.
    **options: Description of **options.

Returns:
    str: Description of return value."""
    minifier = HTMLMinifier(remove_comments=remove_comments, collapse_whitespace=collapse_whitespace, **options)
    return minifier.minify(html_str)

def process_file(path: str | Path, **options: Any) -> str:
    """process_file – process file.

Args:
    path: Description of path.
    **options: Description of **options.

Returns:
    str: Description of return value."""
    path = Path(path)
    html_str = path.read_text(encoding='utf-8')
    minified = minify(html_str, **options)
    path.write_text(minified, encoding='utf-8')
    return minified

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    args = sys.argv[1:]
    files = [Path(p) for p in args] if args else get_files(cwd, ext=['.html'])
    mpf_async(process_file, files)
if __name__ == '__main__':
    raise SystemExit(main())
