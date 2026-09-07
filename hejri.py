#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import datetime

from dh import georgian_to_hijri
from typing import Any

current_year: Any
current_month: Any
current_day: Any


def get_current_ymd():
    today = datetime.date.today()
    return (today.year, today.month, today.day)


current_year, current_month, current_day = get_current_ymd()
print(georgian_to_hijri(current_year, current_month, current_day))
