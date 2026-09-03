#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    filepath: Path
    success: bool
    modified: bool
    error: Optional[str] = None
    message: str = ""


def validate_input_line(line: str) -> str:
    if not isinstance(line, str):
        raise ValueError("Input line must be a string")
    normalized = line.strip()
    if not normalized:
        raise ValueError("Input line cannot be empty")
    if "\n" in normalized or "\r" in normalized:
        normalized = normalized.replace("\n", "").replace("\r", "")
        logger.warning(f"Removed newline characters from input: {normalized!r}")
    return normalized


def line_exists_in_file(filepath: Path, target_line: str) -> bool:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.rstrip("\n\r") == target_line:
                    return True
        return False
    except (IOError, OSError) as e:
        logger.warning(f"Error reading {filepath}: {e}")
        return False


def append_line_to_gitignore(filepath: Path, target_line: str) -> ProcessResult:
    try:
        if not os.access(filepath.parent, os.W_OK):
            return ProcessResult(
                filepath=filepath,
                success=False,
                modified=False,
                error="Permission denied",
                message=f"No write permission for {filepath.parent}",
            )
        if filepath.exists() and line_exists_in_file(filepath, target_line):
            return ProcessResult(
                filepath=filepath,
                success=True,
                modified=False,
                message="Line already exists",
            )
        try:
            content = filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            logger.warning(f"Encoding issues in {filepath}, using fallback")
        needs_newline = content and not content.endswith("\n")
        new_content = content
        if needs_newline:
            new_content += "\n"
        new_content += target_line + "\n"
        filepath.write_text(new_content, encoding="utf-8")
        return ProcessResult(
            filepath=filepath,
            success=True,
            modified=True,
            message="Line added successfully",
        )
    except Exception as e:
        logger.error(f"Unexpected error processing {filepath}: {e}")
        return ProcessResult(
            filepath=filepath,
            success=False,
            modified=False,
            error=str(e),
            message=f"Failed to process: {type(e).__name__}",
        )


def find_gitignore_files(search_paths: list[Path]) -> list[Path]:
    gitignore_files = []
    for search_path in search_paths:
        if not search_path.exists():
            logger.warning(f"Path does not exist: {search_path}")
            continue
        if search_path.is_symlink():
            logger.warning(f"Skipping symlink: {search_path}")
            continue
        if search_path.is_file():
            if search_path.name == ".gitignore":
                gitignore_files.append(search_path)
            continue
        if search_path.is_dir():
            try:
                for gitignore in search_path.rglob(".gitignore"):
                    if gitignore.is_file() and not gitignore.is_symlink():
                        gitignore_files.append(gitignore)
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot access directory {search_path}: {e}")
                continue
    return gitignore_files


def process_gitignore_wrapper(args: tuple[Path, str]) -> ProcessResult:
    filepath, target_line = args
    return append_line_to_gitignore(filepath, target_line)


def main() -> int:
    if len(sys.argv) < 2:
        logger.error("Usage: python gitignore_updater.py <line> [path1] [path2] ...")
        logger.error("  <line>: The line to add to all .gitignore files")
        logger.error(
            "  [paths]: Optional paths to search (defaults to current directory)"
        )
        return 1
    target_line = sys.argv[1]
    search_paths_arg = sys.argv[2:] if len(sys.argv) > 2 else ["."]
    try:
        target_line = validate_input_line(target_line)
        logger.info(f"Target line: {target_line!r}")
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 1
    search_paths = []
    for path_str in search_paths_arg:
        try:
            path = Path(path_str).resolve()
            search_paths.append(path)
            logger.info(f"Search path: {path}")
        except (ValueError, OSError) as e:
            logger.error(f"Invalid path {path_str}: {e}")
            return 1
    logger.info("Scanning for .gitignore files...")
    gitignore_files = find_gitignore_files(search_paths)
    if not gitignore_files:
        logger.warning("No .gitignore files found")
        return 0
    logger.info(f"Found {len(gitignore_files)} .gitignore file(s)")
    tasks = [(filepath, target_line) for filepath in gitignore_files]
    num_workers = min(4, cpu_count() or 1)
    logger.info(f"Using {num_workers} worker(s)")
    results = []
    try:
        with Pool(processes=num_workers) as pool:
            results = pool.map(process_gitignore_wrapper, tasks)
    except KeyboardInterrupt:
        logger.error("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Multiprocessing error: {e}")
        return 1
    successful = sum(1 for r in results if r.success)
    modified = sum(1 for r in results if r.modified)
    skipped = successful - modified
    failed = len(results) - successful
    logger.info("=" * 40)
    logger.info("SUMMARY")
    logger.info("=" * 40)
    logger.info(f"Total files processed: {len(results)}")
    logger.info(f"Successfully processed: {successful}")
    logger.info(f"Files modified: {modified}")
    logger.info(f"Files skipped (already exist): {skipped}")
    logger.info(f"Failed: {failed}")
    if failed > 0:
        logger.info("\nFailed files:")
        for result in results:
            if not result.success:
                logger.info(f"  {result.filepath}: {result.message}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
