#!/data/data/com.termux/files/home/.local/bin/python
"""create_setuppy.py – Create Setuppy utilities.

This module provides functionality for create setuppy."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from typing import Any
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

def parse_args() -> argparse.Namespace:
    """parse_args – parse args.

Returns:
    argparse.Namespace: Description of return value."""
    parser = argparse.ArgumentParser(description='Generate setup.py from pyproject.toml.')
    parser.add_argument('project_dir', nargs='?', type=Path, default=Path('.'), help='Project directory. Defaults to the current directory.')
    parser.add_argument('-o', '--output', type=Path, default=None, help='Output setup.py path. Defaults to PROJECT_DIR/setup.py.')
    parser.add_argument('--force', action='store_true', help='Overwrite an existing setup.py.')
    return parser.parse_args()

def read_pyproject(project_dir: Path) -> dict[str, Any]:
    """read_pyproject – read pyproject.

Args:
    project_dir: Description of project_dir.

Returns:
    dict[str, Any]: Description of return value."""
    path = project_dir / 'pyproject.toml'
    if not path.is_file():
        raise FileNotFoundError(f'Missing pyproject.toml: {path}')
    with path.open('rb') as file:
        return tomllib.load(file)

def get_backend(data: dict[str, Any]) -> str:
    """get_backend – get backend.

Args:
    data: Description of data.

Returns:
    str: Description of return value."""
    try:
        return data['build-system']['build-backend']
    except KeyError as error:
        raise ValueError('pyproject.toml does not define [build-system].build-backend') from error

def dotted_to_path(name: str) -> str:
    """dotted_to_path – dotted to path.

Args:
    name: Description of name.

Returns:
    str: Description of return value."""
    return name.replace('.', '/').replace('-', '_')

def canonical_package_name(name: str) -> str:
    """canonical_package_name – canonical package name.

Args:
    name: Description of name.

Returns:
    str: Description of return value."""
    return re.sub('[-.]+', '_', name).lower()

def package_discovery_code(project_dir_name: str, package_name: str | None=None) -> str:
    """package_discovery_code – package discovery code.

Args:
    project_dir_name: Description of project_dir_name.
    package_name: Description of package_name.

Returns:
    str: Description of return value."""
    if package_name:
        package_name_literal = repr(package_name)
        return f'\nfrom pathlib import Path\nfrom setuptools import find_packages\n_project_root = Path(__file__).parent\n_package_name = {package_name_literal}\nif (_project_root / _package_name).is_dir():\n    packages = find_packages(\n        where=str(_project_root),\n        include=(_package_name, f"{{_package_name}}.*"),\n    )\n    package_dir = {{}}\nelif (_project_root / "src" / _package_name).is_dir():\n    packages = find_packages(\n        where=str(_project_root / "src"),\n        include=(_package_name, f"{{_package_name}}.*"),\n    )\n    package_dir = {{"": "src"}}\nelse:\n    packages = []\n    package_dir = {{}}\n'.strip()
    return '\nfrom pathlib import Path\nfrom setuptools import find_packages\n_project_root = Path(__file__).parent\nif (_project_root / "src").is_dir():\n    packages = find_packages(where=str(_project_root / "src"))\n    package_dir = {"": "src"}\nelse:\n    packages = find_packages(where=str(_project_root))\n    package_dir = {}\n'.strip()

def literal(value: Any) -> str:
    """literal – literal.

Args:
    value: Description of value.

Returns:
    str: Description of return value."""
    return repr(value)

def authors_to_setup(project: dict[str, Any]) -> dict[str, str]:
    """authors_to_setup – authors to setup.

Args:
    project: Description of project.

Returns:
    dict[str, str]: Description of return value."""
    authors = project.get('authors', [])
    names = [author['name'] for author in authors if isinstance(author, dict) and author.get('name')]
    emails = [author['email'] for author in authors if isinstance(author, dict) and author.get('email')]
    result: dict[str, str] = {}
    if names:
        result['author'] = ', '.join(names)
    if emails:
        result['author_email'] = ', '.join(emails)
    return result

def pep621_metadata(project: dict[str, Any]) -> dict[str, Any]:
    """pep621_metadata – pep621 metadata.

Args:
    project: Description of project.

Returns:
    dict[str, Any]: Description of return value."""
    metadata: dict[str, Any] = {'name': project['name']}
    for key in ('version', 'description', 'readme', 'license', 'requires-python', 'dependencies', 'optional-dependencies', 'classifiers', 'keywords'):
        if key in project:
            metadata[key] = project[key]
    metadata.update(authors_to_setup(project))
    urls = project.get('urls', {})
    if 'Homepage' in urls:
        metadata['url'] = urls['Homepage']
    scripts = project.get('scripts', {})
    if scripts:
        metadata['entry_points'] = {'console_scripts': [f'{name} = {target}' for name, target in scripts.items()]}
    return metadata

def poetry_metadata(poetry: dict[str, Any]) -> dict[str, Any]:
    """poetry_metadata – poetry metadata.

