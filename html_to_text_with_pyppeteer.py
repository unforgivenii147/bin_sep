#!/data/data/com.termux/files/home/.local/bin/python
"""html_to_text_with_pyppeteer.py – Html To Text With Pyppeteer utilities.

This module provides functionality for html to text with pyppeteer."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from pyppeteer import launch

async def main() -> None:
    """main – main."""
    url = sys.argv[1]
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    await page.screenshot({'path': 'example.png'})
    content = await page.evaluate('document.body.textContent', force_expr=True)
    outfile = Path(url).with_suffix('.txt')
    Path(outfile).write_text(content, encoding='utf-8')
    dimensions = await page.evaluate('() => {\n        return {\n            width: document.documentElement.clientWidth,\n            height: document.documentElement.clientHeight,\n            deviceScaleFactor: window.devicePixelRatio,\n        }\n    }')
    print(dimensions)
    await browser.close()
asyncio.get_event_loop().run_until_complete(main())
