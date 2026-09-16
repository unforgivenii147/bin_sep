#!/data/data/com.termux/files/home/.local/bin/python
"""chm2pdf.py – Chm2Pdf utilities.

This module provides functionality for chm2pdf."""
from __future__ import annotations
from typing import Any
import html
import os
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
import chm.chm as pychm
from weasyprint import HTML

class CHMHTMLParser(HTMLParser):
    """CHMHTMLParser – CHMHTMLParser."""

    def __init__(self) -> None:
        """__init__ –   init  ."""
        super().__init__()
        self.content = []
        self.in_body = False
        self.skip_tags = {'script', 'style', 'meta', 'link', 'iframe'}
        self.current_skip_tag = None

    def handle_starttag(self, tag: Any, attrs: Any) -> None:
        """handle_starttag – handle starttag.

Args:
    tag: Description of tag.
    attrs: Description of attrs."""
        if tag in self.skip_tags:
            self.current_skip_tag = tag
        elif tag == 'body':
            self.in_body = True
        elif not self.current_skip_tag and self.in_body:
            attrs_str = ''.join((f' {k}="{v}"' for k, v in attrs if k != 'href' and k != 'src'))
            self.content.append(f'<{tag}{attrs_str}>')

    def handle_endtag(self, tag: Any) -> None:
        """handle_endtag – handle endtag.

Args:
    tag: Description of tag."""
        if tag == self.current_skip_tag:
            self.current_skip_tag = None
        elif tag == 'body':
            self.in_body = False
        elif not self.current_skip_tag and self.in_body:
            self.content.append(f'</{tag}>')

    def handle_data(self, data: str) -> None:
        """handle_data – handle data.

Args:
    data: Description of data."""
        if not self.current_skip_tag and self.in_body:
            self.content.append(data)

    def handle_startendtag(self, tag: Any, attrs: Any) -> None:
        """handle_startendtag – handle startendtag.

Args:
    tag: Description of tag.
    attrs: Description of attrs."""
        if tag not in self.skip_tags and self.in_body:
            attrs_str = ''.join((f' {k}="{v}"' for k, v in attrs if k != 'href' and k != 'src'))
            self.content.append(f'<{tag}{attrs_str} />')

    def get_content(self) -> Any:
        """get_content – get content."""
        return ''.join(self.content)

def extract_html_content(chm_file: Path | str) -> Any:
    """extract_html_content – extract html content.

Args:
    chm_file: Description of chm_file."""
    try:
        chm = pychm.CHMFile()
        if not chm.LoadCHM(str(chm_file)):
            raise Exception(f'Failed to load CHM file: {chm_file}')
        toc = chm.GetTopicsTree()
        if not toc:
            default_topic = chm.GetDefaultTopic()
            if default_topic:
                return extract_single_topic(chm, default_topic)
            else:
                files = chm.GetAllFiles()
                html_files = [f for f in files if f.lower().endswith(('.html', '.htm'))]
                if html_files:
                    return extract_multiple_topics(chm, html_files)
                else:
                    raise Exception('No HTML content found in CHM file')
        else:
            return extract_topics_from_toc(chm, toc)
    except Exception as e:
        raise Exception(f'Error extracting HTML from CHM: {e}')
    finally:
        if 'chm' in locals():
            chm.CloseCHM()

def extract_single_topic(chm: Any, topic_path: Path | str) -> Any:
    """extract_single_topic – extract single topic.

Args:
    chm: Description of chm.
    topic_path: Description of topic_path."""
    try:
        content = chm.RetrieveObject(chm.ResolveObject(topic_path))
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        return clean_html(content)
    except Exception as e:
        print(f'Warning: Could not extract topic {topic_path}: {e}')
        return ''

def extract_multiple_topics(chm: Any, topics: Any) -> Any:
    """extract_multiple_topics – extract multiple topics.

Args:
    chm: Description of chm.
    topics: Description of topics."""
    combined_html = ['<!DOCTYPE html><html><head><meta charset="utf-8"><style>body { font-family: Arial, sans-serif; line-height: 1.6; margin: 2em; }img { max-width: 100%; }h1, h2, h3, h4 { color: #333; }pre { background-color: #f5f5f5; padding: 1em; border-radius: 4px; }code { background-color: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; }</style></head><body>']
    for topic in topics:
        try:
            content = chm.RetrieveObject(chm.ResolveObject(topic))
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            cleaned = clean_html(content)
            if cleaned:
                combined_html.append(cleaned)
                combined_html.append('<hr style="border: 1px solid #ccc; margin: 20px 0;">')
        except Exception as e:
            print(f'Warning: Could not extract topic {topic}: {e}')
    combined_html.append('</body></html>')
    return ''.join(combined_html)

