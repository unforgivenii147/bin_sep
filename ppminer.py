#!/data/data/com.termux/files/home/.local/bin/python
"""ppminer.py – Ppminer utilities.

This module provides functionality for ppminer."""
from __future__ import annotations
import argparse
import multiprocessing as mp
import sys
from pathlib import Path
from pdfminer.high_level import extract_text
from pdfminer.pdfpage import PDFPage

def positive_int(value: str) -> int:
    """positive_int – positive int.

Args:
    value: Description of value.

Returns:
    int: Description of return value."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('must be greater than zero')
    return number

def find_pdf_files(inputs: list[str]) -> list[Path]:
    """find_pdf_files – find pdf files.

Args:
    inputs: Description of inputs.

Returns:
    list[Path]: Description of return value."""
    pdf_files: set[Path] = set()
    for item in inputs:
        path = Path(item).expanduser()
        if not path.exists():
            raise FileNotFoundError(f'Input does not exist: {path}')
        if path.is_file():
            if path.suffix.lower() == '.pdf':
                pdf_files.add(path.resolve())
        elif path.is_dir():
            for candidate in path.rglob('*'):
                if candidate.is_file() and candidate.suffix.lower() == '.pdf':
                    pdf_files.add(candidate.resolve())
    return sorted(pdf_files)

def count_pages(pdf_path: Path) -> int:
    """count_pages – count pages.

Args:
    pdf_path: Description of pdf_path.

Returns:
    int: Description of return value."""
    with pdf_path.open('rb') as pdf_file:
        return sum((1 for _ in PDFPage.get_pages(pdf_file, password='', caching=True, check_extractable=True)))

def extract_one_page(job: tuple[str, int]) -> str:
    """extract_one_page – extract one page.

Args:
    job: Description of job.

Returns:
    str: Description of return value."""
    pdf_name, page_number = job
    if page_number % 10 == 0:
        print(f'processing {page_number}')
    text = extract_text(pdf_name, page_numbers=[page_number])
    return text.rstrip('\x0c')

def process_pdf(pdf_path: Path, workers: int=8) -> None:
    """process_pdf – process pdf.

Args:
    pdf_path: Description of pdf_path.
    workers: Description of workers."""
    page_count = count_pages(pdf_path)
    if page_count == 0:
        print(f'Skipping empty PDF: {pdf_path}')
        return
    output_dir = pdf_path.parent / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    padding_width = max(3, len(str(page_count)))
    jobs = [(str(pdf_path), page_number) for page_number in range(page_count)]
    process_count = min(workers, page_count)
    print(f'Processing {pdf_path} ({page_count} pages, {process_count} workers)')
    with mp.Pool(processes=process_count) as pool:
        page_texts = pool.map(extract_one_page, jobs)
    for page_number, text in enumerate(page_texts, start=1):
        output_file = output_dir / f'{page_number:0{padding_width}d}.txt'
        output_file.write_text(text, encoding='utf-8')
    print(f'Saved pages to: {output_dir}')

def build_parser() -> argparse.ArgumentParser:
    """build_parser – build parser.

Returns:
    argparse.ArgumentParser: Description of return value."""
    parser = argparse.ArgumentParser(description='Extract each PDF page into a separate TXT file.')
    parser.add_argument('inputs', nargs='+', help='PDF files and/or directories containing PDF files.')
    return parser

def main() -> int:
    """main – main.

Returns:
    int: Description of return value."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        pdf_files = find_pdf_files(args.inputs)
        if not pdf_files:
            parser.error('No PDF files were found.')
        for pdf_path in pdf_files:
            try:
                process_pdf(pdf_path, 8)
            except Exception as error:
                print(f'Error processing {pdf_path}: {error}', file=sys.stderr)
    except FileNotFoundError as error:
        parser.error(str(error))
    return 0
if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
