#!/data/data/com.termux/files/home/.local/bin/python
"""pdf2text.py – Pdf2Text utilities.

This module provides functionality for pdf2text."""
from __future__ import annotations
from typing import Any
import sys
from pathlib import Path
import PyPDF2

def extract_text_from_pdf(pdf_filename: str) -> Any:
    """extract_text_from_pdf – extract text from pdf.

Args:
    pdf_filename: Description of pdf_filename."""
    with Path(pdf_filename).open('rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        extracted_text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()
    return extracted_text

def save_text_to_file(text: str, output_filename: str) -> None:
    """save_text_to_file – save text to file.

Args:
    text: Description of text.
    output_filename: Description of output_filename."""
    Path(output_filename).write_text(text, encoding='utf-8')
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python extract_pdf_text.py <pdf_filename>')
        sys.exit(1)
    pdf_filename = sys.argv[1]
    text_filename = pdf_filename.replace('.pdf', '.txt')
    extracted_text = extract_text_from_pdf(pdf_filename)
    save_text_to_file(extracted_text, text_filename)
    print(f'Text extracted and saved to {text_filename}')
