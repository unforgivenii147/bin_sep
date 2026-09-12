#!/data/data/com.termux/files/home/.local/bin/python
"""
Prompt: Refactor a Python script that detects and keeps only the latest version of package files (.whl and .deb) in a directory tree. Use multiprocessing.Pool.apply_async with a fixed pool of 8 workers instead of concurrent.futures. Add complete type hints, docstrings, loguru logging, pathlib, and fix type checker issues. Provide CLI with mutually exclusive --deb, --wheel, --all flags, --dry-run, --dir, and --verbose.
"""

import argparse
import re
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from packaging import version as pkg_version

# Module-level constants
MAX_WORKERS: int = 8
WHEEL_EXTENSION: str = ".whl"
DEB_EXTENSION: str = ".deb"


def parse_wheel_version(filename: str) -> Optional[tuple[str, str]]:
    """
    Parse a wheel filename into package name and version.

    Args:
        filename: The wheel filename (e.g., "package-1.0.0-py3-none-any.whl").

    Returns:
        A tuple of (package_name, version) or None if parsing fails.
    """
    name: str = filename[:-4]
    parts: list[str] = name.split("-")
    if len(parts) < 5:
        return None
    pkg_name_parts: list[str] = []
    version_parts: list[str] = []
    found_version: bool = False
    for i, part in enumerate(parts):
        if not found_version and (
            re.match(r"^\d", part) or part.lower() in ["v", "ver", "version"]
        ):
            found_version = True
            version_parts.append(part)
        elif not found_version:
            pkg_name_parts.append(part)
        else:
            remaining_parts: int = len(parts) - i
            if remaining_parts <= 3:
                break
            version_parts.append(part)
    if pkg_name_parts and version_parts:
        pkg_name: str = "-".join(pkg_name_parts)
        version: str = "-".join(version_parts)
        return pkg_name, version
    return None


def parse_deb_version(filename: str) -> Optional[tuple[str, str]]:
    """
    Parse a deb filename into package name and version.

    Args:
        filename: The deb filename (e.g., "package_1.0.0_amd64.deb").

    Returns:
        A tuple of (package_name, version) or None if parsing fails.
    """
    name: str = filename[:-4]
    parts: list[str] = name.split("_")
    if len(parts) >= 2:
        pkg_name: str = parts[0]
        version: str = parts[1]
        return pkg_name, version
    return None


def compare_versions(ver1: str, ver2: str) -> int:
    """
    Compare two version strings.

    Args:
        ver1: First version string.
        ver2: Second version string.

    Returns:
        -1 if ver1 < ver2, 1 if ver1 > ver2, 0 if equal.
    """
    try:
        v1: Any = pkg_version.parse(ver1)
        v2: Any = pkg_version.parse(ver2)
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    except Exception:
        if ver1 < ver2:
            return -1
        elif ver1 > ver2:
            return 1
        else:
            return 0


def process_file(file_path: Path, file_type: str) -> Optional[tuple[str, str, Path]]:
    """
    Process a single package file and extract its name and version.

    Args:
        file_path: Path to the package file.
        file_type: Either "wheel" or "deb".

    Returns:
        A tuple of (package_name, version, file_path) or None if processing fails.
    """
    try:
        filename: str = file_path.name
        if file_type == "wheel" and filename.endswith(WHEEL_EXTENSION):
            parsed: Optional[tuple[str, str]] = parse_wheel_version(filename)
            if parsed:
                pkg_name, version = parsed
                return pkg_name, version, file_path
        elif file_type == "deb" and filename.endswith(DEB_EXTENSION):
            parsed = parse_deb_version(filename)
            if parsed:
                pkg_name, version = parsed
                return pkg_name, version, file_path
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
    return None


def _process_file_wrapper(args: tuple[Path, str]) -> Optional[tuple[str, str, Path]]:
    """
    Wrapper for process_file to be used with multiprocessing.Pool.apply_async.

    Args:
        args: A tuple of (file_path, file_type).

    Returns:
        A tuple of (package_name, version, file_path) or None if processing fails.
    """
    file_path, file_type = args
    return process_file(file_path, file_type)


