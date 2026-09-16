#!/data/data/com.termux/files/home/.local/bin/python
"""make_template_html.py – Make Template Html utilities.

This module provides functionality for make template html."""
from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup

def find_html_files(cwd: str='.') -> list[Path]:
    """find_html_files – find html files.

Args:
    cwd: Description of cwd.

Returns:
    list[Path]: Description of return value."""
    root_path = Path(cwd).resolve()
    html_files = [path for path in root_path.rglob('*.html') if path.name != 'template.html']
    for path in root_path.rglob('*.htm'):
        html_files.append(path)
    return sorted(html_files)

def extract_common_structure(html_files: list[Path]) -> dict:
    """extract_common_structure – extract common structure.

Args:
    html_files: Description of html_files.

Returns:
    dict: Description of return value."""
    body_classes = []
    meta_tags = []
    link_tags = []
    script_tags = []
    for path in html_files:
        try:
            with Path(path).open(encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                if soup.head:
                    meta_tags.extend((str(meta) for meta in soup.head.find_all('meta')))
                    link_tags.extend((str(link) for link in soup.head.find_all('link')))
                    script_tags.extend((str(script) for script in soup.head.find_all('script') if script.get('src')))
                if soup.body and soup.body.get('class'):
                    body_classes.extend(soup.body.get('class'))
        except Exception as e:
            print(f'Error processing {path}: {e}')
    common_meta = list(set(meta_tags))
    common_links = list(set(link_tags))
    common_scripts = list(set(script_tags))
    common_body_class = ' '.join(set(body_classes)) if body_classes else ''
    return {'meta_tags': common_meta, 'link_tags': common_links, 'script_tags': common_scripts, 'body_class': common_body_class}

def merge_html_content(html_files: list[Path]) -> str:
    """merge_html_content – merge html content.

Args:
    html_files: Description of html_files.

Returns:
    str: Description of return value."""
    merged_sections = []
    for path in html_files:
        try:
            with Path(path).open(encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                content = soup.body.decode_contents() if soup.body else str(soup)
                section_html = f'\n    <!-- Content from: {path.relative_to(Path.cwd())} -->\n    <section class="merged-content" data-source="{path.name}">\n        {content}\n    </section>\n'
                merged_sections.append(section_html)
        except Exception as e:
            print(f'Error merging {path}: {e}')
    return ''.join(merged_sections)

def create_template_html(html_files: list[Path], output_file: str='template.html', title: str='Merged HTML Template') -> bool:
    """create_template_html – create template html.

Args:
    html_files: Description of html_files.
    output_file: Description of output_file.
    title: Description of title.

Returns:
    bool: Description of return value."""
    if not html_files:
        print('No HTML files found')
        return False
    print(f'Processing {len(html_files)} HTML files...')
    structure = extract_common_structure(html_files)
    merged_content = merge_html_content(html_files)
    template = f"""\n<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{title}</title>\n    {chr(10).join(('    ' + tag for tag in structure['meta_tags']))}\n    {chr(10).join(('    ' + tag for tag in structure['link_tags']))}\n    <style>\n            body {{font-family: Arial, sans-serif;\n                line-height: 1.6;\n                margin: 0;\n                padding: 20px;\n                background-color:}}\n            .container {{max-width: 1200px;\n                margin: 0 auto;\n                background: white;\n                padding: 20px;\n                box-shadow: 0 0 10px rgba(0,0,0,0.1);}}\n            .merged-content {{margin-bottom: 40px;\n                padding: 20px;\n                border-left: 4px solid\n                background:}}\n            .merged-content::before {{content: attr(data-source);\n            display: block;\n            font-weight: bold;\n            color:\n            margin-bottom: 10px;\n            font-size: 0.9em;}}\n        h1, h2, h3 {{color:}}\n        .toc {{background:\n            padding: 20px;\n            margin-bottom: 30px;\n            border-radius: 5px;}}\n        .toc h2 {{margin-top: 0;}}\n        .toc ul {{list-style: none;\n            padding-left: 0;}}\n        .toc li {{margin: 5px 0;}}\n        .toc a {{color:\n            text-decoration: none;}}\n        .toc a:hover {{text-decoration: underline;}}\n    </style>\n    {chr(10).join(('    ' + tag for tag in structure['script_tags']))}\n</head>\n<body{(' class="' + structure['body_class'] + '"' if structure['body_class'] else '')}>\n    <div class="container">\n        <h1>{title}</h1>\n        <div class="toc">\n            <h2>Table of Contents</h2>\n            <ul>\n        {chr(10).join((f'                <li><a href="#{Path(f).stem}">{Path(f).relative_to(Path.cwd())}</a></li>' for f in html_files))}\n            </ul>\n        </div>\n{merged_content}\n    </div>\n    <script>\n        document.querySelectorAll('.toc a').forEach(anchor => {{anchor.addEventListener('click', function (e) {{e.preventDefault();\n                const target = document.querySelector(this.getAttribute('href'));\n                if (target) {{target.scrollIntoView({{ behavior: 'smooth' }});}}}});}});\n        document.querySelectorAll('.merged-content').forEach((section, index) => {{const source = section.getAttribute('data-source');\n            const id = source.replace(/\\.html?$/, '');\n            section.id = id;}});\n    </script>\n</body>\n</html>\n"""
    try:
        Path(output_file).write_text(template, encoding='utf-8')
        print(f'Template created successfully: {output_file}')
        print(f'Merged {len(html_files)} HTML files')
        return True
    except Exception as e:
        print(f'Error writing template: {e}')
        return False

def main() -> None:
    """main – main."""
    html_files = find_html_files()
    success = create_template_html(html_files, output_file='template.html', title='Merged HTML Template')
    if success:
        print('Output file: template.html')
if __name__ == '__main__':
    raise SystemExit(main())
