#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def get_created_files(n_commits: int) -> list:
    try:
        cmd = [
            "git",
            "log",
            "-n",
            str(n_commits),
            "--pretty=format:",
            "--name-status",
            "--diff-filter=A",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        created_files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    file_path = parts[1]
                    path = Path(file_path)
                    if path.is_symlink():
                        continue
                    created_files.append(file_path)
        return created_files
    except subprocess.CalledProcessError as e:
        print(f"✗ Git command failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 list_commits.py <N>")
        print("       where N is the number of commits to analyze")
        print("\nExamples:")
        print("  python3 list_commits.py 5")
        print("  python3 list_commits.py 10")
        sys.exit(1)
    try:
        n_commits = int(sys.argv[1])
        if n_commits <= 0:
            print("✗ Error: Number of commits must be positive", file=sys.stderr)
            sys.exit(1)
        created_files = get_created_files(n_commits)
        if created_files:
            for file_path in created_files:
                print(file_path)
        else:
            print(
                "No files created in the last {} commit(s)".format(n_commits),
                file=sys.stderr,
            )
    except ValueError:
        print(f"✗ Error: '{sys.argv[1]}' is not a valid integer", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    raise SystemExit(main())
