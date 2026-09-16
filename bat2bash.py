#!/data/data/com.termux/files/home/.local/bin/python
"""bat2bash.py – Bat2Bash utilities.

This module provides functionality for bat2bash."""
from __future__ import annotations
import re
import sys
from pathlib import Path

class BatToShConverter:
    """BatToShConverter – BatToShConverter."""
    COMMAND_MAP: dict[str, str] = {'^echo\\s+off\\s*$': '# Echo off', '^@echo\\s+off\\s*$': '# Echo off', '^pause\\s*$': 'read -p "Press enter to continue..."', '^cls\\s*$': 'clear', '^exit\\s*$': 'exit 0', '^cd\\s+': 'cd ', '^dir\\s*$': 'ls -la', '^dir\\s+': 'ls -la ', '^del\\s+': 'rm ', '^copy\\s+': 'cp ', '^move\\s+': 'mv ', '^ren\\s+': 'mv ', '^type\\s+': 'cat ', '^findstr\\s+': 'grep ', '^if\\s+exist\\s+': 'if [ -f ', '^if\\s+not\\s+exist\\s+': 'if [ ! -f '}

    def __init__(self) -> None:
        """__init__ –   init  ."""
        self.converted_count = 0
        self.error_count = 0

    def convert_line(self, line: str) -> str:
        """convert_line – convert line.

Args:
    line: Description of line.

Returns:
    str: Description of return value."""
        line = line.rstrip('\r\n')
        if not line.strip() or line.strip().startswith('REM'):
            if line.strip().startswith('REM'):
                return line.replace('REM', '#', 1)
            return line
        line = re.sub('%([A-Za-z_][A-Za-z0-9_]*)%', '$\\1', line)
        line = re.sub('^set\\s+', '', line, flags=re.IGNORECASE)
        line = re.sub('if\\s+"?([^"]*?)"?\\s+==\\s+"?([^"]*?)"?', 'if [ "$\\1" = "$\\2" ]', line, flags=re.IGNORECASE)
        for pattern, replacement in self.COMMAND_MAP.items():
            if re.match(pattern, line, re.IGNORECASE):
                line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                break
        line = re.sub('^:\\w+\\s*$', lambda m: f'# {m.group(0)}', line)
        line = re.sub('goto\\s+(\\w+)', '# TODO: goto \\1', line, flags=re.IGNORECASE)
        return line

    def convert_file(self, bat_file: Path) -> str:
        """convert_file – convert file.

Args:
    bat_file: Description of bat_file.

Returns:
    str: Description of return value."""
        try:
            with open(bat_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f'❌ Error reading {bat_file}: {e}')
            self.error_count += 1
            return ''
        converted_lines = ['#!/bin/bash\n', '# Converted from ' + bat_file.name + '\n', '\n']
        for line in lines:
            converted_lines.append(self.convert_line(line) + '\n')
        return ''.join(converted_lines)

    def process_directory(self, directory: Path | None=None) -> None:
        """process_directory – process directory.

Args:
    directory: Description of directory."""
        if directory is None:
            directory = Path.cwd()
        if not directory.exists():
            print(f'❌ Directory not found: {directory}')
            return
        bat_files = list(directory.rglob('*.bat'))
        if not bat_files:
            print(f'ℹ️  No .bat files found in {directory}')
            return
        print(f'🔍 Found {len(bat_files)} .bat file(s)\n')
        for bat_file in bat_files:
            sh_file = bat_file.with_suffix('.sh')
            print(f'📝 Converting: {bat_file.name} → {sh_file.name}')
            converted_content = self.convert_file(bat_file)
            if converted_content:
                try:
                    with open(sh_file, 'w', encoding='utf-8') as f:
                        f.write(converted_content)
                    sh_file.chmod(493)
                    self.converted_count += 1
                    bat_file.unlink()
                    print(f'   ✅ Converted successfully\n')
                except Exception as e:
                    print(f'   ❌ Error writing {sh_file}: {e}\n')
                    self.error_count += 1

    def print_summary(self) -> None:
        """print_summary – print summary."""
        print('=' * 40)
        print(f'📊 Conversion Summary')
        print(f'   ✅ Successful: {self.converted_count}')
        print(f'   ❌ Errors: {self.error_count}')
        print('=' * 40)

def main() -> None:
    """main – main."""
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    converter = BatToShConverter()
    converter.process_directory(target_dir)
    converter.print_summary()
if __name__ == '__main__':
    raise SystemExit(main())
