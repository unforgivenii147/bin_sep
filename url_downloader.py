#!/data/data/com.termux/files/home/.local/bin/python
"""
Download files listed in urls.txt concurrently using multiprocessing.Pool.apply_async
with a fixed pool of 8 workers. Prefer pycurl, fall back to requests. Save files under
downloads/, then remove successfully downloaded URLs from urls.txt. Use loguru for
logging, pathlib for paths, full type hints, and docstrings throughout.
"""

from __future__ import annotations

import sys
from multiprocessing.pool import AsyncResult, Pool
from pathlib import Path
from typing import List, Set, Tuple

from loguru import logger

try:
    import pycurl  # type: ignore[import-untyped]

    HAS_PYCURL: bool = True
    logger.info("Using pycurl backend")
except ImportError:
    HAS_PYCURL = False
    try:
        import requests

        logger.info("pycurl not available → falling back to requests")
    except ImportError:
        logger.error("Neither pycurl nor requests is installed!")
        logger.error("Run: pip install pycurl requests")
        sys.exit(1)

MAX_WORKERS: int = 8
DEFAULT_TIMEOUT: int = 120
URLS_FILE: Path = Path("urls.txt")
DOWNLOADS_DIR: Path = Path("downloads")


def download_file(url: str, filepath: Path, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """
    Download a single URL to filepath.

    Tries pycurl first (if available), then falls back to requests.

    Args:
        url: The URL to download.
        filepath: Destination path for the downloaded file.
        timeout: Request timeout in seconds.

    Returns:
        True if the download succeeded, False otherwise.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if HAS_PYCURL:
        try:
            with open(filepath, "wb") as f:
                c = pycurl.Curl()
                c.setopt(c.URL, url)
                c.setopt(c.WRITEDATA, f)
                c.setopt(c.TIMEOUT, timeout)
                c.setopt(c.FOLLOWLOCATION, True)
                c.setopt(c.MAXREDIRS, 5)
                c.setopt(c.USERAGENT, "Mozilla/5.0")
                c.perform()
                c.close()
            logger.success(f"Downloaded (pycurl): {filepath.name}")
            return True
        except Exception as e:
            logger.warning(
                f"pycurl failed for {filepath.name}: {e}. Trying requests..."
            )

    try:
        with requests.Session() as session:
            response = session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=timeout,
                stream=True,
                allow_redirects=True,
            )
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.success(f"Downloaded (requests): {filepath.name}")
        return True
    except Exception as e:
        logger.error(f"Failed {filepath.name}: {e}")
        return False


def parse_urls_file(urls_file: Path) -> Tuple[List[str], List[Tuple[str, Path]]]:
    """
    Parse the urls.txt file.

    Args:
        urls_file: Path to the urls.txt file.

    Returns:
        A tuple of (original_lines, download_tasks), where download_tasks is a list
        of (url, filepath) tuples for each valid URL.
    """
    original_lines: List[str] = urls_file.read_text(encoding="utf-8").splitlines()
    download_tasks: List[Tuple[str, Path]] = []

    for line in original_lines:
        stripped: str = line.strip()
        if stripped and not stripped.startswith("#"):
            url: str = stripped.split()[0]
            filename: str = (
                url.split("/")[-1].split("?")[0]
                or f"download_{len(download_tasks) + 1}"
            )
            filepath: Path = DOWNLOADS_DIR / filename
            download_tasks.append((url, filepath))

    return original_lines, download_tasks


def update_urls_file(
    urls_file: Path,
    original_lines: List[str],
    successful_urls: Set[str],
) -> int:
    """
    Rewrite urls.txt, removing lines whose URLs downloaded successfully.

    Args:
        urls_file: Path to the urls.txt file.
        original_lines: The original lines read from the file.
        successful_urls: Set of URLs that were downloaded successfully.

    Returns:
        Number of lines removed.
    """
    remaining_lines: List[str] = []
    removed_count: int = 0

    for line in original_lines:
        stripped: str = line.strip()
        if stripped and not stripped.startswith("#"):
            url: str = stripped.split()[0]
            if url in successful_urls:
                removed_count += 1
                continue
        remaining_lines.append(line)

    urls_file.write_text("\n".join(remaining_lines) + "\n", encoding="utf-8")
    return removed_count


def main() -> int:
    """
    Entry point: read urls.txt, download files concurrently, update urls.txt.

    Returns:
        Process exit code (0 on success, 1 on error).
    """
    if not URLS_FILE.exists():
        logger.error(f"{URLS_FILE} not found!")
        return 1

    original_lines, download_tasks = parse_urls_file(URLS_FILE)

    if not download_tasks:
        logger.info("No valid URLs found in urls.txt")
        return 0

    logger.info(f"Found {len(download_tasks)} files to download.\n")

    successful_urls: Set[str] = set()
    results: List[Tuple[str, AsyncResult[bool]]] = []

    with Pool(processes=MAX_WORKERS) as pool:
        for url, path in download_tasks:
            async_result: AsyncResult[bool] = pool.apply_async(
                download_file, (url, path)
            )
            results.append((url, async_result))

        for url, async_result in results:
            try:
                if async_result.get():
                    successful_urls.add(url)
            except Exception as exc:
                logger.error(f"Unexpected error with {url}: {exc}")

    removed_count: int = update_urls_file(URLS_FILE, original_lines, successful_urls)

    logger.info("=" * 40)
    logger.info("Download session completed!")
    logger.info(f"✅ Successfully downloaded : {removed_count} files")
    logger.info(
        f"❌ Remaining in urls.txt   : {len(download_tasks) - removed_count} files"
    )
    logger.info("-" * 40)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
