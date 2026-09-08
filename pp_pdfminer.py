#!/data/data/com.termux/files/home/.local/bin/python
from __future__ import annotations
import argparse
import logging
import sys
from collections.abc import Container, Iterable
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any
import pdfminer.high_level
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfexceptions import PDFValueError

logging.basicConfig()
OUTPUT_TYPES = ((".htm", "html"), (".html", "html"), (".xml", "xml"), (".tag", "tag"))


def float_or_disabled(x: str) -> float | None:
    if x.lower().strip() == "disabled":
        return None
    try:
        return float(x)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"invalid float value: {x}") from err


def extract_page_worker(args: tuple) -> str:
    (
        pdf_file,
        page_idx,
        output_file,
        laparams,
        codec,
        strip_control,
        password,
        _rotation,
        disable_caching,
    ) = args
    try:
        for _current_idx, page_layout in enumerate(
            pdfminer.high_level.extract_pages(
                pdf_file,
                laparams=laparams,
                maxpages=page_idx + 1,
                page_numbers={page_idx},
                password=password,
                caching=not disable_caching,
            )
        ):
            text = ""
            for element in page_layout:
                if isinstance(element, LTTextBox):
                    text += element.get_text()
            if strip_control:
                text = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")
            with open(output_file, "w", encoding=codec) as f:
                f.write(text)
            return f"✓ {output_file}"
    except Exception as e:
        return f"✗ {output_file}: {e!s}"


def extract_text(
    files: Iterable[str] = [],
    laparams: LAParams | None = None,
    codec: str = "utf-8",
    strip_control: bool = False,
    maxpages: int = 0,
    page_numbers: Container[int] | None = None,
    password: str = "",
    rotation: int = 0,
    debug: bool = False,
    disable_caching: bool = False,
    num_workers: int | None = None,
    **kwargs: Any,
) -> None:
    if not files:
        raise PDFValueError("Must provide files to work upon!")
    if num_workers is None:
        num_workers = cpu_count()
    tasks = []
    for fname in files:
        input_path = Path(fname)
        output_directory = input_path.parent / input_path.stem
        output_directory.mkdir(exist_ok=True)
        page_count = 0
        for _ in pdfminer.high_level.extract_pages(
            fname,
            laparams=laparams,
            maxpages=maxpages,
            page_numbers=page_numbers,
            password=password,
            caching=not disable_caching,
        ):
            page_count += 1
        for page_idx in range(page_count):
            if page_numbers and page_idx not in page_numbers:
                continue
            if page_idx % 10 == 0:
                print(f"processing {page_idx}")
            output_file = output_directory / f"page_{page_idx:04d}.txt"
            if output_file.exists():
                print(f"{output_file} exists")
                continue
            tasks.append(
                (
                    fname,
                    page_idx,
                    output_file,
                    laparams,
                    codec,
                    strip_control,
                    password,
                    rotation,
                    disable_caching,
                )
            )
    print(f"Processing {len(tasks)} pages using {num_workers} workers...\n")
    with Pool(processes=num_workers) as pool:
        results = pool.map(extract_page_worker, tasks)
    for result in results:
        print(result)
    print(
        f"\n✓ Completed: {sum(1 for r in results if r.startswith('✓'))} pages extracted"
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, add_help=True)
    parser.add_argument(
        "files",
        type=str,
        default=None,
        nargs="+",
        help="One or more paths to PDF files.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"pdfminer.six v{pdfminer.__version__}",
    )
    parser.add_argument(
        "--debug",
        "-d",
        default=False,
        action="store_true",
        help="Use debug logging level.",
    )
    parser.add_argument(
        "--disable-caching",
        "-C",
        default=False,
        action="store_true",
        help="If caching or resources, such as fonts, should be disabled.",
    )
    parse_params = parser.add_argument_group(
        "Parser",
        description="Used during PDF parsing",
    )
    parse_params.add_argument(
        "--page-numbers",
        type=int,
        default=None,
        nargs="+",
        help="A space-seperated list of page numbers to parse.",
    )
    parse_params.add_argument(
        "--pagenos",
        "-p",
        type=str,
        help="A comma-separated list of page numbers to parse. "
        "Included for legacy applications, use --page-numbers "
        "for more idiomatic argument entry.",
    )
    parse_params.add_argument(
        "--maxpages",
        "-m",
        type=int,
        default=0,
        help="The maximum number of pages to parse.",
    )
    parse_params.add_argument(
        "--password",
        "-P",
        type=str,
        default="",
        help="The password to use for decrypting PDF file.",
    )
    parse_params.add_argument(
        "--rotation",
        "-R",
        default=0,
        type=int,
        help="The number of degrees to rotate the PDF "
        "before other types of processing.",
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
        help="If two characters have more overlap than this they "
        "are considered to be on the same line. The overlap is specified "
        "relative to the minimum height of both characters.",
    )
    la_param_group.add_argument(
        "--char-margin",
        "-M",
        type=float,
        default=la_params.char_margin,
        help="If two characters are closer together than this margin they "
        "are considered to be part of the same line. The margin is "
        "specified relative to the width of the character.",
    )
    la_param_group.add_argument(
        "--word-margin",
        "-W",
        type=float,
        default=la_params.word_margin,
        help="If two characters on the same line are further apart than this "
        "margin then they are considered to be two separate words, and "
        "an intermediate space will be added for readability. The margin "
        "is specified relative to the width of the character.",
    )
    la_param_group.add_argument(
        "--line-margin",
        "-L",
        type=float,
        default=la_params.line_margin,
        help="If two lines are close together they are considered to "
        "be part of the same paragraph. The margin is specified "
        "relative to the height of a line.",
    )
    la_param_group.add_argument(
        "--boxes-flow",
        "-F",
        type=float_or_disabled,
        default=la_params.boxes_flow,
        help="Specifies how much a horizontal and vertical position of a "
        "text matters when determining the order of lines. The value "
        "should be within the range of -1.0 (only horizontal position "
        "matters) to +1.0 (only vertical position matters). You can also "
        "pass `disabled` to disable advanced layout analysis, and "
        "instead return text based on the position of the bottom left "
        "corner of the text box.",
    )
    la_param_group.add_argument(
        "--all-texts",
        "-A",
        default=la_params.all_texts,
        action="store_true",
        help="If layout analysis should be performed on text in figures.",
    )
    output_params = parser.add_argument_group(
        "Output",
        description="Used during output generation.",
    )
    output_params.add_argument(
        "--codec",
        "-c",
        type=str,
        default="utf-8",
        help="Text encoding to use in output file.",
    )
    output_params.add_argument(
        "--strip-control",
        "-S",
        default=False,
        action="store_true",
        help="Remove control statement from text.",
    )
    output_params.add_argument(
        "--num-workers",
        "-j",
        type=int,
        default=None,
        help=f"Number of worker processes (default: {cpu_count()})",
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
    if parsed_args.page_numbers:
        parsed_args.page_numbers = {x - 1 for x in parsed_args.page_numbers}
    if parsed_args.pagenos:
        parsed_args.page_numbers = {int(x) - 1 for x in parsed_args.pagenos.split(",")}
    return parsed_args


def main(args: list[str] | None = None) -> int:
    parsed_args = parse_args(args)
    extract_text(**vars(parsed_args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
