#!/data/data/com.termux/files/home/.local/bin/python
"""hejri.py – Hejri utilities.

This module provides functionality for hejri."""
from __future__ import annotations
from typing import Any
import datetime
from dh import georgian_to_hijri

def get_current_ymd() -> Any:
    """get_current_ymd – get current ymd."""
    today = datetime.date.today()
    return (today.year, today.month, today.day)
current_year, current_month, current_day = get_current_ymd()
print(georgian_to_hijri(current_year, current_month, current_day))
