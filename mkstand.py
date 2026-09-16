#!/data/data/com.termux/files/home/.local/bin/python
"""mkstand.py – Mkstand utilities.

This module provides functionality for mkstand."""
from __future__ import annotations
from typing import Any
import base64
import mimetypes
import multiprocessing as mp
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse
import requests
from bs4 import BeautifulSoup
WORKERS = 8
REMOTE_SIZE_LIMIT = 5 * 1024 * 1024
USER_AGENT = 'Mozilla/5.0 (compatible; StandaloneHTML/2.0)'
REMOTE_IMAGE_EXTENSIONS = {'.apng', '.avif', '.bmp', '.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.webp'}
HTML_EXTENSIONS = {'.html', '.htm'}
ASSET_ATTRIBUTES = {'link': ('href',), 'script': ('src',), 'img': ('src',), 'source': ('src',), 'video': ('src', 'poster'), 'audio': ('src',), 'object': ('data',), 'embed': ('src',), 'input': ('src',), 'track': ('src',)}
_WORKER_ASSET_CACHE: dict[str, tuple[bytes, str]] = {}

def make_session() -> requests.Session:
    """make_session – make session.

Returns:
    requests.Session: Description of return value."""
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    return session

def is_remote_url(value: str | None) -> bool:
    """is_remote_url – is remote url.

Args:
    value: Description of value.

Returns:
    bool: Description of return value."""
    return bool(value and value.startswith(('http://', 'https://')))

def is_data_url(value: str | None) -> bool:
    """is_data_url – is data url.

Args:
    value: Description of value.

Returns:
    bool: Description of return value."""
    return bool(value and value.lower().startswith('data:'))

def clean_url(value: str) -> str:
    """clean_url – clean url.

Args:
    value: Description of value.

Returns:
    str: Description of return value."""
    value = value.strip()
    value, _fragment = urldefrag(value)
    return value

def resolve_url(value: str, base: Path | str) -> str:
    """resolve_url – resolve url.

Args:
    value: Description of value.
    base: Description of base.

Returns:
    str: Description of return value."""
    value = clean_url(value)
    if value.startswith('//'):
        return 'https:' + value
    if value.startswith(('http://', 'https://', 'data:', '#')):
        return value
    if isinstance(base, Path):
        if value.startswith('/'):
            return str(Path(value).resolve())
        return str((base / unquote(value)).resolve())
    return urljoin(str(base), value)

def guess_mime(url: str, content_type: str | None=None) -> str:
    """guess_mime – guess mime.

Args:
    url: Description of url.
    content_type: Description of content_type.

Returns:
    str: Description of return value."""
    if content_type:
        mime = content_type.split(';', 1)[0].strip().lower()
        if mime:
            return mime
    path = urlparse(url).path
    mime, _encoding = mimetypes.guess_type(path)
    return mime or 'application/octet-stream'

def is_image_url(url: str, content_type: str | None=None) -> bool:
    """is_image_url – is image url.

Args:
    url: Description of url.
    content_type: Description of content_type.

Returns:
    bool: Description of return value."""
    if content_type:
        return content_type.lower().split(';', 1)[0].startswith('image/')
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix in REMOTE_IMAGE_EXTENSIONS

def to_data_uri(content: bytes, mime: str) -> str:
    """to_data_uri – to data uri.

Args:
    content: Description of content.
    mime: Description of mime.

Returns:
    str: Description of return value."""
    encoded = base64.b64encode(content).decode('ascii')
    return f'data:{mime};base64,{encoded}'

def get_remote_size(session: requests.Session, url: str) -> tuple[int | None, str | None]:
    """get_remote_size – get remote size.

Args:
    session: Description of session.
    url: Description of url.

Returns:
    tuple[int | None, str | None]: Description of return value."""
    try:
        response = session.head(url, timeout=15, allow_redirects=True)
        content_length = response.headers.get('Content-Length')
        content_type = response.headers.get('Content-Type')
        size = None
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                size = None
        return (size, content_type)
    except requests.RequestException:
        return (None, None)

