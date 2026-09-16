#!/data/data/com.termux/files/home/.local/bin/python
"""fontpre.py – Fontpre utilities.

This module provides functionality for fontpre."""
from __future__ import annotations
import html
import logging
import sys
from collections.abc import Generator
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
FONTEXT = frozenset({'.ttf', '.otf', '.woff', '.woff2', '.eot', '.svg'})
SAMPLE_TEXT = 'Lorem ipsum dolor sit amet\nهنر برتر از گوهر آمد پدید'
OUTPUT_FILE = 'fontpreview.html'

class FontInfo(NamedTuple):
    """FontInfo – FontInfo."""
    path: Path
    index: int
    size: int
    format: str

def get_timestamp() -> str:
    """get_timestamp – get timestamp.

Returns:
    str: Description of return value."""
    return datetime.now().isoformat(timespec='seconds')

def format_file_size(size_bytes: int) -> str:
    """format_file_size – format file size.

Args:
    size_bytes: Description of size_bytes.

Returns:
    str: Description of return value."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size_bytes < 1024.0:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024.0
    return f'{size_bytes:.1f} TB'

@lru_cache(maxsize=128)
def get_font_format(ext: str) -> str:
    """get_font_format – get font format.

Args:
    ext: Description of ext.

Returns:
    str: Description of return value."""
    format_map = {'.ttf': 'TrueType', '.otf': 'OpenType', '.woff': 'WOFF', '.woff2': 'WOFF2', '.eot': 'Embedded OpenType', '.svg': 'SVG Font'}
    return format_map.get(ext.lower(), ext.upper().lstrip('.'))

def is_font_file(path: Path) -> bool:
    """is_font_file – is font file.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    return path.is_file() and path.suffix.lower() in FONTEXT

def find_fonts_generator(roots: list[Path] | None=None) -> Generator[Path, None, None]:
    """find_fonts_generator – find fonts generator.

Args:
    roots: Description of roots.

Returns:
    Generator[Path, None, None]: Description of return value."""
    if not roots:
        roots = [Path.cwd()]
    visited = set()
    for root in roots:
        try:
            root = root.resolve()
            if not root.exists():
                logger.warning(f'Path does not exist: {root}')
                continue
            if root.is_file():
                if is_font_file(root):
                    yield root
            else:
                for path in root.rglob('*'):
                    if path in visited:
                        continue
                    visited.add(path)
                    if is_font_file(path):
                        try:
                            yield path
                        except (OSError, ValueError) as e:
                            logger.debug(f'Skipping {path}: {e}')
        except (PermissionError, OSError) as e:
            logger.warning(f'Cannot access {root}: {e}')

def collect_fonts(roots: list[Path] | None=None, max_fonts: int=10000) -> list[FontInfo]:
    """collect_fonts – collect fonts.

Args:
    roots: Description of roots.
    max_fonts: Description of max_fonts.

Returns:
    list[FontInfo]: Description of return value."""
    fonts: list[FontInfo] = []
    for i, path in enumerate(find_fonts_generator(roots), 1):
        if i > max_fonts:
            logger.warning(f'Reached maximum font limit ({max_fonts})')
            break
        try:
            stat = path.stat()
            font_info = FontInfo(path=path, index=i, size=stat.st_size, format=get_font_format(path.suffix))
            fonts.append(font_info)
        except (OSError, ValueError) as e:
            logger.debug(f'Error processing {path}: {e}')
            continue
    return sorted(fonts, key=lambda f: (f.path.parent, f.path.name))

def create_font_face(font_info: FontInfo, cwd: Path) -> str:
    """create_font_face – create font face.

Args:
    font_info: Description of font_info.
    cwd: Description of cwd.

Returns:
    str: Description of return value."""
    try:
        rel_path = font_info.path.relative_to(cwd)
        url_path = quote(rel_path.as_posix())
    except ValueError:
        url_path = quote(font_info.path.as_posix())
        if not url_path.startswith('/'):
            url_path = '/' + url_path
    font_id = f'{font_info.index:04d}'
    return f"@font-face {{\n  font-family: 'font_{font_id}';\n  src: url('{url_path}');\n  font-display: swap;\n  font-weight: normal;\n  font-style: normal;\n}}"

