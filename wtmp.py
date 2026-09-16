#!/data/data/com.termux/files/home/.local/bin/python
"""wtmp.py – Wtmp utilities.

This module provides functionality for wtmp."""
from __future__ import annotations
from typing import Any
import shutil
import sys
import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
TEMPDIR = Path('/data/data/com.termux/files/usr/tmp')
DEST_DIR = Path('~/tmp/tgz').expanduser()
ALLOWED_EXTENSIONS = ('.tar.gz', '.whl', '.tar.xz', '.zip', '.tar.bz2', '.tar.lzma', '.tar.lz4', '.tgz', '.txz', '.tbz2', '.tbr')

def copy_if_match(src: Path) -> None:
    """copy_if_match – copy if match.

Args:
    src: Description of src."""
    if any((str(src).endswith(ext) for ext in ALLOWED_EXTENSIONS)):
        try:
            DEST_DIR.mkdir(parents=True, exist_ok=True)
            dest = DEST_DIR / src.name
            shutil.copy2(src, dest)
            print(f'Copied: {src}')
        except Exception as e:
            print(f'Failed to copy {src}: {e}')

def startup_scan(root: Path) -> None:
    """startup_scan – startup scan.

Args:
    root: Description of root."""
    for path in root.rglob('*'):
        if path.is_file():
            copy_if_match(path)

class CopyEventHandler(FileSystemEventHandler):
    """CopyEventHandler – CopyEventHandler."""

    def on_created(self, event: Any) -> None:
        """on_created – on created.

Args:
    event: Description of event."""
        if not event.is_directory:
            copy_if_match(Path(event.src_path))

    def on_modified(self, event: Any) -> None:
        """on_modified – on modified.

Args:
    event: Description of event."""
        if not event.is_directory:
            copy_if_match(Path(event.src_path))
if __name__ == '__main__':
    watch_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else TEMPDIR
    if not watch_path.exists():
        print(f'Error: Path {watch_path} does not exist')
        sys.exit(1)
    print(f'Watching: {watch_path}')
    print(f'Destination: {DEST_DIR}')
    startup_scan(watch_path)
    event_handler = CopyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping observer...')
        observer.stop()
        observer.join()
        print('Script terminated.')
