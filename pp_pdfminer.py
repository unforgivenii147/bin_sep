#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations

import argparse
import glob
import logging
import os
import sys
from io import StringIO
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from pdfminer.pdfexceptions import PDFValueError

logging.basicConfig()


def process_page(args: tuple) -> tuple[int, str]:
    pdf_path, page_num, laparams, password = args
    try:
        output = StringIO()
        extract_text_to_fp(
            open(pdf_path, "rb"),
            output,
            laparams=laparams,
            page_numbers=[page_num],
            password=password,
            codec="utf-8",
        )
        return page_num, output.getvalue()
    except Exception as e:
        logging.error(f"Error processing page {page_num + 1} of {pdf_path}: {e}")
        return page_num, ""


def get_total_pages(pdf_path: str, password: str = "") -> int:

    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfparser import PDFParser

    with open(pdf_path, "rb") as fp:
        parser = PDFParser(fp)
        document = PDFDocument(parser, password)
        return sum(1 for _ in document.get_pages())


def process_pdf(
    pdf_path: str,
    laparams: LAParams | None,
    password: str,
    num_workers: int | None = None,
) -> None:

    pdf_path = Path(pdf_path)

    try:
        total_pages = get_total_pages(str(pdf_path), password)
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
        return

    output_dir = Path(pdf_path.stem)
    output_dir.mkdir(exist_ok=True)

    padding = len(str(total_pages))

    page_args = [(str(pdf_path), i, laparams, password) for i in range(total_pages)]

    workers = num_workers or cpu_count()
    with Pool(processes=workers) as pool:
        results = pool.map(process_page, page_args)

    for page_num, text in results:
        if text:
            filename = f"{page_num + 1:0{padding}d}.txt"
            output_path = output_dir / filename
            output_path.write_text(text, encoding="utf-8")
            logging.info(f"Saved page {page_num + 1} to {output_path}")

    logging.info(f"Completed processing {pdf_path}. Output saved to {output_dir}/")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files, one text file per page."
    )

    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="One or more paths to PDF files or directories containing PDF files.",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="pdf2txt v1.0",
    )

    parser.add_argument(
        "--debug",
        "-d",
        default=False,
        action="store_true",
        help="Use debug logging level.",
    )

    parser.add_argument(
        "--password",
        "-P",
        type=str,
        default="",
        help="The password to use for decrypting PDF file.",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of worker processes (default: CPU count).",
    )

    la_params = LAParams()
    la_param_group = parser.add_argument_group(
        "Layout analysis",
        description="Used during layout analysis.",
    )

    la_param_group.add_argument(
        "--no-laparams",
        "-n",
        default=False,
        action="store_true",
        help="If layout analysis parameters should be ignored.",
    )

    la_param_group.add_argument(
        "--detect-vertical",
        "-V",
        default=la_params.detect_vertical,
        action="store_true",
        help="If vertical text should be considered during layout analysis",
    )

    la_param_group.add_argument(
        "--line-overlap",
        type=float,
        default=la_params.line_overlap,
        help="If two characters have more overlap than this they are considered to be on the same line.",
    )

    la_param_group.add_argument(
        "--char-margin",
        "-M",
        type=float,
        default=la_params.char_margin,
        help="If two characters are closer together than this margin they are considered to be part of the same line.",
    )

    la_param_group.add_argument(
        "--word-margin",
        "-W",
        type=float,
        default=la_params.word_margin,
        help="If two characters on the same line are further apart than this margin then they are considered to be two separate words.",
    )

    la_param_group.add_argument(
        "--line-margin",
        "-L",
        type=float,
        default=la_params.line_margin,
        help="If two lines are close together they are considered to be part of the same paragraph.",
    )

    la_param_group.add_argument(
        "--boxes-flow",
        "-F",
        type=float,
        default=la_params.boxes_flow,
        help="Specifies how much horizontal and vertical position matters when determining line order.",
    )

    la_param_group.add_argument(
        "--all-texts",
        "-A",
        default=la_params.all_texts,
        action="store_true",
        help="If layout analysis should be performed on text in figures.",
    )

    return parser


def parse_args(args: list[str] | None) -> argparse.Namespace:
    parsed_args = create_parser().parse_args(args=args)

    if parsed_args.no_laparams:
        parsed_args.laparams = None
    else:
        parsed_args.laparams = LAParams(
            line_overlap=parsed_args.line_overlap,
            char_margin=parsed_args.char_margin,
            line_margin=parsed_args.line_margin,
            word_margin=parsed_args.word_margin,
            boxes_flow=parsed_args.boxes_flow,
            detect_vertical=parsed_args.detect_vertical,
            all_texts=parsed_args.all_texts,
        )

    return parsed_args


def expand_file_list(inputs: list[str]) -> list[str]:

    pdf_files = []

    for item in inputs:
        if "*" in item or "?" in item:
            pdf_files.extend(glob.glob(item))
            continue

        path = Path(item)

        if path.is_dir():
            pdf_files.extend(path.glob("*.pdf"))
            pdf_files.extend(path.glob("*.PDF"))
        elif path.is_file() and path.suffix.lower() == ".pdf":
            pdf_files.append(str(path))
        else:
            logging.warning(f"Skipping {item}: not a PDF file or directory")

    seen = set()
    unique_files = []
    for f in pdf_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    return unique_files


def main(args: list[str] | None = None) -> int:
    parsed_args = parse_args(args)

    if parsed_args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    pdf_files = expand_file_list(parsed_args.files)

    if not pdf_files:
        logging.error("No PDF files found to process.")
        return 1

    logging.info(f"Processing {len(pdf_files)} PDF file(s)...")

    for pdf_file in pdf_files:
        logging.info(f"Processing: {pdf_file}")
        try:
            process_pdf(
                pdf_file,
                parsed_args.laparams,
                parsed_args.password,
                parsed_args.workers,
            )
        except Exception as e:
            logging.error(f"Failed to process {pdf_file}: {e}")
            continue

    logging.info("All files processed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