def extract_topics_from_toc(chm: Any, toc: Any) -> Any:
    """extract_topics_from_toc – extract topics from toc.

Args:
    chm: Description of chm.
    toc: Description of toc."""
    html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8"><style>body { font-family: Arial, sans-serif; line-height: 1.6; margin: 2em; }img { max-width: 100%; }h1, h2, h3, h4 { color: #333; }pre { background-color: #f5f5f5; padding: 1em; border-radius: 4px; }code { background-color: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; }</style></head><body>']

    def process_toc_node(node: Any, level: int=0) -> None:
        """process_toc_node – process toc node.

Args:
    node: Description of node.
    level: Description of level."""
        if hasattr(node, 'GetTitle') and hasattr(node, 'GetLocal'):
            title = node.GetTitle()
            local_path = node.GetLocal()
            if title and local_path:
                heading_level = min(level + 1, 6)
                html_parts.append(f'<h{heading_level}>{html.escape(title)}</h{heading_level}>')
                try:
                    content = chm.RetrieveObject(chm.ResolveObject(local_path))
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='ignore')
                    cleaned = clean_html(content)
                    if cleaned:
                        html_parts.append(cleaned)
                except Exception as e:
                    print(f'Warning: Could not extract topic {local_path}: {e}')
                html_parts.append('<hr style="border: 1px solid #ccc; margin: 20px 0;">')
        if hasattr(node, 'GetChildren'):
            for child in node.GetChildren():
                process_toc_node(child, level + 1)
    if isinstance(toc, list):
        for topic in toc:
            process_toc_node(topic)
    else:
        process_toc_node(toc)
    html_parts.append('</body></html>')
    return ''.join(html_parts)

def clean_html(html_content: str) -> str:
    """clean_html – clean html.

Args:
    html_content: Description of html_content."""
    if not html_content:
        return ''
    html_content = re.sub('<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub('<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    parser = CHMHTMLParser()
    try:
        parser.feed(html_content)
        body_content = parser.get_content()
        body_content = re.sub('\\n\\s*\\n', '\n\n', body_content)
        return body_content.strip()
    except Exception as e:
        print(f'Warning: HTML parsing failed: {e}')
        return html_content

def convert_chm_to_pdf(input_path: Path | str, output_path: Path | str) -> None:
    """convert_chm_to_pdf – convert chm to pdf.

Args:
    input_path: Description of input_path.
    output_path: Description of output_path."""
    print(f'Converting {input_path} to {output_path}...')
    print('Extracting HTML content from CHM...')
    html_content = extract_html_content(input_path)
    if not html_content:
        raise Exception('No content extracted from CHM file')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
        full_html = f"""<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<style>\n    @page {{\n        size: A4;\n        margin: 2cm;\n        @bottom-center {{\n            content: counter(page);\n            font-size: 10px;\n            color:\n        }}\n    }}\n    body {{\n        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;\n        line-height: 1.6;\n        font-size: 11pt;\n        color:\n        max-width: 100%;\n    }}\n    h1 {{\n        font-size: 24pt;\n        color:\n        border-bottom: 2px solid\n        padding-bottom: 10px;\n        margin-top: 30px;\n    }}\n    h2 {{\n        font-size: 20pt;\n        color:\n        border-bottom: 1px solid\n        padding-bottom: 8px;\n        margin-top: 25px;\n    }}\n    h3 {{\n        font-size: 16pt;\n        color:\n        margin-top: 20px;\n    }}\n    h4 {{\n        font-size: 14pt;\n        color:\n        margin-top: 15px;\n    }}\n    img {{\n        max-width: 100%;\n        height: auto;\n        margin: 10px 0;\n    }}\n    pre {{\n        background-color:\n        border: 1px solid\n        border-radius: 4px;\n        padding: 15px;\n        overflow-x: auto;\n        font-family: 'Courier New', monospace;\n        font-size: 9pt;\n        line-height: 1.4;\n    }}\n    code {{\n        background-color:\n        padding: 2px 4px;\n        border-radius: 3px;\n        font-family: 'Courier New', monospace;\n        font-size: 9pt;\n    }}\n    table {{\n        border-collapse: collapse;\n        width: 100%;\n        margin: 15px 0;\n    }}\n    th, td {{\n        border: 1px solid\n        padding: 8px;\n        text-align: left;\n    }}\n    th {{\n        background-color:\n        font-weight: bold;\n    }}\n    a {{\n        color:\n        text-decoration: none;\n    }}\n    blockquote {{\n        border-left: 4px solid\n        margin: 15px 0;\n        padding: 10px 20px;\n        background-color:\n    }}\n    hr {{\n        border: none;\n        border-top: 1px solid\n        margin: 20px 0;\n    }}\n</style>\n</head>\n<body>\n{html_content}\n</body>\n</html>"""
        temp_html.write(full_html)
        temp_html_path = temp_html.name
    try:
        print('Converting HTML to PDF using WeasyPrint...')
        HTML(filename=temp_html_path).write_pdf(output_path)
        print(f'PDF successfully created: {output_path}')
    finally:
        if os.path.exists(temp_html_path):
            os.unlink(temp_html_path)

def main() -> None:
    """main – main."""
    if len(sys.argv) != 2:
        print('Usage: python chm_to_pdf.py <input_file.chm>')
        print('Example: python chm_to_pdf.py documentation.chm')
        sys.exit(1)
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist")
        sys.exit(1)
    if input_path.suffix.lower() != '.chm':
        print(f"Error: Input file '{input_path}' is not a CHM file")
        sys.exit(1)
    output_path = input_path.with_suffix('.pdf')
    try:
        convert_chm_to_pdf(input_path, output_path)
    except Exception as e:
        print(f'Error during conversion: {e}')
        sys.exit(1)
if __name__ == '__main__':
    main()
