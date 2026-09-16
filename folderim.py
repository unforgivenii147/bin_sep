#!/data/data/com.termux/files/home/.local/bin/python
"""folderim.py – Folderim utilities.

This module provides functionality for folderim."""
from __future__ import annotations
from typing import Any
import shutil
from pathlib import Path
import dh
from PIL import Image
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
HASH_FUNC = dh.phash
MAX_DISTANCE = 10
OUT_PREFIX = 'group_'

def is_image(path: Path) -> bool:
    """is_image – is image.

Args:
    path: Description of path.

Returns:
    bool: Description of return value."""
    return path.suffix.lower() in IMAGE_EXTS and path.is_file()

def compute_hash(path: Path) -> Any:
    """compute_hash – compute hash.

Args:
    path: Description of path."""
    try:
        with Image.open(path) as img:
            return HASH_FUNC(img)
    except Exception as e:
        print(f'[SKIP] {path.name}: {e}')
        return None

def main() -> None:
    """main – main."""
    cwd = Path.cwd()
    images = [p for p in cwd.iterdir() if is_image(p)]
    if not images:
        print('No images found.')
        return
    hashes = {}
    for img in images:
        h = compute_hash(img)
        if h is not None:
            hashes[img] = h
    groups = []
    for img, h in hashes.items():
        placed = False
        for group in groups:
            ref_hash = group[0][1]
            if h - ref_hash <= MAX_DISTANCE:
                group.append((img, h))
                placed = True
                break
        if not placed:
            groups.append([(img, h)])
    for idx, group in enumerate(groups, start=1):
        if len(group) > 1:
            folder = cwd / f'{OUT_PREFIX}{idx:03d}'
            folder.mkdir(exist_ok=True)
            for img, _ in group:
                shutil.move(str(img), folder / img.name)
    print(f'Done. Created {len([g for g in groups if len(g) > 1])} groups with multiple images.')
if __name__ == '__main__':
    raise SystemExit(main())
