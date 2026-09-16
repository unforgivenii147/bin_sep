#!/data/data/com.termux/files/home/.local/bin/python
"""init_project.py – Init Project utilities.

This module provides functionality for init project."""
from __future__ import annotations
import argparse
from pathlib import Path

def load_user_info() -> dict[str, str]:
    """load_user_info – load user info.

Returns:
    dict[str, str]: Description of return value."""
    import json
    info_path = Path.home() / '.myinfo'
    info = {}
    if not info_path.exists():
        return info
    with info_path.open(encoding='utf-8') as f:
        info = json.load(f)
    return info

def write_file_if_missing(path: Path, content: str='') -> None:
    """write_file_if_missing – write file if missing.

Args:
    path: Description of path.
    content: Description of content."""
    if not path.exists():
        path.write_text(content)

def create_pyproject(pkg: str, version: str, author: str, email: str, url: str, description: str, simple_cli: bool, python_requires: str='>=3.11') -> str:
    """create_pyproject – create pyproject.

Args:
    pkg: Description of pkg.
    version: Description of version.
    author: Description of author.
    email: Description of email.
    url: Description of url.
    description: Description of description.
    simple_cli: Description of simple_cli.
    python_requires: Description of python_requires.

Returns:
    str: Description of return value."""
    import_name = pkg.replace('-', '_')
    lines = ['[build-system]', 'requires = ["setuptools>=68"]', 'build-backend = "setuptools.build_meta"', '', '[project]', f'name = "{pkg}"', f'version = "{version}"']
    if description:
        lines.append(f'description = "{description}"')
    if author:
        lines.append(f'authors = [{{name = "{author}"')
        if email:
            lines[-1] += f', email = "{email}"'
        lines[-1] += '}]'
    elif email:
        lines.append(f'authors = [{{email = "{email}"}}]')
    if url:
        lines.extend(['', '[project.urls]', f'Homepage = "{url}"'])
    lines.extend(['', f'requires-python = "{python_requires}"', 'dependencies = []', '', '[tool.setuptools.packages.find]', 'where = ["src"]'])
    if simple_cli:
        lines.extend(['', '[project.scripts]', f'{pkg} = "{import_name}:main"'])
    return '\n'.join(lines) + '\n'

def create_project_structure(pkg: str, author: str, email: str, url: str, description: str, simple_cli: bool, version: str='0.1.0') -> None:
    """create_project_structure – create project structure.

Args:
    pkg: Description of pkg.
    author: Description of author.
    email: Description of email.
    url: Description of url.
    description: Description of description.
    simple_cli: Description of simple_cli.
    version: Description of version."""
    cwd = Path.cwd() / pkg
    cwd.mkdir(exist_ok=True)
    import_name = pkg.replace('-', '_')
    write_file_if_missing(cwd / 'README.md', f'# {pkg}\n')
    write_file_if_missing(cwd / '.gitignore', _GITIGNORE_CONTENT)
    write_file_if_missing(cwd / 'LICENSE', '')
    (cwd / 'pyproject.toml').write_text(create_pyproject(pkg, version, author, email, url, description, simple_cli))
    src_pkg = cwd / 'src' / import_name
    src_pkg.mkdir(parents=True, exist_ok=True)
    write_file_if_missing(src_pkg / '__init__.py', f'__version__ = "{version}"\n')
    if simple_cli:
        write_file_if_missing(src_pkg / '__main__.py', f'"""CLI entry point for {pkg}."""\nimport sys\ndef main() -> int:\n    """Main entry point. Returns process exit code."""\n    print(f"Hello from {pkg}!")\n    return 0\nif __name__ == "__main__":\n    raise SystemExit(main())\n')
    tests = cwd / 'tests'
    tests.mkdir(exist_ok=True)
    write_file_if_missing(tests / '__init__.py')
    write_file_if_missing(tests / f'test_{import_name}.py', f'def test_version():\n    from {import_name} import __version__\n    assert __version__ == "{version}"\n')
    print(f"Project '{pkg}' initialized in {cwd}")
    print(f"  - pyproject.toml with {('CLI entry point' if simple_cli else 'no CLI')}")
    print('  - src/ layout with setuptools auto-discovery')
    print('  - tests/ directory with a smoke test')
_GITIGNORE_CONTENT = '__pycache__/\n*.py[cod]\n*.egg-info/\ndist/\nbuild/\n.venv/\nvenv/\nenv/\n.mypy_cache/\n.ruff_cache/\n.pytest_cache/\n.coverage\n'

def main() -> None:
    """main – main."""
    user_info = load_user_info()
    parser = argparse.ArgumentParser(description='Initialize a modern Python project with pyproject.toml')
    parser.add_argument('name', help='Package name (e.g., my-package)')
    parser.add_argument('--version', default='0.1.0', help='Initial version (default: 0.1.0)')
    parser.add_argument('-d', '--description', default='', help='One-line project description')
    parser.add_argument('-s', '--simple-cli', action='store_true', help='Create a console_scripts entry point + __main__.py')
    args = parser.parse_args()
    author = user_info.get('name', '')
    email = user_info.get('email', '')
    github_user = user_info.get('github_username', '')
    url = f'https://github.com/{github_user}/{args.name}' if github_user else ''
    create_project_structure(args.name, author, email, url, args.description, args.simple_cli, args.version)
if __name__ == '__main__':
    raise SystemExit(main())
