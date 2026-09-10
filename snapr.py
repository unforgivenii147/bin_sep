#!/data/data/com.termux/files/home/.local/bin/python
"""
Generate a Python CLI script that compresses or decompresses files in a directory using Snappy via cramjam, with optional tarring of subdirectories, multiprocessing.Pool.apply_async concurrency using a fixed pool of 8 workers, loguru logging, pathlib path handling, full type hints, and docstrings.
"""

import argparse
import multiprocessing
import shutil
import sys
import tarfile
from pathlib import Path
from typing import Any, Optional, Tuple

import cramjam  # type: ignore[import-untyped]
from loguru import logger

COMPRESSED_EXT: str = ".snappy"
POOL_SIZE: int = 8


def compress_file(file_path: Path, remove_original: bool = True) -> Tuple[bool, str]:
    """Compress a single file using Snappy and optionally remove the original.

    Args:
        file_path: Path to the file to compress.
        remove_original: If True, delete the original file after compression.

    Returns:
        A tuple of (success, message).
    """
    try:
        compressed_path: Path = file_path.with_suffix(file_path.suffix + COMPRESSED_EXT)
        with open(file_path, "rb") as f:
            data: bytes = f.read()
        compressed_data: bytes = bytes(cramjam.snappy.compress(data))
        with open(compressed_path, "wb") as f:
            f.write(compressed_data)
        if remove_original:
            file_path.unlink()
        original_size: int = len(data)
        compressed_size: int = len(compressed_data)
        ratio: float = (
            (compressed_size / original_size * 100) if original_size > 0 else 0.0
        )
        logger.info(
            f"Compressed: {file_path} -> {compressed_path} "
            f"({original_size} -> {compressed_size} bytes, {ratio:.1f}%)"
        )
        return True, f"Compressed {file_path.name}"
    except Exception as e:
        logger.error(f"Error compressing {file_path}: {e!s}")
        return False, str(e)


def decompress_file(file_path: Path, remove_original: bool = True) -> Tuple[bool, str]:
    """Decompress a single Snappy-compressed file and optionally remove the original.

    Args:
        file_path: Path to the compressed file.
        remove_original: If True, delete the compressed file after decompression.

    Returns:
        A tuple of (success, message).
    """
    try:
        if file_path.suffix != COMPRESSED_EXT:
            return False, f"File {file_path} doesn't have {COMPRESSED_EXT} extension"
        output_path: Path = file_path.with_suffix("")
        with open(file_path, "rb") as f:
            compressed_data: bytes = f.read()
        decompressed_data: bytes = bytes(cramjam.snappy.decompress(compressed_data))
        with open(output_path, "wb") as f:
            f.write(decompressed_data)
        if remove_original:
            file_path.unlink()
        logger.info(
            f"Decompressed: {file_path} -> {output_path} "
            f"({len(compressed_data)} -> {len(decompressed_data)} bytes)"
        )
        return True, f"Decompressed {file_path.name}"
    except Exception as e:
        logger.error(f"Error decompressing {file_path}: {e!s}")
        return False, str(e)


def process_file_worker(args: Tuple[Path, str, bool]) -> Tuple[bool, str]:
    """Worker entry point for processing a single file.

    Args:
        args: Tuple of (file_path, operation, remove_original).

    Returns:
        A tuple of (success, message).
    """
    file_path, operation, remove_original = args
    if operation == "compress":
        return compress_file(file_path, remove_original)
    if operation == "decompress":
        return decompress_file(file_path, remove_original)
    return False, f"Unknown operation: {operation}"


def find_files(directory: Path, operation: str, recursive: bool = True) -> list[Path]:
    """Find files to process in a directory.

    Args:
        directory: Base directory to search.
        operation: Either "compress" or "decompress".
        recursive: If True, search recursively.

    Returns:
        A list of matching file paths.
    """
    files: list[Path] = []
    if operation == "compress":
        pattern: str = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix != COMPRESSED_EXT:
                files.append(file_path)
    else:
        pattern = f"**/*{COMPRESSED_EXT}" if recursive else f"*{COMPRESSED_EXT}"
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                files.append(file_path)
    return files


