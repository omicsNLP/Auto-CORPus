"""Functionality for processing PDF files."""

from pathlib import Path

import pandas as pd
import regex
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from pandas import DataFrame

from autocorpus.bioc_supplementary import BioCTableConverter, BioCTextConverter

from . import logger
from .ac_bioc import BioCCollection
from .ac_bioc.bioctable.json import BioCTableCollection

_pdf_converter: PdfConverter | None = None


def _get_pdf_converter() -> PdfConverter | None:
    global _pdf_converter
    if _pdf_converter is None:
        try:
            # Load the PDF models
            _pdf_converter = PdfConverter(
                artifact_dict=create_model_dict(),
            )
        except Exception as e:
            logger.error(f"Error loading PDF models: {e}")
            return None

    return _pdf_converter


def extract_pdf_content(
    file_path: Path,
) -> tuple[BioCCollection, BioCTableCollection]:
    """Extracts content from a PDF file.

    Args:
        file_path (Path): Path to the PDF file.

    Returns:
        A tuple of BioCTextConverter and BioCTableConverter objects containing
        the extracted text and tables.

    Raises:
        RuntimeError: If the PDF converter is not initialized.
    """
    bioc_text, bioc_tables = None, None

    pdf_converter = _get_pdf_converter()
    if not pdf_converter:
        message = "PDF converter not initialized."
        logger.error(message)
        raise RuntimeError(message)

    # extract text from PDF
    rendered = pdf_converter(str(file_path))
    text, _, _ = text_from_rendered(rendered)
    # separate text and tables
    text, tables = _extract_table_from_pdf_text(text)
    # format data for BioC
    bioc_text = BioCTextConverter.build_bioc(text, str(file_path), "pdf")
    bioc_tables = BioCTableConverter.build_bioc(tables, str(file_path))

    return bioc_text, bioc_tables


def _split_text_and_tables(text: str) -> tuple[list[str], list[list[str]]]:
    """Splits PDF text into main text lines and raw table lines."""
    lines = [x for x in text.splitlines() if x]
    tables = []
    table_lines = []
    main_text_lines = []
    inside_table = False

    for line in lines:
        if "|" in line:
            inside_table = True
            table_lines.append(line)
        elif inside_table:
            inside_table = False
            tables.append(table_lines)
            main_text_lines.append(line)
            table_lines = []
            continue
        else:
            main_text_lines.append(line)

    return main_text_lines, tables


def _parse_tables(raw_tables: list[list[str]]) -> list[DataFrame]:
    """Converts raw table text lines into DataFrames."""
    parsed_tables = []
    for table in raw_tables:
        # Remove lines that are just dashes
        table = [line for line in table if not regex.match(r"^\s*[\p{Pd}]+\s*$", line)]

        rows = []
        for line in table:
            if regex.search(r"\|", line):
                cells = [
                    cell.strip()
                    for cell in line.split("|")
                    if not all(x in "|-" for x in cell)
                ]
                if cells:
                    rows.append(cells)

        if not rows:
            continue

        num_columns = max(len(row) for row in rows)
        for row in rows:
            while len(row) < num_columns:
                row.append("")

        df = pd.DataFrame(rows[1:], columns=rows[0])
        parsed_tables.append(df)

    return parsed_tables


def _extract_table_from_pdf_text(text: str) -> tuple[str, list[DataFrame]]:
    """Extracts tables from PDF text and returns the remaining text and parsed tables."""
    main_text_lines, raw_tables = _split_text_and_tables(text)
    tables_output = _parse_tables(raw_tables)
    text_output = "\n\n".join(main_text_lines)
    return text_output, tables_output