def create_font_section(font_info: FontInfo, cwd: Path) -> str:
    """create_font_section – create font section.

Args:
    font_info: Description of font_info.
    cwd: Description of cwd.

Returns:
    str: Description of return value."""
    font_id = f'{font_info.index:04d}'
    font_name = font_info.path.name
    try:
        display_path = font_info.path.relative_to(cwd)
    except ValueError:
        display_path = font_info.path
    escaped_name = html.escape(font_name)
    escaped_path = html.escape(str(display_path))
    escaped_sample = html.escape(SAMPLE_TEXT)
    size_str = format_file_size(font_info.size)
    return f"""\n<section>\n  <h1 style="font-family: 'font_{font_id}', serif;">\n    {escaped_name}\n    <small>({font_info.format})</small>\n  </h1>\n  <textarea\n    style="font-family: 'font_{font_id}', serif; font-size: 22px;"\n    spellcheck="false"\n    placeholder="Type to test font..."\n  >{escaped_sample}</textarea>\n  <div class="metadata">\n    <div class="metadata-item">\n      <span class="metadata-label">Path:</span>\n      <code>{escaped_path}</code>\n    </div>\n    <div class="metadata-item">\n      <span class="metadata-label">Size:</span>\n      <code>{size_str}</code>\n    </div>\n    <div class="metadata-item">\n      <span class="metadata-label">Format:</span>\n      <code>{font_info.format}</code>\n    </div>\n  </div>\n</section>"""

def generate_preview_styles(fonts: list[FontInfo], cwd: Path) -> str:
    """generate_preview_styles – generate preview styles.

Args:
    fonts: Description of fonts.
    cwd: Description of cwd.

Returns:
    str: Description of return value."""
    return '\n\n'.join((create_font_face(font, cwd) for font in fonts))

def generate_preview_sections(fonts: list[FontInfo], cwd: Path) -> str:
    """generate_preview_sections – generate preview sections.

Args:
    fonts: Description of fonts.
    cwd: Description of cwd.

Returns:
    str: Description of return value."""
    return '\n'.join((create_font_section(font, cwd) for font in fonts))

def generate_html(fonts: list[FontInfo], cwd: Path) -> str:
    """generate_html – generate html.

Args:
    fonts: Description of fonts.
    cwd: Description of cwd.

Returns:
    str: Description of return value."""
    timestamp = get_timestamp()
    html_start = f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Font Preview</title>\n<style>\n:root {{\n  --bg:\n  --text:\n  --border:\n  --accent:\n  --input-bg:\n}}\n@media (prefers-color-scheme: dark) {{\n  :root {{\n    --bg:\n    --text:\n    --border:\n    --accent:\n    --input-bg:\n  }}\n}}\n* {{\n  box-sizing: border-box;\n}}\nbody {{\n  background: var(--bg);\n  color: var(--text);\n  font-family: system-ui, -apple-system, sans-serif;\n  margin: 0 auto;\n  padding: 20px;\n  max-width: 960px;\n  transition: background 0.3s, color 0.3s;\n}}\nh1 {{\n  margin-top: 40px;\n  margin-bottom: 0.5em;\n  font-size: 1.6em;\n  border-bottom: 2px solid var(--border);\n  padding-bottom: 0.3em;\n  color: var(--accent);\n  word-break: break-word;\n}}\nh1 small {{\n  font-size: 0.6em;\n  opacity: 0.7;\n  display: inline-block;\n  margin-left: 0.5em;\n}}\ntextarea {{\n  width: 100%;\n  min-height: 100px;\n  padding: 16px;\n  margin-top: 6px;\n  border-radius: 8px;\n  border: 2px solid var(--border);\n  font-size: clamp(1em, 2vw, 1.5em);\n  resize: vertical;\n  white-space: pre-wrap;\n  background: var(--input-bg);\n  color: var(--text);\n  transition: border-color 0.3s;\n  line-height: 1.6;\n  overflow-wrap: break-word;\n}}\ntextarea:focus {{\n  outline: none;\n  border-color: var(--accent);\n}}\nsection {{\n  margin-top: 30px;\n  padding-bottom: 20px;\n  border-bottom: 1px solid var(--border);\n}}\nsection:last-of-type {{\n  border-bottom: none;\n}}\n.note {{\n  color: var(--text);\n  margin-top: 8px;\n  font-size: 0.85em;\n  font-family: monospace;\n  word-break: break-all;\n  opacity: 0.75;\n}}\nfooter {{\n  margin-top: 40px;\n  text-align: center;\n  color: var(--text);\n  font-size: 0.9em;\n  opacity: 0.6;\n}}\n.metadata {{\n  display: flex;\n  gap: 16px;\n  font-size: 0.9em;\n  margin-top: 8px;\n  flex-wrap: wrap;\n}}\n.metadata-item {{\n  display: flex;\n  align-items: center;\n  gap: 4px;\n}}\n.metadata-label {{\n  opacity: 0.7;\n  font-weight: 500;\n}}\n</style>\n</head>\n<body>\n<h1>Font Preview Generator</h1>\n<p class="note">Generated: {timestamp}</p>\n<style>\n'
    html_middle = '\n</style>\n'
    html_end = '\n<footer>\nGenerated by Font Preview Generator | Python 3.12+ | Pathlib optimized\n</footer>\n</body>\n</html>\n'
    if not fonts:
        return f'{html_start}{html_middle}{html_end}'
    styles = generate_preview_styles(fonts, cwd)
    sections = generate_preview_sections(fonts, cwd)
    return f'{html_start}{styles}{html_middle}{sections}{html_end}'

