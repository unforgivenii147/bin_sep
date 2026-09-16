#!/data/data/com.termux/files/home/.local/bin/python
"""mk_setup.py – Mk Setup utilities.

This module provides functionality for mk setup."""
from __future__ import annotations
from typing import Any
import os
import re
import sys
from pathlib import Path

def detect_entry_point(project_dir: Path | str, package_name: str) -> Any:
    """detect_entry_point – detect entry point.

Args:
    project_dir: Description of project_dir.
    package_name: Description of package_name."""
    project_path = Path(project_dir).resolve()
    main_file = project_path / package_name / '__main__.py'
    cli_file = project_path / package_name / 'cli.py'
    root_main = project_path / '__main__.py'
    root_cli = project_path / 'cli.py'
    entry_points = []
    if main_file.exists():
        entry_points.append({'module': f'{package_name}.__main__', 'function': 'main', 'script_name': package_name})
    if cli_file.exists():
        function_name = detect_main_function(cli_file)
        entry_points.append({'module': f'{package_name}.cli', 'function': function_name, 'script_name': package_name if not main_file.exists() else f'{package_name}-cli'})
    if root_main.exists() and (not entry_points):
        entry_points.append({'module': '__main__', 'function': 'main', 'script_name': package_name})
    if root_cli.exists() and (not entry_points):
        function_name = detect_main_function(root_cli)
        entry_points.append({'module': 'cli', 'function': function_name, 'script_name': package_name})
    return entry_points

def detect_main_function(path: Path | str) -> str:
    """detect_main_function – detect main function.

Args:
    path: Description of path."""
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        if re.search('def main\\(', content) or re.search('@click\\.\\w+', content) or re.search('import click', content):
            return 'main'
        elif re.search('def cli\\(', content):
            return 'cli'
        elif re.search('if __name__ == [\\\'"]__main__[\\\'"]:', content):
            return 'main'
        return 'main'
    except Exception:
        return 'main'

def find_requirements(project_dir: Path | str) -> Any:
    """find_requirements – find requirements.

Args:
    project_dir: Description of project_dir."""
    project_path = Path(project_dir).resolve()
    requirements = []
    req_files = ['requirements.txt', 'requirements.in', 'Pipfile']
    for req_file in req_files:
        req_path = project_path / req_file
        if req_path.exists():
            try:
                with open(req_path, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and (not line.startswith('#')) and (not line.startswith('-')):
                            if req_file == 'Pipfile':
                                if '=' in line and (not line.startswith('[')):
                                    pkg = line.split('=')[0].strip()
                                    if pkg:
                                        requirements.append(pkg)
                            else:
                                requirements.append(line)
            except Exception:
                pass
            break
    return requirements

def generate_setup_py(project_dir: Path | str, package_name: str, entry_points: Any, requirements: Any) -> Any:
    """generate_setup_py – generate setup py.

Args:
    project_dir: Description of project_dir.
    package_name: Description of package_name.
    entry_points: Description of entry_points.
    requirements: Description of requirements."""
    entry_points_str = ''
    if entry_points:
        console_scripts = []
        for ep in entry_points:
            console_scripts.append(f"{ep['script_name']}={ep['module']}:{ep['function']}")
        entry_points_str = '    entry_points={\n'
        entry_points_str += "        'console_scripts': [\n"
        for script in console_scripts:
            entry_points_str += f"            '{script}',\n"
        entry_points_str += '        ],\n'
        entry_points_str += '    },\n'
    install_requires = '    install_requires=[],\n'
    if requirements:
        install_requires = '    install_requires=[\n'
        for req in requirements:
            install_requires += f"        '{req}',\n"
        install_requires += '    ],\n'
    readme_content = ''
    readme_path = Path(project_dir) / 'README.md'
    if readme_path.exists():
        readme_content = "    long_description=open('README.md').read(),\n"
        readme_content += "    long_description_content_type='text/markdown',\n"
    setup_content = f"from setuptools import setup, find_packages\nsetup(\n    name='{package_name}',\n    version='1.4.7',\n    description='{package_name} - A Python project',\n    author='Your Name',\n    author_email='your.email@example.com',\n    url='',\n    packages=find_packages(),\n{install_requires}{readme_content}{entry_points_str}    python_requires='>=3.6',\n    classifiers=[\n        'Development Status :: 3 - Alpha',\n        'Intended Audience :: Developers',\n        'Programming Language :: Python :: 3',\n        'Programming Language :: Python :: 3.6',\n        'Programming Language :: Python :: 3.7',\n        'Programming Language :: Python :: 3.8',\n        'Programming Language :: Python :: 3.9',\n        'Programming Language :: Python :: 3.10',\n        'Programming Language :: Python :: 3.11',\n    ],\n)\n"
    return setup_content

def main() -> None:
    """main – main."""
    if len(sys.argv) != 2:
        print('Usage: python create_setup.py <project_directory>')
        sys.exit(1)
    project_dir = sys.argv[1]
    if not os.path.exists(project_dir):
        print(f"Error: Directory '{project_dir}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(project_dir):
        print(f"Error: '{project_dir}' is not a directory.")
        sys.exit(1)
    package_name = os.path.basename(os.path.abspath(project_dir))
    print(f'Package name: {package_name}')
    entry_points = detect_entry_point(project_dir, package_name)
    if not entry_points:
        print('Warning: No __main__.py or cli.py found.')
        print('Creating setup.py without console_scripts entry points.')
    else:
        print('Detected entry points:')
        for ep in entry_points:
            print(f"  - {ep['script_name']} -> {ep['module']}:{ep['function']}")
    requirements = find_requirements(project_dir)
    if requirements:
        print(f'\nFound {len(requirements)} requirements in requirements files.')
    setup_content = generate_setup_py(project_dir, package_name, entry_points, requirements)
    setup_path = os.path.join(project_dir, 'setup.py')
    with open(setup_path, 'w', encoding='utf-8') as f:
        f.write(setup_content)
    print(f'\n✓ Created {setup_path}')
    print('\nGenerated setup.py content preview:')
    print('-' * 40)
    print(setup_content)
if __name__ == '__main__':
    raise SystemExit(main())