def ask_download_confirmation(url: str, size: int) -> bool:
    """ask_download_confirmation – ask download confirmation.

Args:
    url: Description of url.
    size: Description of size.

Returns:
    bool: Description of return value."""
    size_mb = size / (1024 * 1024)
    print()
    print(f'⚠ Remote file is {size_mb:.2f} MiB:')
    print(f'  {url}')
    answer = input('Download it? [y/N]: ').strip().lower()
    return answer in {'y', 'yes'}

def download_remote_assets(urls: Iterable[str]) -> dict[str, tuple[bytes, str]]:
    """download_remote_assets – download remote assets.

Args:
    urls: Description of urls.

Returns:
    dict[str, tuple[bytes, str]]: Description of return value."""
    session = make_session()
    cache: dict[str, tuple[bytes, str]] = {}
    for url in sorted(set(urls)):
        size, content_type = get_remote_size(session, url)
        if is_image_url(url, content_type):
            print(f'  ⊘ skipped remote image: {url}')
            continue
        if size is not None and size >= REMOTE_SIZE_LIMIT and (not ask_download_confirmation(url, size)):
            print(f'  ⊘ skipped by user: {url}')
            continue
        try:
            response = session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            final_url = clean_url(response.url)
            response_type = response.headers.get('Content-Type')
            mime = guess_mime(final_url, response_type)
            actual_size = len(response.content)
            if actual_size >= REMOTE_SIZE_LIMIT and size is None:
                if not ask_download_confirmation(url, actual_size):
                    print(f'  ⊘ skipped by user: {url}')
                    continue
            if is_image_url(final_url, response_type):
                print(f'  ⊘ skipped remote image: {url}')
                continue
            asset = (response.content, mime)
            cache[url] = asset
            cache[final_url] = asset
            print(f'  ↓ downloaded once: {url}')
        except requests.RequestException as exc:
            print(f'  ⚠ failed to download {url}: {exc}')
    return cache
CSS_URL_RE = re.compile('url\\(\\s*[\\"\']?([^\\"\')]+?)[\\"\']?\\s*\\)', flags=re.IGNORECASE)
CSS_IMPORT_RE = re.compile('@import\\s+(?:url\\(\\s*)?[\\"\']?([^\\"\')\\s;]+)[\\"\']?\\s*\\)?', flags=re.IGNORECASE)

def add_remote_url(urls: set[str], value: str | None, base: Path | str) -> None:
    """add_remote_url – add remote url.

Args:
    urls: Description of urls.
    value: Description of value.
    base: Description of base."""
    if not value:
        return
    value = value.strip().strip('"\'')
    if not value or is_data_url(value) or value.startswith('#'):
        return
    resolved = resolve_url(value, base)
    if is_remote_url(resolved):
        urls.add(clean_url(resolved))

def collect_css_urls(css_text: str, base: Path | str, urls: set[str]) -> list[tuple[str, str]]:
    """collect_css_urls – collect css urls.

Args:
    css_text: Description of css_text.
    base: Description of base.
    urls: Description of urls.

Returns:
    list[tuple[str, str]]: Description of return value."""
    imported_stylesheets: list[tuple[str, str]] = []
    for match in CSS_IMPORT_RE.finditer(css_text):
        value = match.group(1).strip()
        resolved = resolve_url(value, base)
        if is_remote_url(resolved):
            urls.add(clean_url(resolved))
            imported_stylesheets.append((clean_url(resolved), clean_url(resolved)))
        elif isinstance(base, Path):
            local_css = Path(resolved)
            if local_css.is_file():
                imported_stylesheets.append((str(local_css), str(local_css)))
    for match in CSS_URL_RE.finditer(css_text):
        add_remote_url(urls, match.group(1), base)
    return imported_stylesheets