Args:
    poetry: Description of poetry.

Returns:
    dict[str, Any]: Description of return value."""
    metadata: dict[str, Any] = {'name': poetry['name'], 'version': poetry['version'], 'description': poetry.get('description', '')}
    authors = poetry.get('authors', [])
    names: list[str] = []
    emails: list[str] = []
    for author in authors:
        match = re.match('^\\s*(.*?)\\s*<([^>]+)>\\s*$', author)
        if match:
            names.append(match.group(1))
            emails.append(match.group(2))
        else:
            names.append(author)
    if names:
        metadata['author'] = ', '.join(names)
    if emails:
        metadata['author_email'] = ', '.join(emails)
    for poetry_key, setup_key in (('homepage', 'url'), ('classifiers', 'classifiers'), ('keywords', 'keywords'), ('readme', 'long_description'), ('dependencies', 'install_requires')):
        if poetry_key in poetry:
            metadata[setup_key] = poetry[poetry_key]
    scripts = poetry.get('scripts', {})
    if scripts:
        metadata['entry_points'] = {'console_scripts': [f'{name} = {target}' for name, target in scripts.items()]}
    return metadata

def normalize_poetry_dependencies(dependencies: dict[str, Any]) -> list[str]:
    """normalize_poetry_dependencies – normalize poetry dependencies.

Args:
    dependencies: Description of dependencies.

Returns:
    list[str]: Description of return value."""
    requirements: list[str] = []
    for name, value in dependencies.items():
        if name == 'python':
            continue
        if isinstance(value, str):
            if value == '*':
                requirements.append(name)
            else:
                requirements.append(f'{name}{value}')
            continue
        if isinstance(value, dict):
            version = value.get('version', '')
            extras = value.get('extras', [])
            requirement = name
            if extras:
                requirement += f"[{','.join(extras)}]"
            if version and version != '*':
                requirement += version
            requirements.append(requirement)
    return requirements

def setup_keyword_arguments(metadata: dict[str, Any]) -> str:
    """setup_keyword_arguments – setup keyword arguments.

Args:
    metadata: Description of metadata.

Returns:
    str: Description of return value."""
    lines: list[str] = []
    simple_mappings = {'name': 'name', 'version': 'version', 'description': 'description', 'author': 'author', 'author_email': 'author_email', 'url': 'url', 'classifiers': 'classifiers', 'keywords': 'keywords', 'install_requires': 'install_requires', 'python_requires': 'python_requires', 'long_description': 'long_description'}
    for source_key, setup_key in simple_mappings.items():
        if source_key not in metadata:
            continue
        value = metadata[source_key]
        if source_key == 'readme':
            continue
        if source_key == 'requires-python':
            setup_key = 'python_requires'
        if source_key == 'dependencies':
            setup_key = 'install_requires'
        if source_key == 'optional-dependencies':
            continue
        lines.append(f'    {setup_key}={literal(value)},')
    if 'entry_points' in metadata:
        lines.append(f"    entry_points={literal(metadata['entry_points'])},")
    optional = metadata.get('optional-dependencies', {})
    if optional:
        extras_require = {group: values for group, values in optional.items()}
        lines.append(f'    extras_require={literal(extras_require)},')
    return '\n'.join(lines)

def generate_setup_py(data: dict[str, Any], project_dir: Path) -> str:
    """generate_setup_py – generate setup py.

Args:
    data: Description of data.
    project_dir: Description of project_dir.

Returns:
    str: Description of return value."""
    backend = get_backend(data)
    project = data.get('project')
    poetry = data.get('tool', {}).get('poetry')
    if project is not None:
        metadata = pep621_metadata(project)
        package_name = project['name']
    elif poetry is not None:
        metadata = poetry_metadata(poetry)
        if isinstance(poetry.get('dependencies'), dict):
            metadata['install_requires'] = normalize_poetry_dependencies(poetry['dependencies'])
        package_name = canonical_package_name(poetry['name'])
    else:
        raise ValueError('This script requires either [project] or [tool.poetry] metadata.')
    package_code = package_discovery_code(project_dir.name, package_name)
    keyword_arguments = setup_keyword_arguments(metadata)
    backend_comment = f'# Original build backend: {backend}'
    return f'"""Generated setup.py.\n{backend_comment}\nGenerated by create_setup.py.\n"""\nfrom setuptools import setup\n{package_code}\nsetup(\n{keyword_arguments}\n    packages=packages,\n    package_dir=package_dir,\n)\n'

def main() -> int:
    """main – main.

Returns:
    int: Description of return value."""
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()
    output_path = args.output.expanduser().resolve() if args.output is not None else project_dir / 'setup.py'
    if output_path.exists() and (not args.force):
        raise FileExistsError(f'{output_path} already exists; use --force to overwrite it')
    data = read_pyproject(project_dir)
    generated = generate_setup_py(data, project_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generated, encoding='utf-8')
    print(f'Created {output_path}')
    return 0
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, KeyError) as error:
        print(f'error: {error}', file=sys.stderr)
        raise SystemExit(1)
