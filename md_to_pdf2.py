#!/data/data/com.termux/files/home/.local/bin/python
"""md_to_pdf2.py – Md To Pdf2 utilities.

This module provides functionality for md to pdf2."""
from __future__ import annotations
import sys
from pathlib import Path
import markdown
import weasyprint
CSS_TEMPLATE = '\n/* ==========================================================================\n   0. LOCAL FONTS CONFIGURATION\n   ========================================================================== */\n@font-face {\n    font-family: "LocalInter";\n    src: url("fonts/Inter-Regular.ttf");\n    font-weight: normal;\n    font-style: normal;\n}\n@font-face {\n    font-family: "LocalInter";\n    src: url("fonts/Inter-Bold.ttf");\n    font-weight: bold;\n    font-style: normal;\n}\n@font-face {\n    font-family: "LocalMono";\n    src: url("fonts/JetBrainsMono-Regular.ttf");\n    font-weight: normal;\n    font-style: normal;\n}\n/* ==========================================================================\n   1. PAGE SETUP & PAGED MEDIA\n   ========================================================================== */\n@page {\n    size: A4;\n    margin: 20mm;\n    @bottom-right {\n        content: "Page " counter(page) " of " counter(pages);\n        font-family: "LocalInter", sans-serif;\n        font-size: 9pt;\n        color:\n    }\n}\nh1, h2, h3, h4, h5, h6 { page-break-after: avoid; break-after: avoid; }\nblockquote, pre, table, figure { page-break-inside: avoid; break-inside: avoid; }\nul, ol { page-break-inside: auto; }\nli { page-break-inside: avoid; break-inside: avoid; }\n/* ==========================================================================\n   2. TYPOGRAPHY & BASE STYLES\n   ========================================================================== */\nhtml, body {\n    font-family: "LocalInter", sans-serif;\n    font-size: 11pt;\n    line-height: 1.6;\n    color:\n}\np {\n    margin-top: 0;\n    margin-bottom: 1.2em;\n    text-align: justify;\n}\nh1 {\n    font-size: 24pt;\n    margin-top: 0;\n    margin-bottom: 15pt;\n    color:\n    border-bottom: 2px solid\n    padding-bottom: 5pt;\n}\nh2 {\n    font-size: 18pt;\n    margin-top: 24pt;\n    margin-bottom: 12pt;\n    color:\n    border-bottom: 1px solid\n    padding-bottom: 3pt;\n}\nh3 {\n    font-size: 14pt;\n    margin-top: 18pt;\n    margin-bottom: 8pt;\n    color:\n}\n/* ==========================================================================\n   3. INLINE ELEMENTS & DECORATIONS\n   ========================================================================== */\na { color:\na[href^="http"]:after {\n    content: " (" attr(href) ")";\n    font-size: 9pt;\n    color:\n}\nstrong { color:\ncode {\n    font-family: "LocalMono", monospace;\n    font-size: 9.5pt;\n    background-color:\n    padding: 2px 4px;\n    border-radius: 3px;\n    color:\n}\nblockquote {\n    margin: 1.5em 0;\n    padding: 0.5em 15px;\n    border-left: 4px solid\n    color:\n    background-color:\n    font-style: italic;\n}\n/* ==========================================================================\n   4. CODE BLOCKS (Markdown ``` )\n   ========================================================================== */\npre {\n    background-color:\n    border: 1px solid\n    border-radius: 4px;\n    padding: 12px;\n    margin: 1.5em 0;\n    overflow: hidden;\n}\npre code {\n    background-color: transparent;\n    padding: 0;\n    border-radius: 0;\n    color:\n    font-family: "LocalMono", monospace;\n    font-size: 9pt;\n    white-space: pre-wrap;\n}\n/* ==========================================================================\n   5. TABLES & LISTS\n   ========================================================================== */\ntable {\n    width: 100%;\n    border-collapse: collapse;\n    margin: 20px 0;\n    font-size: 10.5pt;\n}\nth, td {\n    border: 1px solid\n    padding: 8px 12px;\n    text-align: left;\n}\nth {\n    background-color:\n    font-weight: bold;\n    color:\n}\ntr:nth-child(even) { background-color:\nul, ol { margin-top: 0; margin-bottom: 1.5em; padding-left: 24px; }\nli { margin-bottom: 0.4em; }\n/* ==========================================================================\n   6. IMAGES / FIGURES\n   ========================================================================== */\nimg {\n    max-width: 100%;\n    height: auto;\n    display: block;\n    margin: 20px auto;\n    border-radius: 4px;\n}\n'

def convert_md_to_pdf(input_path_str: str) -> None:
    """convert_md_to_pdf – convert md to pdf.

Args:
    input_path_str: Description of input_path_str."""
    input_file = Path(input_path_str)
    if not input_file.exists():
        print(f"❌ Error: The file '{input_path_str}' does not exist.")
        sys.exit(1)
    output_pdf = input_file.with_suffix('.pdf')
    print(f'📖 Reading: {input_file.name}')
    md_content = input_file.read_text(encoding='utf-8')
    print('🛠️  Converting Markdown to HTML...')
    html_body = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    full_html = f'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n    <title>{input_file.stem}</title>\n</head>\n<body>\n    {html_body}\n</body>\n</html>'
    print('🚀 Compiling PDF with WeasyPrint using local fonts...')
    try:
        html_doc = weasyprint.HTML(string=full_html, base_url=str(input_file.parent))
        css_doc = weasyprint.CSS(string=CSS_TEMPLATE)
        html_doc.write_pdf(target=output_pdf, stylesheets=[css_doc])
        print(f'✅ Success! PDF generated at:\n   👉 {output_pdf.resolve()}')
    except Exception as e:
        print(f'❌ WeasyPrint Error: {e}')
        sys.exit(1)
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('❌ Usage Error: Provide an input Markdown file.')
        sys.exit(1)
    convert_md_to_pdf(sys.argv[1])