def collect_remote_assets(html_path: Path) -> set[str]:
    """collect_remote_assets – collect remote assets.

Args:
    html_path: Description of html_path.

Returns:
    set[str]: Description of return value."""
    urls: set[str] = set()
    css_to_scan: list[tuple[str, Path | str]] = []
    scanned_css: set[str] = set()
    try:
        html_text = html_path.read_text(encoding='utf-8-sig', errors='replace')
    except OSError as exc:
        print(f'⚠ cannot scan {html_path}: {exc}')
        return urls
    soup = BeautifulSoup(html_text, 'html.parser')
    for tag_name, attributes in ASSET_ATTRIBUTES.items():
        for tag in soup.find_all(tag_name):
            for attribute in attributes:
                value = tag.get(attribute)
                if not value:
                    continue
                resolved = resolve_url(value, html_path.parent)
                if tag_name == 'link' and 'stylesheet' in {item.lower() for item in (tag.get('rel', []) if isinstance(tag.get('rel', []), list) else [tag.get('rel')]) if item}:
                    if is_remote_url(resolved):
                        urls.add(clean_url(resolved))
                        css_to_scan.append((clean_url(resolved), clean_url(resolved)))
                    else:
                        local_css = Path(resolved)
                        if local_css.is_file():
                            css_to_scan.append((str(local_css), local_css))
                    continue
                add_remote_url(urls, value, html_path.parent)
    for tag in soup.find_all(srcset=True):
        for item in tag['srcset'].split(','):
            candidate = item.strip().split()
            if candidate:
                add_remote_url(urls, candidate[0], html_path.parent)
    for style in soup.find_all('style'):
        css_to_scan.extend(collect_css_urls(style.get_text(), html_path.parent, urls))
    for tag in soup.find_all(style=True):
        collect_css_urls(tag['style'], html_path.parent, urls)
    session = make_session()
    while css_to_scan:
        css_identifier, _css_base = css_to_scan.pop()
        if css_identifier in scanned_css:
            continue
        scanned_css.add(css_identifier)
        try:
            if is_remote_url(css_identifier):
                response = session.get(css_identifier, timeout=30, allow_redirects=True)
                response.raise_for_status()
                css_text = response.content.decode('utf-8', errors='replace')
                actual_base: Path | str = clean_url(response.url)
            else:
                css_path = Path(css_identifier)
                css_text = css_path.read_text(encoding='utf-8', errors='replace')
                actual_base = css_path.parent
            css_to_scan.extend(collect_css_urls(css_text, actual_base, urls))
        except (OSError, requests.RequestException) as exc:
            print(f'⚠ cannot scan CSS {css_identifier}: {exc}')
    return urls

def fetch_asset(value: str | None, base_dir: Path, asset_cache: dict[str, tuple[bytes, str]]) -> Any:
    """fetch_asset – fetch asset.

Args:
    value: Description of value.
    base_dir: Description of base_dir.
    asset_cache: Description of asset_cache."""
    if not value or is_data_url(value) or value.startswith('#'):
        return (None, None)
    resolved = resolve_url(value, base_dir)
    if is_remote_url(resolved):
        if is_image_url(resolved):
            print(f'  ⊘ skipped remote image: {value}')
            return (None, None)
        asset = asset_cache.get(resolved)
        if asset is None:
            return (None, None)
        print(f'  ⟳ reused cached asset: {resolved}')
        return asset
    local_path = Path(resolved)
    if not local_path.is_file():
        print(f'  ⚠ local file not found: {local_path}')
        return (None, None)
    try:
        content = local_path.read_bytes()
        mime = guess_mime(str(local_path))
        return (content, mime)
    except OSError as exc:
        print(f'  ⚠ cannot read {local_path}: {exc}')
        return (None, None)