def scan_directory(
    directory: Path, file_type: str, check_all: bool = False
) -> dict[str, list[tuple[str, Path]]]:
    """
    Scan a directory for package files and group them by package name.

    Args:
        directory: The directory to scan.
        file_type: Either "wheel", "deb", or "all".
        check_all: If True, scan for both wheel and deb files.

    Returns:
        A dictionary mapping package names to lists of (version, file_path) tuples.
    """
    packages: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    extensions: list[str] = []
    if check_all:
        extensions = [WHEEL_EXTENSION, DEB_EXTENSION]
    elif file_type == "wheel":
        extensions = [WHEEL_EXTENSION]
    elif file_type == "deb":
        extensions = [DEB_EXTENSION]

    files_to_process: list[Path] = []
    for ext in extensions:
        files_to_process.extend(directory.rglob(f"*{ext}"))

    logger.info(f"Found {len(files_to_process)} files to process...")

    tasks: list[tuple[Path, str]] = []
    for file_path in files_to_process:
        if file_path.suffix == WHEEL_EXTENSION:
            tasks.append((file_path, "wheel"))
        elif file_path.suffix == DEB_EXTENSION:
            tasks.append((file_path, "deb"))

    with Pool(processes=MAX_WORKERS) as pool:
        async_results = [
            pool.apply_async(_process_file_wrapper, (task,)) for task in tasks
        ]
        for async_result in async_results:
            result: Optional[tuple[str, str, Path]] = async_result.get()
            if result:
                pkg_name, version, file_path = result
                packages[pkg_name].append((version, file_path))

    return packages


def get_latest_version(
    versions: list[tuple[str, Path]],
) -> Optional[tuple[str, Path]]:
    """
    Get the latest version from a list of (version, path) tuples.

    Args:
        versions: A list of (version, path) tuples.

    Returns:
        The (version, path) tuple with the highest version, or None if empty.
    """
    if not versions:
        return None
    latest: tuple[str, Path] = versions[0]
    for version, path in versions[1:]:
        if compare_versions(version, latest[0]) > 0:
            latest = (version, path)
    return latest


def keep_latest_versions(
    packages: dict[str, list[tuple[str, Path]]], dry_run: bool = False
) -> int:
    """
    Delete all but the latest version of each package.

    Args:
        packages: A dictionary mapping package names to lists of (version, path) tuples.
        dry_run: If True, simulate deletion without actually removing files.

    Returns:
        The number of files deleted (or would be deleted in dry-run mode).
    """
    total_deleted: int = 0
    for pkg_name, versions in packages.items():
        if len(versions) <= 1:
            continue
        latest: Optional[tuple[str, Path]] = get_latest_version(versions)
        if latest is None:
            continue
        latest_version, latest_path = latest
        logger.info(f"\nPackage: {pkg_name}")
        logger.info(f"  Latest version: {latest_version} - {latest_path.name}")
        logger.info(f"  Total versions found: {len(versions)}")
        for version, file_path in versions:
            if file_path == latest_path:
                continue
            if dry_run:
                logger.info(f"  Would delete: {version} - {file_path.name}")
            else:
                try:
                    file_path.unlink()
                    logger.info(f"  Deleted: {version} - {file_path.name}")
                    total_deleted += 1
                except Exception as e:
                    logger.error(f"  Error deleting {file_path.name}: {e}")
    return total_deleted


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Detect and keep only the latest version of package files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group: argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--deb", action="store_true", help="Check .deb files")
    group.add_argument("-w", "--wheel", action="store_true", help="Check .whl files")
    group.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Check all package types (.whl and .deb)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate deletion without actually removing files",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information about each file",
    )
    args: argparse.Namespace = parser.parse_args()

    if not (args.deb or args.wheel or args.all):
        args.wheel = True

    scan_dir: Path = Path(args.dir).resolve()
    if not scan_dir.exists():
        logger.error(f"Error: Directory '{scan_dir}' does not exist")
        return 1

    file_type: str
    if args.all:
        file_type = "all"
    elif args.deb:
        file_type = "deb"
    else:
        file_type = "wheel"

    logger.info(f"Scanning directory: {scan_dir}")
    logger.info(f"File type: {file_type}")
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be deleted")
    logger.info("-" * 40)

    packages: dict[str, list[tuple[str, Path]]] = scan_directory(
        scan_dir, file_type, args.all
    )

    if not packages:
        logger.info("No matching package files found.")
        return 0

    logger.info(f"\nFound {len(packages)} package(s):")
    for pkg_name, versions in packages.items():
        logger.info(f"  {pkg_name}: {len(versions)} version(s)")
        if args.verbose and len(versions) > 1:
            for version, path in versions:
                logger.info(f"    - {version}: {path.name}")

    logger.info("\n" + "=" * 40)
    total_deleted: int = keep_latest_versions(packages, args.dry_run)
    logger.info("\n" + "=" * 40)

    if total_deleted == 0:
        logger.info("No files to delete. All packages have only one version.")
    elif args.dry_run:
        logger.info(f"Dry run complete. Would delete {total_deleted} file(s).")
    else:
        logger.info(f"Cleanup complete. Deleted {total_deleted} file(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
