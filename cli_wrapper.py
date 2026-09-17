#!/data/data/com.termux/files/home/.local/bin/python
"""Run a CLI binary through a logging shim: tee its output to a per-run log file.

Consolidates feloai.py and wrapper_gh.py, which were the same ~100-line template
hard-wired to one binary each (``felo`` and ``gh``). The binary is now the first
argument, so one script wraps any command:

    python cli_wrapper.py gh repo view
    python cli_wrapper.py felo "translate this"
    python cli_wrapper.py --bin /data/data/com.termux/files/usr/bin/curl -I example.com

Each run writes ``~/tmp/log/apps/<bin>_<timestamp>_<ms>.log`` with a header
(command + cwd + time), the merged stdout/stderr stream, and a footer with the
exit code; the exit code of the wrapped binary is propagated.
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

LOG_DIR = Path.home() / "tmp" / "log" / "apps"

# Preferred absolute locations, so the shim never accidentally runs itself.
KNOWN_BINS: dict[str, tuple[str, ...]] = {
    "gh": ("/data/data/com.termux/files/usr/bin/gh",),
    "felo": ("/data/data/com.termux/files/home/.npm-global/bin/felo",),
}


def find_real_binary(name: str) -> str | None:
    """Locate the executable *name*, ignoring any copy that is this script."""
    self_path = os.path.realpath(__file__)
    candidates = [Path(p) for p in KNOWN_BINS.get(name, ())]
    candidates += [
        Path(path_dir) / name for path_dir in os.environ.get("PATH", "").split(os.pathsep)
    ]
    for candidate in candidates:
        try:
            if (
                candidate.is_file()
                and os.access(candidate, os.X_OK)
                and os.path.realpath(candidate) != self_path
            ):
                return str(candidate)
        except OSError:
            continue
    return None


def create_log_file(name: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    milliseconds = int(time.time() * 400) % 1000
    log_file = LOG_DIR / f"{name}_{timestamp}_{milliseconds:03d}.log"
    counter = 1
    while log_file.exists():
        log_file = LOG_DIR / f"{name}_{timestamp}_{milliseconds:03d}_{counter}.log"
        counter += 1
    return log_file


def write_log_header(log_file: Path, name: str, binary: str, command_args: list[str]) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"=== {name.upper()} Command Log ===\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Binary: {binary}\n")
        f.write(f"Cwd: {os.getcwd()}\n")
        f.write(f"Command: {name} {' '.join(command_args)}\n")
        f.write("================================\n\n")


def write_log_footer(log_file: Path, exit_code: int) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n================================\n")
        f.write(f"Exit Code: {exit_code}\n")
        f.write(f"Completed: {timestamp}\n")
        f.write("================================\n")


def parse_args(argv: list[str]) -> tuple[str, list[str]]:
    """Split argv into (binary name, binary args) without argparse eating -flags."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--bin", dest="bin_path")
    known, rest = parser.parse_known_args(argv)
    if known.bin_path:
        binary = known.bin_path
        return Path(binary).name, [binary, *rest]
    if not rest:
        parser.print_usage(sys.stderr)
        raise SystemExit("error: give the binary to wrap, e.g. cli_wrapper.py gh repo view")
    return rest[0], rest


def main() -> None:
    name, argv = parse_args(sys.argv[1:])
    # argv[0] is either an explicit path (--bin) or the binary name to look up
    given = argv[0]
    command_args = argv[1:]
    binary = given if os.path.sep in given else find_real_binary(name)
    if not binary or not os.path.isfile(binary):
        print(f"Error: could not find the real {name} binary", file=sys.stderr)
        print(f"Please install {name} first (e.g. pkg install {name})", file=sys.stderr)
        raise SystemExit(1)

    log_file = create_log_file(name)
    write_log_header(log_file, name, binary, command_args)
    command = [binary, *command_args]
    exit_code = 1
    try:
        with open(log_file, "a", encoding="utf-8") as log_f:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log_f.write(line)
                log_f.flush()
            process.wait()
            exit_code = process.returncode
    except KeyboardInterrupt:
        exit_code = 130
        print("\nInterrupted by user", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 - always log, then propagate
        exit_code = 1
        error_msg = f"Error running command: {exc}\n"
        sys.stderr.write(error_msg)
        with open(log_file, "a", encoding="utf-8") as log_f:
            log_f.write(error_msg)
    write_log_footer(log_file, exit_code)
    print(f"Log saved to: {log_file}", file=sys.stderr)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
