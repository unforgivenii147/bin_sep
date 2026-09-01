#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dh import get_installed_packages


def check_package_update(package_info: dict[str, str]) -> tuple[str, str, str, bool]:
    package_name = package_info["name"]
    current_version = package_info["version"]
    try:
        cmd = ["pip", "index", "versions", package_name]
        result = runcmd(cmd, show_output=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "Available versions:" in line:
                    versions_str = line.split("Available versions:")[1].strip()
                    versions = [v.strip() for v in versions_str.split(",")]
                    if versions:
                        latest_version = versions[0]
                        if current_version != latest_version:
                            return (package_name, current_version, latest_version, True)
                        break
    except subprocess.TimeoutExpired:
        print(f"Timeout checking {package_name}")
    except Exception as e:
        print(f"Error checking {package_name}: {e}")
    return (package_name, current_version, current_version, False)


def check_updates_parallel(
    packages: list[dict[str, str]], max_workers: int = 8
) -> list[tuple[str, str, str]]:
    upgradable = []
    print(
        f"Checking {len(packages)} packages for updates using {max_workers} workers..."
    )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_package = {
            executor.submit(check_package_update, pkg): pkg["name"] for pkg in packages
        }
        completed = 0
        for future in as_completed(future_to_package):
            package_name = future_to_package[future]
            completed += 1
            try:
                result = future.result()
                name, current_ver, latest_ver, has_update = result
                if has_update:
                    upgradable.append((name, current_ver, latest_ver))
                    print(
                        f"[{completed}/{len(packages)}] {name}: {current_ver} -> {latest_ver} (UPDATE AVAILABLE)"
                    )
                else:
                    print(
                        f"[{completed}/{len(packages)}] {name}: {current_ver} (up-to-date)"
                    )
            except Exception as e:
                print(
                    f"[{completed}/{len(packages)}] Error processing {package_name}: {e}"
                )
    return upgradable


def save_upgradable_packages(upgradable: list[tuple[str, str, str]], output_file: Path):
    try:
        with open(output_file, "w") as f:
            f.write("# Packages with available updates\n")
            f.write(f"# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# Format: package_name current_version -> latest_version\n\n")
            f.writelines(
                f"{name}=={current_ver}  # -> {latest_ver}\n"
                for name, current_ver, latest_ver in upgradable
            )
        print(f"\nResults saved to {output_file}")
        print(f"Found {len(upgradable)} packages with available updates")
    except OSError as e:
        print(f"Error saving results to {output_file}: {e}")


def find_site_packages() -> list[Path]:
    import site

    return site.getsitepackages()


def main():
    print("Python Package Update Checker")
    print("-" * 42)
    site_dirs = find_site_packages()
    if not site_dirs:
        print("No site-packages directories found!")
        sys.exit(1)
    print(f"Found {len(site_dirs)} site-packages directories:")
    for site_dir in site_dirs:
        print(f"  - {site_dir}")
    all_packages = []
    for site_dir in site_dirs:
        print(f"\nScanning {site_dir}...")
        packages = get_installed_packages()
        print(f"  Found {len(packages)} packages")
        all_packages.extend(packages)
    if not all_packages:
        print("No packages found!")
        sys.exit(1)
    seen = set()
    unique_packages = []
    for pkg in all_packages:
        if pkg["name"] not in seen:
            seen.add(pkg["name"])
            unique_packages.append(pkg)
    print(f"\nTotal unique packages to check: {len(unique_packages)}")
    upgradable = check_updates_parallel(unique_packages, max_workers=20)
    output_file = Path.cwd() / "upgradable.txt"
    save_upgradable_packages(upgradable, output_file)
    print("\n" + "=" * 42)
    print("Summary:")
    print(f"  Total packages checked: {len(unique_packages)}")
    print(f"  Updates available: {len(upgradable)}")
    print(f"  Up-to-date: {len(unique_packages) - len(upgradable)}")
    if upgradable:
        print("\nPackages with available updates:")
        for name, current_ver, latest_ver in upgradable:
            print(f"  {name}: {current_ver} -> {latest_ver}")


if __name__ == "__main__":
    raise SystemExit(main())
