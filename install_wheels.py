#!/data/data/com.termux/files/home/.local/bin/python
"""
Generate a Python script that installs all .whl files in the current directory using
multiprocessing.Pool.apply_async with a fixed pool of 8 workers, classifies each wheel
as pure-Python (user install) or platform-specific (system install) by inspecting its
WHEEL/METADATA and binary contents, logs progress and a final summary via loguru, and
uses only pathlib for filesystem operations with complete type annotations.
"""

from __future__ import annotations

import platform
import subprocess
import sys
import zipfile
from multiprocessing.pool import ApplyResult, Pool
from pathlib import Path
from typing import Final

from loguru import logger

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

POOL_SIZE: Final[int] = 8
PURE_PYTHON_MARKER: Final[str] = "-none-any"
ROOT_IS_PURELIB_TRUE: Final[str] = "Root-Is-Purelib: true"
ROOT_IS_PURELIB_FALSE: Final[str] = "Root-Is-Purelib: false"
BINARY_EXTENSIONS: Final[tuple[str, ...]] = (".so", ".pyd", ".dll", ".dylib")
METADATA_SUFFIXES: Final[tuple[str, ...]] = (".dist-info/WHEEL", ".dist-info/METADATA")


# ---------------------------------------------------------------------------
# Wheel inspection
# ---------------------------------------------------------------------------


def is_pure_python_wheel(wheel_path: Path) -> bool:
    """Return True if the wheel at ``wheel_path`` is a pure-Python wheel.

    Detection order:
    1. The ``-none-any`` tag in the filename.
    2. The ``Root-Is-Purelib`` field in the wheel metadata.
    3. Presence of native binary extensions inside the archive.
    """
    wheel_name: str = wheel_path.stem
    if PURE_PYTHON_MARKER in wheel_name:
        return True

    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(METADATA_SUFFIXES):
                    with zf.open(name) as f:
                        content: str = f.read().decode("utf-8")
                        if ROOT_IS_PURELIB_TRUE in content:
                            return True
                        if ROOT_IS_PURELIB_FALSE in content:
                            return False
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not inspect {wheel_path.name}: {exc}")

    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(BINARY_EXTENSIONS):
                    return False
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not inspect {wheel_path.name}: {exc}")
        return False


def get_wheel_type(wheel_path: Path) -> str:
    """Return a human-readable description of the wheel's platform target."""
    try:
        wheel_name: str = wheel_path.stem
        parts: list[str] = wheel_name.split("-")
        if len(parts) >= 4:
            platform_tag: str = parts[-1]
            if "none-any" in wheel_name:
                return "Pure Python (any platform)"
            if "android" in platform_tag.lower():
                return f"Android-specific ({platform_tag})"
            if "linux" in platform_tag.lower():
                return f"Linux-specific ({platform_tag})"
            return f"Platform-specific ({platform_tag})"
    except Exception:  # noqa: BLE001
        pass
    return "Unknown"


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------


def install_wheel(wheel_path: Path, user_install: bool) -> tuple[Path, bool, str]:
    """Install a single wheel using pip and return (path, success, message)."""
    try:
        cmd: list[str] = [sys.executable, "-m", "pip", "install", str(wheel_path)]
        if user_install:
            cmd.insert(3, "--user")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        install_type: str = (
            "user site-packages" if user_install else "system site-packages"
        )
        return wheel_path, True, f"✓ {wheel_path.name} -> {install_type}"
    except subprocess.CalledProcessError as exc:
        error_msg: str = exc.stderr.strip() if exc.stderr else str(exc)
        return wheel_path, False, f"✗ {wheel_path.name}: {error_msg}"
    except Exception as exc:  # noqa: BLE001
        return wheel_path, False, f"✗ {wheel_path.name}: {exc!s}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Discover wheels in the current directory and install them in parallel."""
    current_dir: Path = Path.cwd()
    wheel_files: list[Path] = list(current_dir.glob("*.whl"))

    if not wheel_files:
        logger.info("No .whl files found in current directory.")
        return

    logger.info(f"Found {len(wheel_files)} wheel(s) in {current_dir}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info("-" * 40)

    install_tasks: list[tuple[Path, bool]] = []
    for wheel in wheel_files:
        is_pure: bool = is_pure_python_wheel(wheel)
        wheel_type: str = get_wheel_type(wheel)
        install_type: str = "USER site-packages" if is_pure else "SYSTEM site-packages"
        logger.info(f"Analyzing: {wheel.name}")
        logger.info(f"  Type: {wheel_type}")
        logger.info(f"  Target: {install_type}")
        install_tasks.append((wheel, is_pure))

    logger.info("=" * 40)
    logger.info("Starting parallel installation...")
    logger.info("-" * 40)

    successful: list[Path] = []
    failed: list[tuple[Path, str]] = []

    with Pool(processes=POOL_SIZE) as pool:
        async_results: list[ApplyResult[tuple[Path, bool, str]]] = [
            pool.apply_async(install_wheel, (wheel, is_pure))
            for wheel, is_pure in install_tasks
        ]

        for async_result in async_results:
            try:
                wheel_path, success, message = async_result.get()
                logger.info(message)
                if success:
                    successful.append(wheel_path)
                else:
                    failed.append((wheel_path, message))
            except Exception as exc:  # noqa: BLE001
                logger.error(f"✗ Error processing wheel: {exc}")
                failed.append((Path("<unknown>"), str(exc)))

    logger.info("=" * 40)
    logger.info("INSTALLATION SUMMARY")
    logger.info("-" * 40)
    logger.info(f"Total wheels: {len(wheel_files)}")
    logger.info(f"✓ Successfully installed: {len(successful)}")
    logger.info(f"✗ Failed: {len(failed)}")

    if successful:
        logger.info("Successfully installed:")
        for wheel in successful:
            is_pure = is_pure_python_wheel(wheel)
            location: str = "user site" if is_pure else "system site"
            logger.info(f"  ✓ {wheel.name} -> {location}")

    if failed:
        logger.info("Failed installations:")
        for wheel, error in failed:
            logger.info(f"  ✗ {wheel.name}: {error}")

    logger.info("Done!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Installation interrupted by user.")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error: {exc}")
        sys.exit(1)
