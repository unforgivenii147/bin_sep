#!/data/data/com.termux/files/home/.local/bin/python
"""
Set up an encrypted dotfiles repo in $HOME using git + age + a Python filter.

What it does:
  1. Verifies age + git are installed.
  2. Generates an age keypair (if missing) at ~/.config/age/.
  3. Writes the git filter script to ~/.local/bin/git-age-filter.
  4. Creates .gitattributes and .gitignore in $HOME.
  5. Initializes a bare repo at ~/dotfiles.git using a work-tree=$HOME setup.
  6. Registers the age clean/smudge filters in the repo config.
  7. Prints next steps.
"""
from __future__ import annotations
from typing import Any
import os
import shutil
import subprocess
import sys
import textwrap
HOME = os.path.expanduser('~')
AGE_DIR = os.path.join(HOME, '.config', 'age')
AGE_KEY = os.path.join(AGE_DIR, 'keys.txt')
AGE_PUB = os.path.join(AGE_DIR, 'public.key')
FILTER_PATH = os.path.join(HOME, '.local', 'bin', 'git-age-filter')
REPO_DIR = os.path.join(HOME, 'dotfiles.git')
GITATTRIBUTES = os.path.join(HOME, '.gitattributes')
GITIGNORE = os.path.join(HOME, '.gitignore')
SECRET_PATTERNS = ['secrets/**', '*.secret', '.env', '*.token']
IGNORE_PATTERNS = ['.config/age/', 'dotfiles.git/', 'storage/', '*.log', '.cache/']

def run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess:
    """run – run.

Args:
    cmd: Description of cmd.
    **kw: Description of **kw.

Returns:
    subprocess.CompletedProcess: Description of return value."""
    return subprocess.run(cmd, check=True, **kw)

def which(binary: str) -> str | None:
    """which – which.

Args:
    binary: Description of binary.

Returns:
    str | None: Description of return value."""
    return shutil.which(binary) or (os.path.exists(f'/data/data/com.termux/files/usr/bin/{binary}') and f'/data/data/com.termux/files/usr/bin/{binary}')

def ensure_tools() -> None:
    """ensure_tools – ensure tools."""
    missing = [b for b in ('age', 'age-keygen', 'git') if not which(b)]
    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print('Install with:  pkg install age git')
        sys.exit(1)

def ensure_age_key() -> str:
    """ensure_age_key – ensure age key.

Returns:
    str: Description of return value."""
    os.makedirs(AGE_DIR, mode=448, exist_ok=True)
    if not os.path.exists(AGE_KEY):
        print('Generating age keypair...')
        out = subprocess.run([which('age-keygen') or 'age-keygen', '-o', AGE_KEY], capture_output=True)
        if out.returncode != 0:
            print(out.stderr.decode(), file=sys.stderr)
            sys.exit(1)
        os.chmod(AGE_KEY, 384)
    pubkey = None
    with open(AGE_KEY) as f:
        for line in f:
            if line.startswith('# public key:'):
                pubkey = line.split(':', 1)[1].strip()
                break
    if not pubkey:
        print('Could not find public key in keys.txt', file=sys.stderr)
        sys.exit(1)
    with open(AGE_PUB, 'w') as f:
        f.write(pubkey + '\n')
    os.chmod(AGE_PUB, 420)
    print(f'age public key: {pubkey}')
    return pubkey
FILTER_SOURCE = '#!/data/data/com.termux/files/usr/bin/python\n"""Git clean/smudge filter using age. Managed by setup_dotfiles.py."""\nimport os, subprocess, sys\n\nAGE_BIN = "age"\nAGE_KEY_FILE = os.path.expanduser("~/.config/age/keys.txt")\nAGE_PUBKEY_FILE = os.path.expanduser("~/.config/age/public.key")\n\n\ndef die(msg, code=1):\n    print(f"git-age-filter: {msg}", file=sys.stderr)\n    sys.exit(code)\n\n\ndef clean():\n    if not os.path.exists(AGE_PUBKEY_FILE):\n        die(f"missing public key: {AGE_PUBKEY_FILE}")\n    pubkey = open(AGE_PUBKEY_FILE).read().strip()\n    p = subprocess.run([AGE_BIN, "-r", pubkey, "-a"],\n                       input=sys.stdin.buffer.read(),\n                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n    if p.returncode != 0:\n        die(f"encrypt failed: {p.stderr.decode(errors=\'replace\')}")\n    sys.stdout.buffer.write(p.stdout)\n\n\ndef smudge():\n    data = sys.stdin.buffer.read()\n    if not data.lstrip().startswith(b"-----BEGIN AGE ENCRYPTED FILE-----"):\n        sys.stdout.buffer.write(data); return\n    if not os.path.exists(AGE_KEY_FILE):\n        print("git-age-filter: no private key; leaving ciphertext", file=sys.stderr)\n        sys.stdout.buffer.write(data); return\n    p = subprocess.run([AGE_BIN, "-d", "-i", AGE_KEY_FILE],\n                       input=data,\n                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n    if p.returncode != 0:\n        die(f"decrypt failed: {p.stderr.decode(errors=\'replace\')}")\n    sys.stdout.buffer.write(p.stdout)\n\n\nif __name__ == "__main__":\n    if len(sys.argv) != 2 or sys.argv[1] not in ("clean", "smudge"):\n        die("usage: git-age-filter {clean|smudge}")\n    (clean if sys.argv[1] == "clean" else smudge)()\n'

