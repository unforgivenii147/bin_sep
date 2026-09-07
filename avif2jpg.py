#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

from pathlib import Path

from PIL import Image
from typing import Any

input_dir: Any = Path("avif_images")
output_dir: Any = Path("jpg_images")
output_dir.mkdir(exist_ok=True, parents=True)
if input_dir.exists() and input_dir.is_dir():
    for file in input_dir.iterdir():
        if file.is_file() and file.suffix.lower() in (".avif", ".aviff"):
            output_path: Any = output_dir / (file.stem + ".jpg")
            with Image.open(file) as img:
                img: Any = img.convert("RGB")
                img.save(output_path, "JPEG", quality=95)
