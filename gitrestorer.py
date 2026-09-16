#!/data/data/com.termux/files/home/.local/bin/python
"""gitrestorer.py – Gitrestorer utilities.

This module provides functionality for gitrestorer."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path

def is_git_repo(path: Path) -> bool:
    """is_git_repo – is git repo.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    return (path / '.git').is_dir()

def git_pull(repo_path: Path) -> None:
    """git_pull – git pull.

Args:
    repo_path: Description of repo_path."""
    print(f'\n==> Pulling in repo: {repo_path}')
    try:
        subprocess.run(['git', '-C', str(repo_path), 'restore', '.'], check=True)
    except subprocess.CalledProcessError:
        print(f'⚠️  git pull failed in: {repo_path}')

def main() -> None:
    """main – main."""
    root = Path.cwd()
    for dirpath, _dirnames, _filenames in os.walk(root):
        current = Path(dirpath)
        if is_git_repo(current):
            git_pull(current)
    print('\nDone.')
if __name__ == '__main__':
    raise SystemExit(main())
