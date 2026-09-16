#!/data/data/com.termux/files/home/.local/bin/python
"""py_dev.py – Py Dev utilities.

This module provides functionality for py dev."""
from __future__ import annotations
import subprocess
import sys
import venv
from pathlib import Path

class PythonDevSetup:
    """PythonDevSetup – PythonDevSetup."""
    DEV_PACKAGES = ['pre-commit']
    PRE_COMMIT_CONFIG = 'repos:\n  - repo: https://github.com/pre-commit/pre-commit-hooks\n    rev: v4.5.0\n    hooks:\n      - id: trailing-whitespace\n      - id: end-of-file-fixer\n      - id: check-yaml\n      - id: check-added-large-files\n      - id: check-merge-conflict\n      - id: debug-statements\n      - id: check-ast\n  - repo: https://github.com/astral-sh/ruff-pre-commit\n    rev: v0.3.7\n    hooks:\n      - id: ruff\n        args: [--fix, --exit-non-zero-on-fix]\n  - repo: https://github.com/psf/black-pre-commit\n    rev: 24.2.0\n    hooks:\n      - id: black\n  - repo: https://github.com/pycqa/isort\n    rev: 5.13.2\n    hooks:\n      - id: isort\n        args: ["--profile", "black"]\n  - repo: https://github.com/pre-commit/mirrors-mypy\n    rev: v1.8.0\n    hooks:\n      - id: mypy\n        additional_dependencies: [types-requests, types-python-dateutil]\n        args: [--ignore-missing-imports, --disallow-untyped-defs]\n        exclude: ^tests/\n'
    PYTHON_VERSION = '3.12.12'
    GITIGNORE_TEMPLATE = '# Byte-compiled / optimized / DLL files\n__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\nwheels/\n*.egg-info/\n.installed.cfg\n*.egg\n*.manifest\n*.spec\npip-log.txt\npip-delete-this-directory.txt\nhtmlcov/\n.tox/\n.nox/\n.coverage\n.coverage.*\n.cache\nnosetests.xml\ncoverage.xml\n*.cover\n*.py,cover\n.hypothesis/\n.pytest_cache/\n*.mo\n*.pot\n.env\n.venv\nenv/\nvenv/\nENV/\nenv.bak/\nvenv.bak/\n.idea/\n.vscode/\n*.swp\n*.swo\n*~\n.DS_Store\nThumbs.db\n*.log\nlogs/\n.env.local\n.env.*.local\n'

    def __init__(self, project_path: Path | None=None) -> None:
        """__init__ –   init  .

Args:
    project_path: Description of project_path."""
        self.project_path = project_path or Path.cwd()
        self.venv_path = self.project_path / '.venv'
        self.is_windows = sys.platform == 'win32'

    def check_python_version(self) -> bool:
        """check_python_version – check python version.

Returns:
    bool: Description of return value."""
        try:
            result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
            version_str = result.stdout.strip()
            print(f'Found Python: {version_str}')
            version = version_str.split()[-1]
            major, minor, _ = version.split('.')
            if int(major) >= 3 and int(minor) >= 11:
                return True
            else:
                print(f'Warning: Python {major}.{minor} detected. Recommended: Python 3.11+')
                return True
        except Exception as e:
            print(f'Error checking Python version: {e}')
            return False

    def create_project_structure(self) -> None:
        """create_project_structure – create project structure."""
        structure = {'src': [], 'tests': ['__init__.py', 'conftest.py'], 'docs': [], 'scripts': [], '.github/workflows': ['ci.yml']}
        print('\nCreating project structure...')
        for dir_path, files in structure.items():
            full_path = self.project_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            for file in files:
                (full_path / file).touch(exist_ok=True)
                print(f'  Created: {dir_path}/{file}')
            if not files:
                (full_path / '__init__.py').touch(exist_ok=True)
                print(f'  Created: {dir_path}/__init__.py')
        main_file = self.project_path / 'src' / 'main.py'
        if not main_file.exists():
            main_file.write_text(self._get_main_template())
            print(f'  Created: src/main.py')
        test_file = self.project_path / 'tests' / 'test_main.py'
        if not test_file.exists():
            test_file.write_text(self._get_test_template())
            print(f'  Created: tests/test_main.py')
        ci_file = self.project_path / '.github' / 'workflows' / 'ci.yml'
        if not ci_file.exists():
            ci_file.write_text(self._get_ci_template())
            print(f'  Created: .github/workflows/ci.yml')

    def _get_main_template(self) -> str:
        """_get_main_template –  get main template.

Returns:
    str: Description of return value."""
        return '"""Main module for the project."""\nfrom __future__ import annotations\ndef main() -> None:\n    print("Hello, Python!")\nif __name__ == "__main__":\n    main()\n'

    def _get_test_template(self) -> str:
        """_get_test_template –  get test template.

Returns:
    str: Description of return value."""
        return '"""Tests for the main module."""\nimport pytest\nfrom src.main import main\ndef test_main(capsys: pytest.CaptureFixture[str]) -> None:\n    main()\n    captured = capsys.readouterr()\n    assert captured.out.strip() == "Hello, Python!"\n'

    def _get_ci_template(self) -> str:
        """_get_ci_template –  get ci template.

Returns:
    str: Description of return value."""
        return 'name: Python CI\non:\n  push:\n    branches: [main, develop]\n  pull_request:\n    branches: [main]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python-version: ["3.11", "3.12"]\n    steps:\n      - uses: actions/checkout@v4\n      - name: Set up Python ${{ matrix.python-version }}\n        uses: actions/setup-python@v5\n        with:\n          python-version: ${{ matrix.python-version }}\n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install ruff black isort mypy pytest pytest-cov\n      - name: Lint with ruff\n        run: ruff check .\n      - name: Format check with black\n        run: black --check .\n      - name: Import sort check\n        run: isort --check-only .\n      - name: Type check with mypy\n        run: mypy src/\n      - name: Test with pytest\n        run: |\n          pip install -e .\n          pytest --cov=src --cov-report=xml tests/\n      - name: Upload coverage\n        uses: codecov/codecov-action@v3\n        with:\n          file: ./coverage.xml\n'

    def _get_python_path(self) -> str:
        """_get_python_path –  get python path.

Returns:
    str: Description of return value."""
        if self.venv_path.exists():
            if self.is_windows:
                return str(self.venv_path / 'Scripts' / 'python')
            else:
                return str(self.venv_path / 'bin' / 'python')
        return sys.executable

    def setup_pre_commit(self) -> bool:
        """setup_pre_commit – setup pre commit.

Returns:
    bool: Description of return value."""
        print('\nSetting up pre-commit hooks...')
        try:
            pre_commit_file = self.project_path / '.pre-commit-config.yaml'
            pre_commit_file.write_text(self.PRE_COMMIT_CONFIG)
            print('  Created: .pre-commit-config.yaml')
            python_version_file = self.project_path / '.python-version'
            python_version_file.write_text(self.PYTHON_VERSION)
            print(f'  Created: .python-version ({self.PYTHON_VERSION})')
            gitignore_file = self.project_path / '.gitignore'
            if not gitignore_file.exists():
                gitignore_file.write_text(self.GITIGNORE_TEMPLATE)
                print('  Created: .gitignore')
            subprocess.run(['pre-commit', 'install'], cwd=self.project_path, check=True)
            print('  Pre-commit hooks installed')
            subprocess.run(['pre-commit', 'run', '--all-files'], cwd=self.project_path)
            return True
        except Exception as e:
            print(f'  Error setting up pre-commit: {e}')
            return False

    def create_pyproject_toml(self) -> bool:
        """create_pyproject_toml – create pyproject toml.

Returns:
    bool: Description of return value."""
        print('\nCreating pyproject.toml...')
        pyproject_path = self.project_path / 'pyproject.toml'
        if pyproject_path.exists():
            print('  pyproject.toml already exists')
            return True
        content = f'[build-system]\nrequires = ["setuptools>=61.0", "wheel"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "{self.project_path.name}"\nversion = "1.4.7"\ndescription = "Python project"\nreadme = "README.md"\nrequires-python = ">=3.11"\nlicense = {{text = "MIT"}}\nauthors = [\n    {{name = "Your Name", email = "your.email@example.com"}}\n]\n[project.optional-dependencies]\ndev = [\n    "pyright",\n    "black",\n    "isort",\n    "mypy",\n    "debugpy",\n    "pytest",\n    "pytest-cov",\n    "pre-commit",\n    "pynvim",\n]\n[tool.setuptools.packages.find]\nwhere = ["src"]\n[tool.ruff]\nline-length = 120\ntarget-version = "py312"\nselect = ["E", "F", "I", "N", "W", "UP"]\nignore = ["E501"]\n[tool.ruff.isort]\nprofile = "black"\n[tool.black]\nline-length = 120\ntarget-version = ["py312"]\n[tool.isort]\nprofile = "black"\nline_length = 120\n[tool.mypy]\npython_version = "3.12"\nwarn_return_any = true\nwarn_unused_configs = true\ndisallow_untyped_defs = true\nignore_missing_imports = true\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\npython_files = ["test_*.py"]\npython_functions = ["test_*"]\naddopts = "-v --tb=short"\n[tool.coverage.run]\nsource = ["src"]\n[tool.coverage.report]\nexclude_lines = [\n    "pragma: no cover",\n    "def __repr__",\n    "raise NotImplementedError",\n    "if TYPE_CHECKING:",\n]\n'
        pyproject_path.write_text(content)
        print('  Created: pyproject.toml')
        return True

    def create_requirements_files(self) -> bool:
        """create_requirements_files – create requirements files.

Returns:
    bool: Description of return value."""
        print('\nCreating requirements files...')
        req_path = self.project_path / 'requirements.txt'
        if not req_path.exists():
            req_path.write_text('# Add your production dependencies here\n')
            print('  Created: requirements.txt')
        req_dev_path = self.project_path / 'requirements-dev.txt'
        if not req_dev_path.exists():
            dev_deps = '\n'.join(self.DEV_PACKAGES)
            req_dev_path.write_text(f'# Development dependencies\n{dev_deps}\n')
            print('  Created: requirements-dev.txt')
        return True

    def generate_neovim_config_info(self) -> bool:
        """generate_neovim_config_info – generate neovim config info.

Returns:
    bool: Description of return value."""
        print('\nCreating Neovim configuration info...')
        neovim_file = self.project_path / 'NEOVIM.md'
        if not neovim_file.exists():
            content = f'# Neovim Configuration for Python Development\nThis project uses **LazyVim** with a custom Python configuration.\n1. **Install Neovim** (v0.9+ recommended):\n   Linux/macOS:\n   brew install neovim  (macOS)\n   sudo apt install neovim  (Ubuntu/Debian)\n   Windows:\n   choco install neovim\n2. **Install LazyVim**:\n   mv ~/.config/nvim ~/.config/nvim.bak\n   git clone https://github.com/LazyVim/starter ~/.config/nvim\n   rm -rf ~/.config/nvim/.git\n3. **Add Python Configuration**:\n   Create ~/.config/nvim/lua/plugins/python.lua with the configuration.\n4. **Install Python LSP Tools**:\n   pip install pyright black isort debugpy pynvim\n| Key | Action |\n|-----|--------|\n| <leader>rp | Run current Python file |\n| <leader>rv | Run Python file (vertical split) |\n| <leader>rh | Run Python file (horizontal split) |\n| <leader>pi | Open Python REPL |\n| <leader>dc | Debug: Continue |\n| <leader>db | Debug: Toggle breakpoint |\n| <leader>dr | Debug: Open REPL |\n| <leader>di | Debug: Toggle UI |\n| <leader>tr | Run tests |\n| <leader>tf | Run tests for current file |\n| <leader>tt | Run all tests |\n| <leader>td | Debug tests |\n| <leader>cv | Create virtualenv |\nThe configuration automatically detects and uses virtual environments.\nTo create a virtual environment:\npython -m venv .venv\nsource .venv/bin/activate\nThe Python configuration includes:\n- LSP: Pyright + Ruff LSP\n- Formatting: Black + isort (via Conform.nvim)\n- Linting: Ruff (via nvim-lint)\n- Debugging: debugpy with DAP UI\n- Testing: neotest with pytest\n- Snippets: Python docstring and code snippets\n- Virtualenv: Automatic venv detection and creation\nLSP not working?\n:LspInfo\n:Mason\nFormatting not working?\n:ConformInfo\nDebugging not working?\n:DapInfo\n'
            neovim_file.write_text(content)
            print('  Created: NEOVIM.md')
        return True

    def run(self) -> bool:
        """run – run.

Returns:
    bool: Description of return value."""
        print('=' * 40)
        print('  Python Development Environment Setup')
        print('=' * 40)
        if not self.check_python_version():
            return False
        self.create_project_structure()
        if not self.create_pyproject_toml():
            return False
        if not self.create_requirements_files():
            return False
        if not self.setup_pre_commit():
            print('  Warning: Pre-commit setup failed, continuing...')
        if not self.generate_neovim_config_info():
            print('  Warning: Neovim info generation failed, continuing...')
        print('\n' + '=' * 40)
        print('  Setup Complete!')
        print('=' * 40)
        print(f'\nProject: {self.project_path}')
        print(f'Python: {self._get_python_path()}')
        print(f'Venv: {self.venv_path}')
        print('\nNext steps:')
        print('  1. Activate virtual environment:')
        if self.is_windows:
            print(f'     .\\{self.venv_path.name}\\Scripts\\activate')
        else:
            print(f'     source {self.venv_path.name}/bin/activate')
        print('  2. Start coding!')
        print('  3. Use pre-commit run --all-files to check everything')
        return True

def main() -> None:
    """main – main."""
    project_name = None
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    if project_name:
        project_path = Path(project_name)
        if not project_path.exists():
            project_path.mkdir(parents=True)
            print(f'Created project directory: {project_path}')
    else:
        print('Python Development Environment Setup')
        print('-' * 40)
        project_name = input('Enter project name (or press Enter for current directory): ').strip()
        if project_name:
            project_path = Path(project_name)
            if not project_path.exists():
                project_path.mkdir(parents=True)
                print(f'Created project directory: {project_path}')
        else:
            project_path = Path.cwd()
            print(f'Using current directory: {project_path}')
    setup = PythonDevSetup(project_path)
    success = setup.run()
    if not success:
        print('\nSetup failed. Check the error messages above.')
        sys.exit(1)
if __name__ == '__main__':
    main()
