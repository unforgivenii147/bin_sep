#!/data/data/com.termux/files/home/.local/bin/python

import base64
from pathlib import Path


def get_font_b64_or_fallback(filename):
    """Attempts to find and read a TTF file, returning its Base64 string."""
    path = Path(filename)
    if not path.exists():
        print(f"⚠️  Warning: '{filename}' not found in current directory.")
        print(
            f"   WeasyPrint will fall back to default system typography for this style."
        )
        return ""

    binary_data = path.read_bytes()
    b64_encoded = base64.b64encode(binary_data).decode("utf-8")
    return b64_encoded


def build_precise_css():
    print("Parsing typography file tree...")

    # 1. Fetch data for each precise styling variant
    reg_b64 = get_font_b64_or_fallback("Inter-Regular.ttf")
    bold_b64 = get_font_b64_or_fallback("Inter-Bold.ttf")
    italic_b64 = get_font_b64_or_fallback("Inter-Italic.ttf")
    bi_b64 = get_font_b64_or_fallback("Inter-BoldItalic.ttf")
    mono_b64 = get_font_b64_or_fallback("JetBrainsMono-Regular.ttf")

    # 2. Build font-face blocks only if the source file was actually present
    font_face_blocks = []

    if reg_b64:
        font_face_blocks.append(f"""@font-face {{
    font-family: 'Inter';
    font-style: normal;
    font-weight: 400;
    src: url(data:font/truetype;charset=utf-8;base64,{reg_b64}) format('truetype');
}}""")

    if bold_b64:
        font_face_blocks.append(f"""@font-face {{
    font-family: 'Inter';
    font-style: normal;
    font-weight: 700;
    src: url(data:font/truetype;charset=utf-8;base64,{bold_b64}) format('truetype');
}}""")

    if italic_b64:
        font_face_blocks.append(f"""@font-face {{
    font-family: 'Inter';
    font-style: italic;
    font-weight: 400;
    src: url(data:font/truetype;charset=utf-8;base64,{italic_b64}) format('truetype');
}}""")

    if bi_b64:
        font_face_blocks.append(f"""@font-face {{
    font-family: 'Inter';
    font-style: italic;
    font-weight: 700;
    src: url(data:font/truetype;charset=utf-8;base64,{bi_b64}) format('truetype');
}}""")

    if mono_b64:
        font_face_blocks.append(f"""@font-face {{
    font-family: 'JetBrains Mono';
    font-style: normal;
    font-weight: 400;
    src: url(data:font/truetype;charset=utf-8;base64,{mono_b64}) format('truetype');
}}""")

    combined_font_faces = "\n\n".join(font_face_blocks)

    # 3. Formulate structural layout styles
    css_template = f"""/* ==========================================================================
   1. PRECISION FONT REGISTRATION (AUTOMATICALLY INLINED)
   ========================================================================== */{combined_font_faces}

/* Global Reset & Base Typography */
html, body {{
    margin: 0;
    padding: 0;
    font-family: 'Inter', -apple-system, sans-serif;
    font-size: 10.5pt;
    font-weight: 400;
    font-style: normal;
    line-height: 1.6;
    color: #1e293b;
    -webkit-print-color-adjust: exact;
}}

/* Headlines: Bold and Bigger */
h1, h2, h3, h4 {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-style: normal;
    color: #0f172a;
    margin-top: 0;
    page-break-after: avoid;
    break-after: avoid;
}}

h1 {{ 
    font-size: 26pt; 
    line-height: 1.15; 
    margin-bottom: 20pt; 
    letter-spacing: -0.02em; 
}}

h2 {{ 
    font-size: 18pt; 
    line-height: 1.25; 
    margin-top: 24pt;
    margin-bottom: 12pt; 
    border-bottom: 0.75pt solid #cbd5e1; 
    padding-bottom: 6pt; 
}}

h3 {{ 
    font-size: 14pt; 
    line-height: 1.35; 
    margin-top: 18pt;
    margin-bottom: 8pt; 
}}

p {{ margin-top: 0; margin-bottom: 10pt; text-align: justify; }}

/* Code Snippets: Monospace */
code, pre, kbd, samp {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9pt;
    direction: ltr;
    text-align: left;
    white-space: pre-wrap;
    word-break: normal;
}}

pre {{
    background-color: #f8fafc;
    border: 0.5pt solid #e2e8f0;
    border-radius: 4px;
    padding: 10pt 12pt;
    margin: 12pt 0;
    page-break-inside: avoid;
    break-inside: avoid;
}}

p code {{
    background-color: #f1f5f9;
    padding: 2pt 4pt;
    border-radius: 3px;
    color: #0f172a;
}}

/* Variant Styling Rules */
em, i {{
    font-style: italic;
    font-weight: 400;
}}

strong, b {{
    font-weight: 700;
    font-style: normal;
}}

strong em, em strong, b i, i b {{
    font-weight: 700;
    font-style: italic;
}}

/* ==========================================================================
   2. CSS PAGED MEDIA (WEASYPRINT CORE)
   ========================================================================== */
@page {{
    size: A4 portrait;
    margin: 25mm 20mm 20mm 20mm;
    
    @top-left {{
        content: "Official Document Title";
        font-family: 'Inter', sans-serif;
        font-size: 8.5pt;
        color: #64748b;
        border-bottom: 0.5pt solid #cbd5e1;
        padding-bottom: 4pt;
        vertical-align: bottom;
    }}
    
    @top-right {{
        content: "Confidential";
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 8.5pt;
        color: #ef4444;
        border-bottom: 0.5pt solid #cbd5e1;
        padding-bottom: 4pt;
        vertical-align: bottom;
    }}

    @bottom-left {{
        content: "Generated Document";
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }}

    @bottom-right {{
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Inter', sans-serif;
        font-size: 8.5pt;
        color: #64748b;
    }}
}}

@page :first {{
    margin-top: 20mm;
    @top-left {{ content: normal; border-bottom: none; }}
    @top-right {{ content: normal; border-bottom: none; }}
}}

/* ==========================================================================
   3. STRUCTURAL COMPONENTS
   ========================================================================== */
.page-break {{
    page-break-before: always;
    break-before: always;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16pt;
    page-break-inside: auto;
}}

tr {{
    page-break-inside: avoid;
    break-inside: avoid;
}}

thead {{ display: table-header-group; }}

th {{
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 700;
    text-align: left;
    padding: 8pt 10pt;
    font-size: 9.5pt;
    border-bottom: 2pt solid #cbd5e1;
}}

td {{
    padding: 8pt 10pt;
    border-bottom: 1px solid #e2e8f0;
    font-size: 9.5pt;
    vertical-align: top;
}}"""

    output_name = "print-style.css"
    Path(output_name).write_text(css_template, encoding="utf-8")
    print(f"\n🎉 Process Complete! Output saved to: {output_name}")


if __name__ == "__main__":
    build_precise_css()


# * Inter-Regular.ttf
# * Inter-Bold.ttf
# * Inter-Italic.ttf
# * Inter-BoldItalic.ttf
# * JetBrainsMono-Regular.ttf
