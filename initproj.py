#!/data/data/com.termux/files/home/.local/bin/python
"""initproj.py – Initproj utilities.

This module provides functionality for initproj."""
from __future__ import annotations
import sys
from pathlib import Path

def create_file(path: Path, content: str) -> None:
    """create_file – create file.

Args:
    path: Description of path.
    content: Description of content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + '\n', encoding='utf-8')
    print(f'Created: {path}')

def main() -> None:
    """main – main."""
    project_name = input('Enter project name (e.g., my-cli-tool): ').strip().replace(' ', '-')
    if not project_name:
        print('Project name cannot be empty.')
        sys.exit(1)
    pkg_name = project_name.replace('-', '_')
    author_name = input('Enter author name: ').strip() or 'Your Name'
    author_email = input('Enter author email: ').strip() or 'author@example.com'
    root = Path(project_name)
    if root.exists():
        print(f"Error: Directory '{project_name}' already exists.")
        sys.exit(1)
    print(f"\nScaffolding modern '{project_name}' layout with Typer CLI...")
    pyproject_content = f'''\n[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n[project]\nname = "{project_name}"\ndynamic = ["version"]\ndescription = "A standard library and CLI tool built with Typer."\nreadme = "README.md"\nrequires-python = ">=3.10"\nauthors = [\n    {{ name = "{author_name}", email = "{author_email}" }}\n]\nclassifiers = [\n    "Programming Language :: Python :: 3",\n    "License :: OSI Approved :: MIT License",\n    "Operating System :: OS Independent",\n]\ndependencies = [\n    "typer>=0.12.0",\n    "rich>=13.0.0",\n]\n[project.optional-dependencies]\ndev = [\n    "pytest>=8.0.0",\n    "black>=24.0.0",\n    "flake8>=7.0.0",\n]\n[project.scripts]\n{project_name} = "{pkg_name}.cli:app"\n{project_name}-admin = "{pkg_name}.admin:app"\n[tool.hatch.version]\npath = "src/{pkg_name}/__init__.py"\n[tool.black]\nline-length = 88\ntarget-version = ['py310']\n'''
    init_content = '__version__ = "0.1.0"'
    cli_content = f'\nimport typer\nfrom rich import print\napp = typer.Typer(help="Main CLI for {project_name}")\n@app.command()\ndef hello(name: str = typer.Argument("World", help="The name to greet")):\n    """Greet someone politely."""\n    print(f"[bold green]Hello[/bold green] [cyan]{{name}}[/cyan]! Welcome to {project_name}.")\n@app.command()\ndef version():\n    """Show tool version."""\n    from {pkg_name} import __version__\n    print(f"{project_name} version: [yellow]{{__version__}}[/yellow]")\nif __name__ == "__main__":\n    app()\n'
    admin_content = f'\nimport typer\nfrom rich import print\napp = typer.Typer(help="Administrative commands for {project_name}")\n@app.command()\ndef setup():\n    """Initialize application system configs."""\n    print("[bold yellow]Initializing secure admin layout... Done.[/bold yellow]")\nif __name__ == "__main__":\n    app()\n'
    readme_content = f'\nA cookiecutter-pypackage styled boilerplate library including dual CLI entrypoints powered by Typer.\n```bash\npip install .\n```\nFor development installations:\n```bash\npip install -e ".[dev]"\n```\n```bash\n{project_name} hello --name Alice\n```\n```bash\n{project_name}-admin setup\n```\n- Run tests: `pytest`\n- Format code: `black .`\n'
    test_content = f'\nfrom typer.testing import CliRunner\nfrom {pkg_name}.cli import app\nrunner = CliRunner()\ndef test_hello_endpoint():\n    result = runner.invoke(app, ["hello", "Tester"])\n    assert result.exit_code == 0\n    assert "Hello Tester!" in result.stdout\n'
    create_file(root / 'pyproject.toml', pyproject_content)
    create_file(root / 'README.md', readme_content)
    create_file(root / 'src' / pkg_name / '__init__.py', init_content)
    create_file(root / 'src' / pkg_name / 'cli.py', cli_content)
    create_file(root / 'src' / pkg_name / 'admin.py', admin_content)
    create_file(root / 'tests' / '__init__.py', '')
    create_file(root / 'tests' / 'test_cli.py', test_content)
    print(f"\n[Success] Your library template '{project_name}' has been created successfully!")
    print(f'Next steps:\n  cd {project_name}\n  pip install -e .[dev]\n  pytest')
if __name__ == '__main__':
    main()
