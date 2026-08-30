#!/data/data/com.termux/files/home/.local/bin/python

import re
import os
import sys
from pathlib import Path


def extract_plugin_name(plugin_block):
    match = re.search(r'"([^"]+)"', plugin_block)
    if match:
        plugin_url = match.group(1)
        plugin_name = plugin_url.split("/")[-1]
        plugin_name = re.sub(r"[^a-zA-Z0-9\-_.]", "_", plugin_name)
        return plugin_name
    return None


def parse_lua_file(content):
    content = content.strip()

    if content.startswith("return"):
        content = content[6:].strip()

    if content.startswith("{"):
        content = content[1:]
    if content.endswith("}"):
        content = content[:-1]

    plugins = []
    current_plugin = []
    brace_count = 0
    in_string = False
    string_char = None

    for i, char in enumerate(content):
        if char in ('"', "'") and (i == 0 or content[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    current_plugin.append(char)
                    plugin_text = "".join(current_plugin).strip()
                    if plugin_text:
                        if plugin_text.endswith(","):
                            plugin_text = plugin_text[:-1]
                        plugins.append(plugin_text)
                    current_plugin = []
                    continue

        if brace_count > 0:
            current_plugin.append(char)

    return plugins


def create_plugin_file(plugin_name, plugin_content, output_dir):
    filename = f"{plugin_name}.lua"
    filepath = os.path.join(output_dir, filename)

    file_content = f"""return {plugin_content}

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(file_content)

    return filepath


def main():
    if len(sys.argv) < 2:
        print("Usage: python split_plugins.py <input_file.lua> [output_directory]")
        print(
            "       or: cat plugins.lua | python split_plugins.py - [output_directory]"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "plugins"

    if input_file == "-":
        content = sys.stdin.read()
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    plugins = parse_lua_file(content)

    if not plugins:
        print("No plugins found in the input file.")
        sys.exit(1)

    print(f"Found {len(plugins)} plugin specifications.")

    for i, plugin_content in enumerate(plugins, 1):
        plugin_name = extract_plugin_name(plugin_content)

        if plugin_name:
            filepath = create_plugin_file(plugin_name, plugin_content, output_dir)
            print(f"[{i}/{len(plugins)}] Created: {filepath}")
        else:
            print(
                f"[{i}/{len(plugins)}] Warning: Could not extract plugin name, skipping..."
            )

    print(f"\nDone! Plugin files have been created in '{output_dir}' directory.")


if __name__ == "__main__":
    main()