def process_css(css_text: str, base_dir: Path, asset_cache: dict[str, tuple[bytes, str]]) -> str:
    """process_css – process css.

Args:
    css_text: Description of css_text.
    base_dir: Description of base_dir.
    asset_cache: Description of asset_cache.

Returns:
    str: Description of return value."""

    def replace_import(match: re.Match) -> str:
        """replace_import – replace import.

Args:
    match: Description of match.

Returns:
    str: Description of return value."""
        original = match.group(0)
        value = match.group(1).strip()
        content, _mime = fetch_asset(value, base_dir, asset_cache)
        if content is None:
            return original
        imported_css = content.decode('utf-8', errors='replace')
        imported_base = base_dir
        if is_remote_url(value):
            imported_base = Path('.')
        else:
            imported_base = Path(resolve_url(value, base_dir)).parent
        return process_css(imported_css, imported_base, asset_cache)
    css_text = CSS_IMPORT_RE.sub(replace_import, css_text)

    def replace_url(match: re.Match) -> str:
        """replace_url – replace url.

Args:
    match: Description of match.

Returns:
    str: Description of return value."""
        original = match.group(0)
        value = match.group(1).strip()
        if value.startswith(('#', 'data:')):
            return original
        resolved = resolve_url(value, base_dir)
        if is_remote_url(resolved) and is_image_url(resolved):
            print(f'  ⊘ skipped remote CSS image: {resolved}')
            return original
        content, mime = fetch_asset(value, base_dir, asset_cache)
        if content is None:
            return original
        return f'url("{to_data_uri(content, mime)}")'
    return CSS_URL_RE.sub(replace_url, css_text)

def process_srcset(srcset: str, base_dir: Path, asset_cache: dict[str, tuple[bytes, str]]) -> str:
    """process_srcset – process srcset.

Args:
    srcset: Description of srcset.
    base_dir: Description of base_dir.
    asset_cache: Description of asset_cache.

Returns:
    str: Description of return value."""
    output: list[str] = []
    for item in srcset.split(','):
        item = item.strip()
        if not item:
            continue
        tokens = item.split()
        value = tokens[0]
        descriptor = ' '.join(tokens[1:])
        resolved = resolve_url(value, base_dir)
        if is_remote_url(resolved) and is_image_url(resolved):
            print(f'  ⊘ skipped remote srcset image: {resolved}')
            output.append(item)
            continue
        content, mime = fetch_asset(value, base_dir, asset_cache)
        if content is None:
            output.append(item)
            continue
        data_uri = to_data_uri(content, mime)
        output.append(f'{data_uri} {descriptor}' if descriptor else data_uri)
    return ', '.join(output)

def replace_attribute_asset(tag: Any, attribute: str, base_dir: Path, asset_cache: dict[str, tuple[bytes, str]]) -> None:
    """replace_attribute_asset – replace attribute asset.

Args:
    tag: Description of tag.
    attribute: Description of attribute.
    base_dir: Description of base_dir.
    asset_cache: Description of asset_cache."""
    value = tag.get(attribute)
    if not value or is_data_url(value):
        return
    resolved = resolve_url(value, base_dir)
    if is_remote_url(resolved) and is_image_url(resolved):
        print(f'  ⊘ skipped remote image: {resolved}')
        return
    content, mime = fetch_asset(value, base_dir, asset_cache)
    if content is not None:
        tag[attribute] = to_data_uri(content, mime)

