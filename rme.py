#!/data/data/com.termux/files/home/.local/bin/python

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown


def read_markdown(file_path: str) -> str:
    path = Path(file_path).expanduser()

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    return path.read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdview",
        description="View a Markdown file in the terminal, page by page.",
    )
    parser.add_argument(
        "file",
        default="README.md",
        nargs="*",
        type=str,
        help="Path to a Markdown file",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    console = Console()
    err_console = Console(stderr=True)
    if not args.file:
        args.file = "README.md"
    try:
        markdown_text = read_markdown(args.file)
    except FileNotFoundError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        return 1
    except PermissionError:
        err_console.print(f"[red]Error:[/red] Permission denied: {args.file}")
        return 1
    except UnicodeDecodeError:
        err_console.print(
            f"[red]Error:[/red] {args.file} is not a valid UTF-8 text file."
        )
        return 1
    except OSError as error:
        err_console.print(f"[red]Error:[/red] ")

    md = Markdown(markdown_text)

    with console.capture() as capture:
        console.print(md)
    rendered = capture.get()
    lines = rendered.splitlines()

    if not lines:
        console.print("[dim](empty file)[/dim]")
        return 0

    height = max(console.height - 2, 1)
    page_count = max((len(lines) + height - 1) // height, 1)
    current_page = 0

    while True:
        console.clear()
        start = current_page * height
        end = start + height
        for line in lines[start:end]:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()

        console.print(
            f"\n[bold]Page {current_page + 1}/{page_count}[/bold]  "
            f"[dim](n: next, p: prev, q: quit)[/dim]"
        )

        try:
            key = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if key in ("q", "quit"):
            break
        elif key in ("n", "next", ""):
            if current_page < page_count - 1:
                current_page += 1
            else:
                console.print("[dim](already at last page)[/dim]")
        elif key in ("p", "prev"):
            if current_page > 0:
                current_page -= 1
            else:
                console.print("[dim](already at first page)[/dim]")
        else:
            continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
