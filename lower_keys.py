#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import json
import sys
from typing import Any

input_file: Any = sys.argv[1]
with open(input_file, "r", encoding="utf-8") as f:
    data: Any = json.load(f)
lowercased_data: Any = {key.lower(): value for key, value in data.items()}
with open(input_file, "w", encoding="utf-8") as f:
    json.dump(lowercased_data, f, ensure_ascii=False, indent=2)
print(f"Successfully updated {input_file}")