def make_standalone(html_path_string: str) -> bool:
    """make_standalone – make standalone.

Args:
    html_path_string: Description of html_path_string.

Returns:
    bool: Description of return value."""
    html_path = Path(html_path_string).resolve()
    base_dir = html_path.parent
    asset_cache = _WORKER_ASSET_CACHE
    try:
        html_text = html_path.read_text(encoding='utf-8-sig', errors='replace')
    except OSError as exc:
        print(f'ERROR: cannot read {html_path}: {exc}')
        return False
    print(f'Processing: {html_path}')
    soup = BeautifulSoup(html_text, 'html.parser')
    for link in soup.find_all('link', rel=True):
        rels = link.get('rel', [])
        rels = rels if isinstance(rels, list) else [rels]
        rels = {str(item).lower() for item in rels if item}
        if 'stylesheet' not in rels:
            continue
        href = link.get('href')
        content, _mime = fetch_asset(href, base_dir, asset_cache)
        if content is None:
            continue
        css = content.decode('utf-8', errors='replace')
        css = process_css(css, base_dir, asset_cache)
        style = soup.new_tag('style')
        style.string = css
        link.replace_with(style)
    for link in soup.find_all('link', href=True):
        rels = link.get('rel', [])
        rels = rels if isinstance(rels, list) else [rels]
        rels = {str(item).lower() for item in rels if item}
        if 'stylesheet' in rels or 'manifest' in rels:
            continue
        replace_attribute_asset(link, 'href', base_dir, asset_cache)
    for script in soup.find_all('script', src=True):
        content, _mime = fetch_asset(script.get('src'), base_dir, asset_cache)
        if content is None:
            continue
        javascript = content.decode('utf-8', errors='replace')
        javascript = re.sub('\\n?//#\\s*sourceMappingURL=.*', '', javascript)
        javascript = re.sub('</script', '<\\\\/script', javascript, flags=re.IGNORECASE)
        del script['src']
        script.string = javascript
    for img in soup.find_all('img', src=True):
        replace_attribute_asset(img, 'src', base_dir, asset_cache)
    for tag in soup.find_all(srcset=True):
        tag['srcset'] = process_srcset(tag['srcset'], base_dir, asset_cache)
    for tag_name, attributes in ASSET_ATTRIBUTES.items():
        if tag_name in {'link', 'script', 'img'}:
            continue
        for tag in soup.find_all(tag_name):
            for attribute in attributes:
                replace_attribute_asset(tag, attribute, base_dir, asset_cache)
    for style in soup.find_all('style'):
        css = style.get_text()
        if css:
            css = re.sub('^\\s*<!--\\s*', '', css)
            css = re.sub('\\s*-->\\s*$', '', css)
            style.string = process_css(css, base_dir, asset_cache)
    for tag in soup.find_all(style=True):
        if tag['style']:
            tag['style'] = process_css(tag['style'], base_dir, asset_cache)
    try:
        html_path.write_text(str(soup), encoding='utf-8')
    except OSError as exc:
        print(f'ERROR: cannot write {html_path}: {exc}')
        return False
    print(f'✓ Done: {html_path}')
    return True

def init_worker(asset_cache: dict[str, tuple[bytes, str]]) -> None:
    """init_worker – init worker.

Args:
    asset_cache: Description of asset_cache."""
    global _WORKER_ASSET_CACHE
    _WORKER_ASSET_CACHE = asset_cache

def find_html_files(inputs: list[str]) -> list[Path]:
    """find_html_files – find html files.

Args:
    inputs: Description of inputs.

Returns:
    list[Path]: Description of return value."""
    paths = [Path(value).resolve() for value in inputs] if inputs else [Path.cwd()]
    results: set[Path] = set()
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in HTML_EXTENSIONS:
                results.add(path)
        elif path.is_dir():
            for item in path.rglob('*'):
                if item.is_file() and item.suffix.lower() in HTML_EXTENSIONS:
                    results.add(item)
        else:
            print(f'⚠ input does not exist: {path}')
    return sorted(results)

def main() -> int:
    """main – main.

Returns:
    int: Description of return value."""
    html_files = find_html_files(sys.argv[1:])
    if not html_files:
        print('No HTML files found.')
        return 1
    print(f'Found {len(html_files)} HTML file(s).')
    print('Scanning for remote assets...')
    all_remote_urls: set[str] = set()
    for html_path in html_files:
        all_remote_urls.update(collect_remote_assets(html_path))
    print(f'Found {len(all_remote_urls)} unique remote asset URL(s).')
    asset_cache = download_remote_assets(all_remote_urls)
    print(f'Cached {len(asset_cache)} remote asset reference(s).')
    print(f'Processing with {WORKERS} workers...')
    with mp.Pool(processes=WORKERS, initializer=init_worker, initargs=(asset_cache,)) as pool:
        jobs = [pool.apply_async(make_standalone, (str(html_path),)) for html_path in html_files]
        results = []
        for job in jobs:
            try:
                results.append(job.get())
            except Exception as exc:
                print(f'⚠ worker failed: {exc}')
                results.append(False)
    successful = sum((bool(result) for result in results))
    print()
    print(f'Processed {successful}/{len(html_files)} file(s).')
    return 0 if successful == len(html_files) else 1
if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