def create_tar_archive(directory: Path, remove_original: bool = True) -> Optional[Path]:
    """Create a tar archive from a directory and optionally remove the original.

    Args:
        directory: Directory to archive.
        remove_original: If True, delete the directory after archiving.

    Returns:
        The path to the created tar archive, or None on failure.
    """
    try:
        tar_path: Path = directory.with_suffix(".tar")
        logger.info(f"Creating tar archive: {tar_path}")
        with tarfile.open(tar_path, "w") as tar:
            tar.add(directory, arcname=directory.name)
        if remove_original:
            shutil.rmtree(directory)
            logger.info(f"Removed original directory: {directory}")
        logger.info(f"Created tar archive: {tar_path}")
        return tar_path
    except Exception as e:
        logger.error(f"Error creating tar archive for {directory}: {e!s}")
        return None


def tar_subdirectories(base_dir: Path, remove_original: bool = True) -> list[Path]:
    """Tar all immediate subdirectories of a base directory.

    Args:
        base_dir: Base directory whose subdirectories will be archived.
        remove_original: If True, delete each subdirectory after archiving.

    Returns:
        A list of created tar archive paths.
    """
    tar_files: list[Path] = []
    for item in base_dir.iterdir():
        if item.is_dir():
            tar_path: Optional[Path] = create_tar_archive(item, remove_original)
            if tar_path is not None:
                tar_files.append(tar_path)
    return tar_files


def process_files(
    file_paths: list[Path],
    operation: str,
    remove_original: bool = True,
) -> Tuple[int, int]:
    """Process a list of files concurrently using a fixed-size multiprocessing pool.

    Args:
        file_paths: List of file paths to process.
        operation: Either "compress" or "decompress".
        remove_original: If True, delete original files after processing.

    Returns:
        A tuple of (success_count, failure_count).
    """
    if not file_paths:
        logger.warning(f"No files found to {operation}")
        return 0, 0

    logger.info(f"Processing {len(file_paths)} files with {POOL_SIZE} workers")
    success_count: int = 0
    failure_count: int = 0

    args_list: list[Tuple[Path, str, bool]] = [
        (fp, operation, remove_original) for fp in file_paths
    ]

    pool: multiprocessing.pool.Pool = multiprocessing.Pool(processes=POOL_SIZE)
    try:
        async_results: list[Tuple[Path, Any]] = [
            (args[0], pool.apply_async(process_file_worker, (args,)))
            for args in args_list
        ]
        for file_path, async_result in async_results:
            try:
                success, message = async_result.get()
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    logger.error(f"Failed to process {file_path}: {message}")
            except Exception as e:
                failure_count += 1
                logger.error(f"Error processing {file_path}: {e!s}")
    finally:
        pool.close()
        pool.join()

    return success_count, failure_count


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed arguments namespace.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Compress or decompress files recursively using Snappy (cramjam)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python snappy_tool.py -c .
  python snappy_tool.py -d /path/to/directory
  python snappy_tool.py -c -t .
  python snappy_tool.py -c --keep-original .
        """,
    )
    parser.add_argument("directory", type=str, help="Directory to process")
    group: argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group(
        required=True
    )
    group.add_argument("-c", "--compress", action="store_true", help="Compress files")
    group.add_argument(
        "-d", "--decompress", action="store_true", help="Decompress files"
    )
    parser.add_argument(
        "-t",
        "--tar",
        action="store_true",
        help="Tar subdirectories first before compression",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        help="Keep original files (default: remove them)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not process subdirectories recursively",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    return parser.parse_args()


def main() -> int:
    """Run the Snappy compression/decompression CLI.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    args: argparse.Namespace = parse_args()

    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    base_dir: Path = Path(args.directory)
    if not base_dir.exists() or not base_dir.is_dir():
        logger.error(f"Directory not found: {base_dir}")
        return 1

    remove_original: bool = not args.keep_original
    operation: str = "compress" if args.compress else "decompress"
    recursive: bool = not args.no_recursive

    logger.info(f"Starting {operation} operation on {base_dir}")
    logger.info(f"Remove original: {remove_original}, Recursive: {recursive}")

    if args.tar and args.compress:
        logger.info("Tarring subdirectories...")
        tar_files: list[Path] = tar_subdirectories(base_dir, remove_original)
        logger.info(f"Created {len(tar_files)} tar archives")

    files_to_process: list[Path] = find_files(base_dir, operation, recursive)

    if not files_to_process:
        logger.warning(f"No files found to {operation}")
        return 0

    logger.info(f"Found {len(files_to_process)} files to {operation}")

    success_count: int
    failure_count: int
    success_count, failure_count = process_files(
        files_to_process, operation, remove_original
    )

    logger.info(f"Completed {operation} operation")
    logger.info(f"Success: {success_count}, Failed: {failure_count}")

    return 1 if failure_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
