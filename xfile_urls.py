#!/data/data/com.termux/files/home/.local/bin/python
"""xfile_urls.py – Xfile Urls utilities.

This module provides functionality for xfile urls."""
from __future__ import annotations
import argparse
import hashlib
import os
import re
from multiprocessing import Pool
from pathlib import Path
from urllib.parse import unquote, urlparse
import requests
ALLOWED_EXTENSIONS = {'.css', '.ttf', '.woff', '.woff2', '.pdf'}

def clean_url(url: str) -> str:
    """clean_url – clean url.

Args:
    url: Description of url.

Returns:
    str: Description of return value."""
    url = url.strip().strip('"\'<>(),;')
    return url

def is_target_url(url: str) -> bool:
    """is_target_url – is target url.

Args:
    url: Description of url.

Returns:
    bool: Description of return value."""
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path).lower()
        return any((path.endswith(extension) for extension in ALLOWED_EXTENSIONS))
    except ValueError:
        return False

def extract_urls(input_file: str, output_file: str) -> list[str]:
    """extract_urls – extract urls.

Args:
    input_file: Description of input_file.
    output_file: Description of output_file.

Returns:
    list[str]: Description of return value."""
    url_pattern = re.compile('https?://[^\\s\\"\'<>]+', re.IGNORECASE)
    found_urls = set()
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as source:
        for line in source:
            for match in url_pattern.findall(line):
                url = clean_url(match)
                if is_target_url(url):
                    found_urls.add(url)
    sorted_urls = sorted(found_urls)
    with open(output_file, 'w', encoding='utf-8') as destination:
        for url in sorted_urls:
            destination.write(url + '\n')
    return sorted_urls

def filename_from_url(url: str) -> str:
    """filename_from_url – filename from url.

Args:
    url: Description of url.

Returns:
    str: Description of return value."""
    parsed = urlparse(url)
    name = os.path.basename(unquote(parsed.path))
    if not name or '.' not in name:
        name = 'downloaded_file'
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()[:10]
    stem, suffix = os.path.splitext(name)
    safe_stem = re.sub('[^A-Za-z0-9._-]', '_', stem)
    return f'{safe_stem}_{url_hash}{suffix}'

def download_one(task: tuple[str, str]) -> tuple[str, bool, str]:
    """download_one – download one.

Args:
    task: Description of task.

Returns:
    tuple[str, bool, str]: Description of return value."""
    url, output_dir = task
    filename = filename_from_url(url)
    destination = Path(output_dir) / filename
    try:
        response = requests.get(url, timeout=30, allow_redirects=True, headers={'User-Agent': 'url-file-downloader/1.0'})
        response.raise_for_status()
        destination.write_bytes(response.content)
        return (url, True, str(destination))
    except requests.RequestException as error:
        return (url, False, str(error))
    except OSError as error:
        return (url, False, str(error))

def download_files(urls: list[str], output_dir: str, workers: int) -> None:
    """download_files – download files.

Args:
    urls: Description of urls.
    output_dir: Description of output_dir.
    workers: Description of workers."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    tasks = [(url, output_dir) for url in urls]
    with Pool(processes=workers) as pool:
        for url, success, result in pool.imap_unordered(download_one, tasks):
            if success:
                print(f'[OK]   {url} -> {result}')
            else:
                print(f'[FAIL] {url} -> {result}')

def main() -> None:
    """main – main."""
    parser = argparse.ArgumentParser(description='Extract CSS, font, and PDF URLs from a text file.')
    parser.add_argument('-i', '--input', default='urls.txt', help='Input file containing URLs or HTML text (default: urls.txt)')
    parser.add_argument('-o', '--output', default='file_urls.txt', help='Output file for extracted URLs (default: file_urls.txt)')
    parser.add_argument('-d', '--download', nargs='?', const='downloads', metavar='DIRECTORY', help='Download extracted files into DIRECTORY. If no directory is supplied, use ./downloads.')
    parser.add_argument('-w', '--workers', type=int, default=os.cpu_count() or 4, help=f'Number of multiprocessing workers (default: {os.cpu_count() or 4})')
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be at least 1')
    urls = extract_urls(args.input, args.output)
    print(f'Extracted {len(urls)} matching URLs to {args.output}')
    if args.download is not None and urls:
        download_files(urls, args.download, args.workers)
if __name__ == '__main__':
    raise SystemExit(main())
