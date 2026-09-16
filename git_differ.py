#!/data/data/com.termux/files/home/.local/bin/python
"""git_differ.py – Git Differ utilities.

This module provides functionality for git differ."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

def run_git(*args: str, cwd: Path) -> str:
    """run_git – run git.

Args:
    cwd: Description of cwd.
    *args: Description of *args.

Returns:
    str: Description of return value."""
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout

def get_last_two_commits(repo: Path) -> tuple[str, str]:
    """get_last_two_commits – get last two commits.

Args:
    repo: Description of repo.

Returns:
    tuple[str, str]: Description of return value."""
    log_output = run_git('log', '-2', '--format=%H', cwd=repo).strip().splitlines()
    if len(log_output) < 2:
        raise RuntimeError('Repository needs at least 2 commits to diff.')
    newer, older = log_output
    return (older, newer)

def get_commit_meta(repo: Path, commit_hash: str) -> dict:
    """get_commit_meta – get commit meta.

Args:
    repo: Description of repo.
    commit_hash: Description of commit_hash.

Returns:
    dict: Description of return value."""
    fmt = '%an%x00%ae%x00%ad%x00%s'
    line = run_git('show', '-s', f'--format={fmt}', commit_hash, cwd=repo).strip()
    author, email, date, subject = line.split('\x00')
    return {'hash': commit_hash, 'author': author, 'email': email, 'date': date, 'subject': subject}

def get_file_stats(repo: Path, older: str, newer: str) -> list[dict]:
    """get_file_stats – get file stats.

Args:
    repo: Description of repo.
    older: Description of older.
    newer: Description of newer.

Returns:
    list[dict]: Description of return value."""
    name_status = run_git('diff', '--name-status', older, newer, cwd=repo).strip().splitlines()
    numstat = run_git('diff', '--numstat', older, newer, cwd=repo).strip().splitlines()
    numstat_map = {}
    for line in numstat:
        parts = line.split('\t')
        if len(parts) == 3:
            added, deleted, path = parts
            numstat_map[path] = {'insertions': None if added == '-' else int(added), 'deletions': None if deleted == '-' else int(deleted)}
    files = []
    for line in name_status:
        parts = line.split('\t')
        status = parts[0]
        if status.startswith(('R', 'C')) and len(parts) == 3:
            old_path, path = (parts[1], parts[2])
        else:
            old_path, path = (None, parts[1])
        stats = numstat_map.get(path, {'insertions': None, 'deletions': None})
        files.append({'status': status, 'path': path, 'old_path': old_path, 'insertions': stats['insertions'], 'deletions': stats['deletions']})
    return files

def get_patch(repo: Path, older: str, newer: str) -> str:
    """get_patch – get patch.

Args:
    repo: Description of repo.
    older: Description of older.
    newer: Description of newer.

Returns:
    str: Description of return value."""
    return run_git('diff', older, newer, cwd=repo)

def build_report(repo: Path) -> dict:
    """build_report – build report.

Args:
    repo: Description of repo.

Returns:
    dict: Description of return value."""
    older, newer = get_last_two_commits(repo)
    return {'repo': str(repo.resolve()), 'from_commit': get_commit_meta(repo, older), 'to_commit': get_commit_meta(repo, newer), 'files': get_file_stats(repo, older, newer), 'patch': get_patch(repo, older, newer)}

def main() -> None:
    """main – main."""
    repo = Path.cwd()
    output_path = repo / 'diff_report.json'
    try:
        report = build_report(repo)
    except RuntimeError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    output_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'✓ Wrote diff report: {output_path}')
if __name__ == '__main__':
    raise SystemExit(main())
