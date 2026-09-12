#!/data/data/com.termux/files/home/.local/bin/python
"""Compress files recursively with gzip at maximum compression (level 9).

Uses a multiprocessing pool of 8 workers to compress every file found under the
given directories (default: current directory), skipping already-compressed
archive extensions and any user-specified extensions. Deletes each original file
after a successful gzip write, prints a per-file table and a final summary via
loguru, and reports total counts, sizes, compression ratio, and elapsed time.
"""

import argparse
import gzip
import time
from datetime import timedelta
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Final

from dh import fsz
from loguru import logger

BUFFER_SIZE: Final[int] = 256 * 1024
WORKERS: Final[int] = 8
DEFAULT_SKIP_EXTENSIONS: Final[set[str]] = {
    ".gz",
    ".zip",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".tar",
}


class CompressionStats:
    """Aggregate counters and byte totals for a compression run."""

    total_files: int
    successful: int
    failed: int
    total_original_size: int
    total_compressed_size: int

    def __init__(self) -> None:
        """Initialize all counters and byte totals to zero."""
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.total_original_size = 0
        self.total_compressed_size = 0

    def add_success(self, original_size: int, compressed_size: int) -> None:
        """Record a successfully compressed file and its sizes."""
        self.total_files += 1
        self.successful += 1
        self.total_original_size += original_size
        self.total_compressed_size += compressed_size

    def add_failure(self) -> None:
        """Record a file that failed to compress."""
        self.total_files += 1
        self.failed += 1


def stream_copy(src_file: Any, dst_file: Any, chunk_size: int = BUFFER_SIZE) -> None:
    """Copy all bytes from ``src_file`` to ``dst_file`` in fixed-size chunks."""
    while True:
        chunk: bytes = src_file.read(chunk_size)
        if not chunk:
            break
        dst_file.write(chunk)


def compress_file(file_path: Path) -> tuple[Path, bool, int, int, str]:
    """Gzip ``file_path`` to ``<name>.gz``, delete the original on success.

    Returns a tuple of ``(path, success, original_size, compressed_size, error)``.
    """
    gz_path: Path = file_path.with_suffix(file_path.suffix + ".gz")
    try:
        original_size: int = file_path.stat().st_size
        with (
            open(file_path, "rb") as f_in,
            gzip.open(gz_path, "wb", compresslevel=9) as f_out,
        ):
            stream_copy(f_in, f_out)
        compressed_size: int = gz_path.stat().st_size
        file_path.unlink()
        return (file_path, True, original_size, compressed_size, "")
    except Exception as e:  # noqa: BLE001
        if gz_path.exists():
            gz_path.unlink()
        return (file_path, False, 0, 0, str(e))


def find_files_to_compress(
    directories: list[Path], skip_extensions: set[str] | None = None
) -> list[Path]:
    """Return all files under ``directories`` whose suffix is not skipped."""
    if skip_extensions is None:
        skip_extensions = set(DEFAULT_SKIP_EXTENSIONS)
    files_to_compress: list[Path] = []
    for directory in directories:
        if not directory.exists():
            logger.warning("Directory '{}' does not exist, skipping...", directory)
            continue
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix not in skip_extensions:
                files_to_compress.append(file_path)
    return files_to_compress


def format_ratio(original: int, compressed: int) -> str:
    """Return the percentage of bytes saved as a formatted string."""
    if original == 0:
        return "N/A"
    ratio: float = (1 - compressed / original) * 100
    return f"{ratio:.1f}%"


def main() -> int:
    """Parse arguments, compress matching files, and print a summary."""
    parser = argparse.ArgumentParser(
        description="Compress files recursively with gzip (maximum compression)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s dir1 dir2
  %(prog)s /path/to/dir1 /path/to/dir2
        """,
    )
    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to process (default: current directory)",
    )
    parser.add_argument(
        "--exclude",
        "-e",
        nargs="+",
        default=[],
        help="Additional file extensions to exclude (e.g., .pdf .jpg)",
    )
    args = parser.parse_args()
    directories: list[Path] = [Path(d).resolve() for d in args.directories]

    logger.info("=" * 40)
    logger.info("🔍 GZIP Compression Tool (Maximum Compression - Level 9)".center(70))
    logger.info("-" * 40)
    logger.info("📂 Processing directories:")
    for d in directories:
        logger.info("   • {}", d)

    skip_extensions: set[str] = set(DEFAULT_SKIP_EXTENSIONS)
    if args.exclude:
        for ext in args.exclude:
            if not ext.startswith("."):
                ext = "." + ext
            skip_extensions.add(ext)
        logger.info("🚫 Excluding extensions: {}", ", ".join(sorted(skip_extensions)))

    logger.info("🔎 Scanning for files...")
    start_time: float = time.time()
    files_to_compress: list[Path] = find_files_to_compress(directories, skip_extensions)
    if not files_to_compress:
        logger.success("✅ No files found to compress!")
        return 0

    logger.info("📊 Found {} file(s) to compress", len(files_to_compress))
    logger.info("-" * 40)
    logger.info(
        f"{'File':<50} {'Original':>10} {'Compressed':>10} {'Ratio':>8} {'Status':>10}"
    )
    logger.info("-" * 40)

    stats: CompressionStats = CompressionStats()
    with Pool(processes=WORKERS) as pool:
        async_results: list[Any] = [
            pool.apply_async(compress_file, (file_path,))
            for file_path in files_to_compress
        ]
        for async_result in async_results:
            file_path, success, orig_size, comp_size, error = async_result.get()
            try:
                rel_path: Path = file_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = file_path
            display_path: str = str(rel_path)
            if len(display_path) > 47:
                display_path = "..." + display_path[-44:]
            if success:
                stats.add_success(orig_size, comp_size)
                status_symbol: str = "✅"
                logger.info(
                    f"{display_path:<50} {fsz(orig_size):>10} "
                    f"{fsz(comp_size):>10} "
                    f"{format_ratio(orig_size, comp_size):>8} "
                    f"{status_symbol:>10}"
                )
            else:
                stats.add_failure()
                status_symbol = "❌"
                logger.info(
                    f"{display_path:<50} {'N/A':>10} {'N/A':>10} "
                    f"{'N/A':>8} {status_symbol:>10}"
                )
                if error:
                    logger.warning("   ⚠ Error: {}", error)

    elapsed_time: float = time.time() - start_time
    logger.info("=" * 40)
    logger.info("📊 COMPRESSION SUMMARY".center(70))
    logger.info("-" * 40)
    logger.info("  Total files processed:     {}", stats.total_files)
    logger.info("  Successfully compressed:   {} ✅", stats.successful)
    logger.info("  Failed compressions:       {} ❌", stats.failed)
    logger.info("  Original total size:       {}", fsz(stats.total_original_size))
    logger.info("  Compressed total size:     {}", fsz(stats.total_compressed_size))
    if stats.total_original_size > 0:
        overall_ratio: float = (
            1 - stats.total_compressed_size / stats.total_original_size
        ) * 100
        space_saved: int = stats.total_original_size - stats.total_compressed_size
        logger.info("  Overall compression ratio: {:.1f}%", overall_ratio)
        logger.info("  Space saved:               {}", fsz(space_saved))
    logger.info(
        "  Time elapsed:               {}",
        timedelta(seconds=int(elapsed_time)),
    )
    logger.info("-" * 40)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
