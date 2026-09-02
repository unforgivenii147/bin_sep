#!/data/data/com.termux/files/home/.local/bin/python

from __future__ import annotations

import multiprocessing as mp
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


WORKERS = 4
SUPPORTED_SUFFIX = ".srt"

# Matches a complete SRT timing line, for example:
#
# 00:01:02,345 --> 00:01:05,678
# 1:02:03.400 --> 1:02:05.900
#
# Optional settings after the second timestamp are preserved.
TIMING_LINE_RE = re.compile(
    r"""
    ^
    (?P<start>
        \d{1,}:\d{2}:\d{2}
        [,.]
        \d{3}
    )
    (?P<separator>
        \s+-->\s+
    )
    (?P<end>
        \d{1,}:\d{2}:\d{2}
        [,.]
        \d{3}
    )
    (?P<settings>
        [^\r\n]*
    )
    (?P<newline>
        \r?\n|\r|$
    )
    $
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class ProcessResult:
    path: Path
    success: bool
    message: str


def parse_timestamp(timestamp: str) -> int:
    """
    Convert an SRT timestamp into milliseconds.

    Supports both comma and period millisecond separators.
    """
    hours, minutes, seconds_and_ms = timestamp.split(":", maxsplit=2)
    seconds, milliseconds = re.split(r"[,.]", seconds_and_ms, maxsplit=1)

    return (
        int(hours) * 60 * 60 * 1000
        + int(minutes) * 60 * 1000
        + int(seconds) * 1000
        + int(milliseconds)
    )


def format_timestamp(milliseconds: int, separator: str = ",") -> str:
    """
    Convert milliseconds into an SRT timestamp.

    Negative values are clamped to zero.
    """
    milliseconds = max(0, milliseconds)

    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)

    return (
        f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        f"{separator}{milliseconds:03d}"
    )


def shift_timing_line(line: str, shift_ms: int) -> str:
    """Shift the two timestamps on an SRT timing line."""
    match = TIMING_LINE_RE.match(line)

    if match is None:
        return line

    start_text = match.group("start")
    end_text = match.group("end")

    # Preserve the separator used by each timestamp.
    start_separator = "," if "," in start_text else "."
    end_separator = "," if "," in end_text else "."

    shifted_start = format_timestamp(
        parse_timestamp(start_text) + shift_ms,
        separator=start_separator,
    )
    shifted_end = format_timestamp(
        parse_timestamp(end_text) + shift_ms,
        separator=end_separator,
    )

    return (
        shifted_start
        + match.group("separator")
        + shifted_end
        + match.group("settings")
        + match.group("newline")
    )


def transform_file(
    source: TextIO,
    destination: TextIO,
    shift_ms: int,
) -> None:
    """
    Stream an SRT file from source to destination.

    Only timestamp lines are modified. All other content is copied unchanged.
    """
    for line in source:
        destination.write(shift_timing_line(line, shift_ms))


def process_file(path: Path, shift_ms: int) -> ProcessResult:
    """
    Shift one file in place using a temporary file and atomic replacement.

    The source file is not replaced unless the complete transformation succeeds.
    """
    path = path.resolve()

    if not path.is_file():
        return ProcessResult(path, False, "not a regular file")

    encodings = (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    )

    original_mode = path.stat().st_mode
    last_decode_error: UnicodeDecodeError | None = None

    for encoding in encodings:
        temporary_path: Path | None = None

        try:
            with (
                path.open("r", encoding=encoding, errors="strict", newline="")
                as source,
                tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding=encoding,
                    newline="",
                    dir=path.parent,
                    prefix=f".{path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as destination,
            ):
                temporary_path = Path(destination.name)
                transform_file(source, destination, shift_ms)
                destination.flush()
                os.fsync(destination.fileno())

            # Preserve the original permission bits.
            os.chmod(temporary_path, original_mode)

            # Atomic on the same filesystem.
            os.replace(temporary_path, path)

            return ProcessResult(
                path,
                True,
                f"updated using {encoding}",
            )

        except UnicodeDecodeError as error:
            last_decode_error = error

            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

            continue

        except Exception as error:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

            return ProcessResult(
                path,
                False,
                f"{type(error).__name__}: {error}",
            )

    return ProcessResult(
        path,
        False,
        f"unable to decode file: {last_decode_error}",
    )


def process_file_worker(path: str, shift_ms: int) -> ProcessResult:
    """Multiprocessing-compatible wrapper."""
    return process_file(Path(path), shift_ms)


def collect_srt_files(inputs: list[str]) -> list[Path]:
    """
    Collect unique SRT files from file and directory arguments.

    Directories are searched recursively.
    """
    files: dict[Path, Path] = {}

    for item in inputs:
        path = Path(item).expanduser()

        if path.is_file():
            if path.suffix.lower() == SUPPORTED_SUFFIX:
                resolved = path.resolve()
                files[resolved] = resolved

        elif path.is_dir():
            for candidate in path.rglob("*"):
                if (
                    candidate.is_file()
                    and candidate.suffix.lower() == SUPPORTED_SUFFIX
                ):
                    resolved = candidate.resolve()
                    files[resolved] = resolved

        else:
            print(f"Warning: skipping missing path: {path}", file=sys.stderr)

    return sorted(files.values(), key=lambda file: str(file).lower())


def parse_arguments(argv: list[str]) -> tuple[list[str], int]:
    """
    Parse arguments in this form:

        shiftsrt.py amount
        shiftsrt.py file.srt amount
        shiftsrt.py file1.srt dir1/ +12
    """
    if len(argv) < 1:
        raise ValueError(
            "usage: shiftsrt.py [FILE_OR_DIR ...] SECONDS"
        )

    try:
        shift_seconds = int(argv[-1])
    except ValueError as error:
        raise ValueError(
            "SECONDS must be an integer such as +12, -3, or 0"
        ) from error

    inputs = argv[:-1]

    if not inputs:
        inputs = [str(Path.cwd())]

    return inputs, shift_seconds


def main() -> int:
    try:
        inputs, shift_seconds = parse_arguments(sys.argv[1:])
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    files = collect_srt_files(inputs)

    if not files:
        print("No SRT files found.", file=sys.stderr)
        return 1

    shift_ms = shift_seconds * 1_000

    print(
        f"Processing {len(files)} file(s) with "
        f"{min(WORKERS, len(files))} worker(s); "
        f"shift={shift_seconds:+d}s"
    )

    results: list[ProcessResult] = []

    if len(files) == 1:
        results.append(process_file(files[0], shift_ms))
    else:
        worker_count = min(WORKERS, len(files))

        with mp.Pool(processes=worker_count) as pool:
            jobs = [
                pool.apply_async(
                    process_file_worker,
                    (str(path), shift_ms),
                )
                for path in files
            ]

            for job in jobs:
                try:
                    results.append(job.get())
                except Exception as error:
                    results.append(
                        ProcessResult(
                            Path("<worker>"),
                            False,
                            f"{type(error).__name__}: {error}",
                        )
                    )

    failures = 0

    for result in results:
        if result.success:
            print(f"OK:   {result.path} ({result.message})")
        else:
            failures += 1
            print(
                f"FAIL: {result.path} ({result.message})",
                file=sys.stderr,
            )

    print(
        f"Completed: {len(results) - failures} succeeded, "
        f"{failures} failed."
    )

    return 1 if failures else 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
