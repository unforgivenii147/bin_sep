#!/data/data/com.termux/files/home/.local/bin/python
"""compile_precise.py – Compile Precise utilities.

This module provides functionality for compile precise."""
from __future__ import annotations
from typing import Any
import base64
from pathlib import Path

def get_font_b64_or_fallback(filename: Path | str) -> Any:
    """get_font_b64_or_fallback – get font b64 or fallback.

Args:
    filename: Description of filename."""
    path = Path(filename)
    if not path.exists():
        print(f"⚠️  Warning: '{filename}' not found in current directory.")
        print(f'   WeasyPrint will fall back to default system typography for this style.')
        return ''
    binary_data = path.read_bytes()
    b64_encoded = base64.b64encode(binary_data).decode('utf-8')
    return b64_encoded

def build_precise_css() -> None:
    """build_precise_css – build precise css."""
    print('Parsing typography file tree...')
    reg_b64 = get_font_b64_or_fallback('Inter-Regular.ttf')
    bold_b64 = get_font_b64_or_fallback('Inter-Bold.ttf')
    italic_b64 = get_font_b64_or_fallback('Inter-Italic.ttf')
    bi_b64 = get_font_b64_or_fallback('Inter-BoldItalic.ttf')
    mono_b64 = get_font_b64_or_fallback('JetBrainsMono-Regular.ttf')
    font_face_blocks = []
    if reg_b64:
        font_face_blocks.append(f"@font-face {{\n    font-family: 'Inter';\n    font-style: normal;\n    font-weight: 400;\n    src: url(data:font/truetype;charset=utf-8;base64,{reg_b64}) format('truetype');\n}}")
    if bold_b64:
        font_face_blocks.append(f"@font-face {{\n    font-family: 'Inter';\n    font-style: normal;\n    font-weight: 700;\n    src: url(data:font/truetype;charset=utf-8;base64,{bold_b64}) format('truetype');\n}}")
    if italic_b64:
        font_face_blocks.append(f"@font-face {{\n    font-family: 'Inter';\n    font-style: italic;\n    font-weight: 400;\n    src: url(data:font/truetype;charset=utf-8;base64,{italic_b64}) format('truetype');\n}}")
    if bi_b64:
        font_face_blocks.append(f"@font-face {{\n    font-family: 'Inter';\n    font-style: italic;\n    font-weight: 700;\n    src: url(data:font/truetype;charset=utf-8;base64,{bi_b64}) format('truetype');\n}}")
    if mono_b64:
        font_face_blocks.append(f"@font-face {{\n    font-family: 'JetBrains Mono';\n    font-style: normal;\n    font-weight: 400;\n    src: url(data:font/truetype;charset=utf-8;base64,{mono_b64}) format('truetype');\n}}")
    combined_font_faces = '\n\n'.join(font_face_blocks)
    css_template = f"""/* ==========================================================================\n   1. PRECISION FONT REGISTRATION (AUTOMATICALLY INLINED)\n   ========================================================================== */\n{combined_font_faces}\n/* Global Reset & Base Typography */\nhtml, body {{\n    margin: 0;\n    padding: 0;\n    font-family: 'Inter', -apple-system, sans-serif;\n    font-size: 10.5pt;\n    font-weight: 400;\n    font-style: normal;\n    line-height: 1.6;\n    color:\n    -webkit-print-color-adjust: exact;\n}}\n/* Headlines: Bold and Bigger */\nh1, h2, h3, h4 {{\n    font-family: 'Inter', sans-serif;\n    font-weight: 700;\n    font-style: normal;\n    color:\n    margin-top: 0;\n    page-break-after: avoid;\n    break-after: avoid;\n}}\nh1 {{\n    font-size: 26pt;\n    line-height: 1.15;\n    margin-bottom: 20pt;\n    letter-spacing: -0.02em;\n}}\nh2 {{\n    font-size: 18pt;\n    line-height: 1.25;\n    margin-top: 24pt;\n    margin-bottom: 12pt;\n    border-bottom: 0.75pt solid\n    padding-bottom: 6pt;\n}}\nh3 {{\n    font-size: 14pt;\n    line-height: 1.35;\n    margin-top: 18pt;\n    margin-bottom: 8pt;\n}}\np {{ margin-top: 0; margin-bottom: 10pt; text-align: justify; }}\n/* Code Snippets: Monospace */\ncode, pre, kbd, samp {{\n    font-family: 'JetBrains Mono', monospace;\n    font-size: 9pt;\n    direction: ltr;\n    text-align: left;\n    white-space: pre-wrap;\n    word-break: normal;\n}}\npre {{\n    background-color:\n    border: 0.5pt solid\n    border-radius: 4px;\n    padding: 10pt 12pt;\n    margin: 12pt 0;\n    page-break-inside: avoid;\n    break-inside: avoid;\n}}\np code {{\n    background-color:\n    padding: 2pt 4pt;\n    border-radius: 3px;\n    color:\n}}\n/* Variant Styling Rules */\nem, i {{\n    font-style: italic;\n    font-weight: 400;\n}}\nstrong, b {{\n    font-weight: 700;\n    font-style: normal;\n}}\nstrong em, em strong, b i, i b {{\n    font-weight: 700;\n    font-style: italic;\n}}\n/* ==========================================================================\n   2. CSS PAGED MEDIA (WEASYPRINT CORE)\n   ========================================================================== */\n@page {{\n    size: A4 portrait;\n    margin: 25mm 20mm 20mm 20mm;\n    @top-left {{\n        content: "Official Document Title";\n        font-family: 'Inter', sans-serif;\n        font-size: 8.5pt;\n        color:\n        border-bottom: 0.5pt solid\n        padding-bottom: 4pt;\n        vertical-align: bottom;\n    }}\n    @top-right {{\n        content: "Confidential";\n        font-family: 'Inter', sans-serif;\n        font-weight: 700;\n        font-size: 8.5pt;\n        color:\n        border-bottom: 0.5pt solid\n        padding-bottom: 4pt;\n        vertical-align: bottom;\n    }}\n    @bottom-left {{\n        content: "Generated Document";\n        font-family: 'Inter', sans-serif;\n        font-size: 8pt;\n        color:\n    }}\n    @bottom-right {{\n        content: "Page " counter(page) " of " counter(pages);\n        font-family: 'Inter', sans-serif;\n        font-size: 8.5pt;\n        color:\n    }}\n}}\n@page :first {{\n    margin-top: 20mm;\n    @top-left {{ content: normal; border-bottom: none; }}\n    @top-right {{ content: normal; border-bottom: none; }}\n}}\n/* ==========================================================================\n   3. STRUCTURAL COMPONENTS\n   ========================================================================== */\n.page-break {{\n    page-break-before: always;\n    break-before: always;\n}}\ntable {{\n    width: 100%;\n    border-collapse: collapse;\n    margin-bottom: 16pt;\n    page-break-inside: auto;\n}}\ntr {{\n    page-break-inside: avoid;\n    break-inside: avoid;\n}}\nthead {{ display: table-header-group; }}\nth {{\n    background-color:\n    color:\n    font-weight: 700;\n    text-align: left;\n    padding: 8pt 10pt;\n    font-size: 9.5pt;\n    border-bottom: 2pt solid\n}}\ntd {{\n    padding: 8pt 10pt;\n    border-bottom: 1px solid\n    font-size: 9.5pt;\n    vertical-align: top;\n}}\n"""
    output_name = 'print-style.css'
    Path(output_name).write_text(css_template, encoding='utf-8')
    print(f'\n🎉 Process Complete! Output saved to: {output_name}')
if __name__ == '__main__':
    build_precise_css()