def write_filter() -> None:
    """write_filter – write filter."""
    os.makedirs(os.path.dirname(FILTER_PATH), exist_ok=True)
    with open(FILTER_PATH, 'w') as f:
        f.write(FILTER_SOURCE)
    os.chmod(FILTER_PATH, 493)
    print(f'wrote filter: {FILTER_PATH}')

def write_gitattributes() -> None:
    """write_gitattributes – write gitattributes."""
    lines = ['# Managed by setup_dotfiles.py — encrypted via age filter']
    lines += [f'{p} filter=age diff=age' for p in SECRET_PATTERNS]
    with open(GITATTRIBUTES, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'wrote: {GITATTRIBUTES}')

def write_gitignore() -> None:
    """write_gitignore – write gitignore."""
    existing = ''
    if os.path.exists(GITIGNORE):
        existing = open(GITIGNORE).read()
    lines = ['# Managed by setup_dotfiles.py']
    lines += [p for p in IGNORE_PATTERNS if p not in existing]
    mode = 'a' if existing else 'w'
    with open(GITIGNORE, mode) as f:
        if existing and (not existing.endswith('\n')):
            f.write('\n')
        f.write('\n'.join(lines) + '\n')
    print(f'updated: {GITIGNORE}')

def git(*args: str, cwd: str | None=None) -> None:
    """git – git.

Args:
    cwd: Description of cwd.
    *args: Description of *args."""
    cmd = ['git', f'--git-dir={REPO_DIR}', f'--work-tree={HOME}', *args]
    subprocess.run(cmd, check=True, cwd=cwd)

def init_repo() -> None:
    """init_repo – init repo."""
    if not os.path.isdir(REPO_DIR):
        run(['git', 'init', '--bare', REPO_DIR])
        print(f'initialized bare repo: {REPO_DIR}')
    git('config', 'filter.age.clean', FILTER_PATH + ' clean')
    git('config', 'filter.age.smudge', FILTER_PATH + ' smudge')
    git('config', 'filter.age.required', 'true')
    git('config', 'diff.age.textconv', FILTER_PATH + ' smudge')
    git('config', 'status.showUntrackedFiles', 'no')
    git('config', 'core.excludesfile', GITIGNORE)
    print('registered age clean/smudge filters')

def main() -> None:
    """main – main."""
    ensure_tools()
    ensure_age_key()
    write_filter()
    write_gitattributes()
    write_gitignore()
    init_repo()
    print(textwrap.dedent(f"""\n    ✅ Setup complete.\n\n    Your repo is a bare repo at:\n        {REPO_DIR}\n    with work-tree = {HOME}\n\n    Add this alias to ~/.bashrc (or ~/.zshrc):\n\n        alias dot='git --git-dir=$HOME/dotfiles.git --work-tree=$HOME'\n\n    Then:\n\n        dot add .gitattributes .gitignore\n        dot add .bashrc .zshrc .config/nvim secrets/api-keys.env\n        dot commit -m "initial dotfiles (encrypted secrets)"\n        dot remote add origin <your-repo-url>\n        dot push -u origin main\n\n    Verify a secret is encrypted before pushing:\n\n        dot show HEAD:secrets/api-keys.env\n        # should print -----BEGIN AGE ENCRYPTED FILE-----\n\n    🔑 BACK UP {AGE_KEY} somewhere safe (password manager).\n    Lose it and the encrypted files are unrecoverable.\n    """))
if __name__ == '__main__':
    main()
