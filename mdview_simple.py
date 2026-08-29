#!/data/data/com.termux/files/home/.local/bin/python
"""Minimal markdown viewer - no external dependencies."""

import sys
import re
from pathlib import Path


def render_markdown(text: str) -> str:
    lines = text.splitlines()
    output = []
    in_code = False

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            in_code = not in_code
            output.append("\033[90m" + line + "\033[0m")  # gray
            continue
        if in_code:
            output.append("\033[90m" + line + "\033[0m")
            continue

        # Headings
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            # Bold + underline for headings
            output.append(f"\033[1;4m{'#' * level} {text}\033[0m")
            continue

        # Bold
        line = re.sub(r"\*\*(.+?)\*\*", r"\033[1m\1\033[0m", line)
        # Italic
        line = re.sub(r"\*(.+?)\*", r"\033[3m\1\033[0m", line)
        # Inline code
        line = re.sub(r"`(.+?)`", r"\033[36m\1\033[0m", line)

        # Unordered list
        if re.match(r"^\s*[-*]\s+", line):
            output.append("\033[33m•\033[0m " + re.sub(r"^\s*[-*]\s+", "", line))
            continue

        # Ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            output.append("\033[33m" + line + "\033[0m")
            continue

        output.append(line)

    return "\n".join(output)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python mdview.py <file.md>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: {file_path} does not exist.")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")
    print(render_markdown(content))


if __name__ == "__main__":
    main()
