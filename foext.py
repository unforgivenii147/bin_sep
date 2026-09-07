#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

BASE_DIR: Any = Path.cwd()
for item in BASE_DIR.iterdir():
    if not item.is_file():
        continue
    ext: Any = item.suffix.lower().lstrip(".") or "no_extension"
    target_dir: Any = BASE_DIR / ext
    target_dir.mkdir(exist_ok=True)
    shutil.move(str(item), target_dir / item.name)
