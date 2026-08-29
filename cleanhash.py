#!/data/data/com.termux/files/home/.local/bin/python
"""
**File extensions using "#" as comment character:**
".py", ".rb", ".pl", ".pm", ".sh", ".bash", ".zsh", ".fish", ".csh", ".ksh", ".yaml", ".yml", ".toml", ".jl", ".ps1", ".psm1", ".awk", ".sed", ".gnuplot", ".cfg", ".conf", ".ini", ".gitignore", ".dockerignore", ".editorconfig", ".env", ".flake8", ".pylintrc", "Makefile" (no extension), "Dockerfile".

**Other common comment characters and example extensions:**

- "//" (line) / "/* */" (block): ".c", ".cpp", ".h", ".java", ".js", ".ts", ".cs", ".go", ".swift", ".kt", ".rs", ".scala", ".dart", ".php" (also "#" and "//").
- "--" (line): ".lua", ".sql", ".ada", ".hs" (Haskell), ".vhd" (VHDL), ".sql" (also "/* */").
- ";" (line): ".asm", ".lisp", ".cl", ".ini" (also "#"), ".s" (assembly).
- "%" (line): ".tex", ".sty", ".cls", ".m" (MATLAB), ".erl" (Erlang), ".prolog".
- "'" (line): ".vb", ".vbs", ".bas" (Visual Basic / BASIC).
- "REM" (keyword): ".bat", ".cmd" (batch files).
- "#" (line) also used in: ".perl", ".python", ".ruby" (already listed).
"""

from __future__ import annotations

import sys
from pathlib import Path
from dh import should_skip
from fastwalk import walk_files

EXT = {
    ".zsh",
    ".fish",
    ".csh",
    ".ksh",
    ".yaml",
    ".yml",
    ".toml",
    ".ps1",
    ".psm1",
    ".awk",
    ".sed",
    ".gnuplot",
    ".cfg",
    ".conf",
    ".ini",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    ".env",
    ".flake8",
    ".pylintrc",
}


def get_files(root_dir):
    for p in walk_files(root_dir):
        if should_skip(p):
            continue
        if p.suffix in EXT:
            yield p


def strip_comments(line):
    if line.startswith("#!"):
        return (line, 0)
    in_single_quote = False
    in_double_quote = False
    for i, char in enumerate(line):
        if char == "'" and (not in_double_quote):
            in_single_quote = not in_single_quote
        elif char == '"' and (not in_single_quote):
            in_double_quote = not in_double_quote
        elif char == "#" and (not in_single_quote) and (not in_double_quote):
            return (line[:i].rstrip() + "\n", 1)
    return (line, 0)


def process_file(path) -> int:
    try:
        rel_path = path.relative_to(Path.cwd().resolve())
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        cleaned_lines = []
        total_removed = 0
        for line in lines:
            cleaned, count = strip_comments(line)
            cleaned_lines.append(cleaned)
            total_removed += count
        if total_removed > 0:
            path.write_text("".join(cleaned_lines))
            print(f"{rel_path}: removed {total_removed} comments")
            return total_removed
        return 0
    except Exception as e:
        print(f"Failed {path}: {e}")
        return 0


def main():
    cwd = Path.cwd()
    args = sys.argv[1:]
    total = 0
    if args:
        for arg in args:
            p = Path(arg)
            if p.is_file():
                total += process_file(p)
            elif p.is_dir():
                for pth in get_files(p):
                    total += process_file(pth)
    else:
        for f in get_files(cwd):
            total += process_file(f)

    print(f"{total} comments removed")


if __name__ == "__main__":
    raise SystemExit(main())