def write_preview(html_content: str, output_path: Path) -> bool:
    """write_preview – write preview.

Args:
    html_content: Description of html_content.
    output_path: Description of output_path.

Returns:
    bool: Description of return value."""
    try:
        temp_path = output_path.with_suffix('.tmp')
        temp_path.write_text(html_content, encoding='utf-8')
        temp_path.replace(output_path)
        return True
    except OSError as e:
        logger.error(f'Failed to write {output_path}: {e}')
        return False

def validate_paths(paths: list[str] | None) -> list[Path]:
    """validate_paths – validate paths.

Args:
    paths: Description of paths.

Returns:
    list[Path]: Description of return value."""
    if not paths:
        return [Path.cwd()]
    validated = []
    for path_str in paths:
        try:
            path = Path(path_str).expanduser().resolve()
            if path.exists():
                validated.append(path)
            else:
                logger.warning(f'Path does not exist: {path_str}')
        except (OSError, ValueError) as e:
            logger.warning(f"Invalid path '{path_str}': {e}")
    return validated if validated else [Path.cwd()]

def main(input_paths: list[str] | None=None, output_file: str=OUTPUT_FILE) -> int:
    """main – main.

Args:
    input_paths: Description of input_paths.
    output_file: Description of output_file.

Returns:
    int: Description of return value."""
    cwd = Path.cwd()
    valid_paths = validate_paths(input_paths)
    print(f'Searching for fonts in {len(valid_paths)} location(s)...')
    fonts = collect_fonts(valid_paths)
    if not fonts:
        logger.warning(f"No font files found. Supported formats: {', '.join(sorted(FONTEXT))}")
        return 1
    print(f'Found {len(fonts)} font(s)')
    print('Generating preview HTML...')
    html_content = generate_html(fonts, cwd)
    output_path = cwd / output_file
    print(f'Writing to {output_path}...')
    if write_preview(html_content, output_path):
        print(f'✓ Successfully generated {output_path}')
        print(f'  File size: {format_file_size(output_path.stat().st_size)}')
        return 0
    else:
        return 1

def cli_main() -> None:
    """cli_main – cli main."""
    import argparse
    parser = argparse.ArgumentParser(description='Generate interactive HTML preview for font files', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  fontpreview.py\n  fontpreview.py ./fonts/\n  fontpreview.py ./fonts/ ~/Downloads/ ./local/\n  fontpreview.py -o my_preview.html ./fonts/\n        ')
    parser.add_argument('paths', nargs='*', help='File or directory paths to process (default: current directory)')
    parser.add_argument('-o', '--output', default=OUTPUT_FILE, help=f'Output HTML filename (default: {OUTPUT_FILE})')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    try:
        exit_code = main(args.paths if args.paths else None, args.output)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning('Operation cancelled by user')
        sys.exit(130)
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        sys.exit(1)
if __name__ == '__main__':
    cli_main()
