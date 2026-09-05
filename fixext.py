#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import argparse
import logging
import multiprocessing as mp
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from dh import MIME2EXT, SHEBANG_MAP, get_files

LOGGER = logging.getLogger(__name__)
PROTECTED_EXTENSIONS = {
    ".css",
    ".js",
    ".min.js",
    ".min.css",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
}


def configure_logging(debug: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.WARNING,
        format="%(levelname)s | %(message)s",
    )


def _mime_to_ext(mime_type: str) -> str | None:
    extensions = MIME2EXT.get(mime_type)
    if isinstance(extensions, list):
        return extensions[0] if extensions else None
    return extensions


def detect_with_pure_magic(file_path: Path) -> str | None:
    try:
        import magic

        mime = magic.Magic(mime=True)
        return _mime_to_ext(mime.from_file(str(file_path)))
    except Exception as exc:
        LOGGER.debug("pure-magic failed for %s: %s", file_path, exc)
        return None


def detect_with_python_magic(file_path: Path) -> str | None:
    try:
        import magic

        mime_type = magic.from_file(str(file_path), mime=True)
        return _mime_to_ext(mime_type)
    except Exception as exc:
        LOGGER.debug("python-magic failed for %s: %s", file_path, exc)
        return None


def detect_with_filetype(file_path: Path) -> str | None:
    try:
        import filetype

        kind = filetype.guess(str(file_path))
        return f".{kind.extension}" if kind else None
    except Exception as exc:
        LOGGER.debug("filetype failed for %s: %s", file_path, exc)
        return None


def detect_with_file_command(file_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["file", "--brief", "--mime-type", str(file_path)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return _mime_to_ext(result.stdout.strip())
    except Exception as exc:
        LOGGER.debug("file command failed for %s: %s", file_path, exc)
    return None


def detect_shebang_ext(file_path: Path) -> str | None:
    try:
        with file_path.open("rb") as file:
            first_line = file.readline()
        if not first_line.startswith(b"#!"):
            return None
        shebang = first_line.decode("utf-8", errors="ignore").strip()
        for key, extension in SHEBANG_MAP.items():
            if key in shebang:
                return extension
    except Exception as exc:
        LOGGER.debug("shebang detection failed for %s: %s", file_path, exc)
    return None


def detect_extension(file_path: Path) -> str | None:
    detectors = (
        detect_shebang_ext,
        detect_with_pure_magic,
        detect_with_python_magic,
        detect_with_filetype,
        detect_with_file_command,
    )
    for detector in detectors:
        extension = detector(file_path)
        if extension:
            if not extension.startswith("."):
                extension = f".{extension}"
            return extension.lower()
    return None


def get_current_extension(file_path: Path) -> str:
    name = file_path.name.lower()
    for extension in sorted(PROTECTED_EXTENSIONS, key=len, reverse=True):
        if name.endswith(extension):
            return extension
    return file_path.suffix.lower()


def is_protected_extension(extension: str) -> bool:
    return extension.lower() in PROTECTED_EXTENSIONS


def rename_with_extension(
    file_path: Path,
    detected_ext: str,
) -> tuple[Path, bool]:
    new_name = file_path.with_suffix(detected_ext)
    if new_name == file_path:
        return file_path, False
    if new_name.exists():
        LOGGER.debug("Destination already exists; skipping: %s", new_name)
        return file_path, False
    try:
        file_path.rename(new_name)
        return new_name, True
    except OSError as exc:
        LOGGER.debug("Could not rename %s: %s", file_path, exc)
        return file_path, False


def check_file(
    file_path: Path,
    auto_fix: bool = False,
) -> tuple[Path, bool, str | None, str | None]:
    if not file_path.is_file():
        return file_path, False, None, None
    current_ext = get_current_extension(file_path)
    detected_ext = detect_extension(file_path)
    if not detected_ext:
        return file_path, False, current_ext or None, None
    if current_ext == detected_ext:
        return file_path, False, current_ext or None, detected_ext
    if is_protected_extension(current_ext) and detected_ext == ".txt":
        LOGGER.debug("Protected extension; skipping %s", file_path)
        return file_path, False, current_ext, detected_ext
    if not auto_fix:
        return file_path, True, current_ext or None, detected_ext
    renamed_path, renamed = rename_with_extension(file_path, detected_ext)
    return renamed_path, renamed, current_ext or None, detected_ext


def collect_files(inputs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for input_path in inputs:
        input_path = input_path.expanduser()
        if input_path.is_file():
            files.append(input_path)
        elif input_path.is_dir():
            files.extend(path for path in input_path.rglob("*") if path.is_file())
        else:
            print(f"Warning: not found or unsupported: {input_path}", file=sys.stderr)
    return list(dict.fromkeys(files))


def print_detected_extension(
    file_path: Path,
    detected_ext: str | None,
) -> None:
    if detected_ext:
        print(f"{file_path.name} -> {detected_ext}")
    else:
        print(f"{file_path} -> unknown")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect and optionally fix file extension mismatches."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="Files or directories to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "-a",
        "--auto-fix",
        action="store_true",
        help="Rename files to their detected extensions.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()
    configure_logging(args.debug)
    cwd = Path.cwd()
    files = collect_files(args.inputs) or get_files(cwd)
    if not files:
        print("No files found.", file=sys.stderr)
        return
    mismatches = 0
    fixed = 0
    with mp.Pool(processes=8) as pool:
        jobs = [
            pool.apply_async(check_file, (file_path, args.auto_fix))
            for file_path in files
        ]
        for file_path, job in zip(files, jobs, strict=False):
            try:
                result_path, is_mismatch, _old_ext, new_ext = job.get()
                print_detected_extension(file_path, new_ext)
                if is_mismatch:
                    mismatches += 1
                    if args.auto_fix and result_path != file_path:
                        fixed += 1
                        print(f"renamed: {file_path} -> {result_path}")
            except Exception as exc:
                LOGGER.debug("Error processing %s: %s", file_path, exc)
                print(f"{file_path} -> error: {exc}", file=sys.stderr)
    print()
    print(f"Total files scanned: {len(files)}")
    print(f"Mismatches found: {mismatches}")
    if args.auto_fix:
        print(f"Files fixed: {fixed}")


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
