#!/data/data/com.termux/files/home/.local/bin/python
"""
Automatically create a new Git branch for the current month.
Branch format: august_2026, september_2026, etc.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_PATH = Path.home() / "bin"
MAIN_BRANCH = "main"  # Change to "master" if needed


def get_branch_name() -> str:
    """Generate branch name like 'august_2026'."""
    now = datetime.now()
    return f"{now.strftime('%B').lower()}_{now.year}"


def branch_exists(branch_name: str) -> bool:
    """Check if branch exists locally or remotely."""
    try:
        # Check local branches
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
        )
        if branch_name in result.stdout:
            return True

        # Check remote branches
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
        )
        return f"refs/heads/{branch_name}" in result.stdout
    except Exception:
        return False


def create_monthly_branch() -> bool:
    """Create new branch for current month."""
    branch_name = get_branch_name()

    print(f"Creating branch for {branch_name}...")

    # Check if already exists
    if branch_exists(branch_name):
        print(f"✓ Branch '{branch_name}' already exists")
        return True

    try:
        # Fetch latest changes
        subprocess.run(
            ["git", "fetch", "--all"], cwd=REPO_PATH, check=True, capture_output=True
        )

        # Checkout main branch
        subprocess.run(
            ["git", "checkout", MAIN_BRANCH],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )

        # Pull latest changes
        subprocess.run(["git", "pull"], cwd=REPO_PATH, check=True, capture_output=True)

        # Create and push new branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )

        # Go back to main
        subprocess.run(
            ["git", "checkout", MAIN_BRANCH],
            cwd=REPO_PATH,
            check=True,
            capture_output=True,
        )

        print(f"✓ Created and pushed branch: {branch_name}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e.stderr.decode() if e.stderr else str(e)}")
        return False


if __name__ == "__main__":
    if not (REPO_PATH / ".git").exists():
        print(f"Error: {REPO_PATH} is not a Git repository")
        sys.exit(1)

    success = create_monthly_branch()
    sys.exit(0 if success else 1)
