"""Functionality for processing PDF files."""

from pathlib import Path

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from autocorpus.bioc_supplementary import (
    BioCTableConverter,
    BioCTextConverter,
    extract_table_from_pdf_text,
)

from . import logger
from .ac_bioc import BioCJSON
from .ac_bioc.bioctable.json import BioCTableJSON

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
) -> bool:
    """Extracts content from a PDF file.

    Args:
        file_path (Path): Path to the PDF file.

    Returns:
        bool: success status of the extraction process.
    """
    bioc_text, bioc_tables = None, None

    pdf_converter = _get_pdf_converter()
    if not pdf_converter:
        logger.error("PDF converter not initialized.")
        return False

    # extract text from PDF
    rendered = pdf_converter(str(file_path))
    text, _, _ = text_from_rendered(rendered)
    # separate text and tables
    text, tables = extract_table_from_pdf_text(text)
    # format data for BioC
    bioc_text = BioCTextConverter.build_bioc(text, str(file_path), "pdf")
    bioc_tables = BioCTableConverter.build_bioc(tables, str(file_path))

    out_filename = str(file_path).replace(".pdf", ".pdf_bioc.json")
    with open(out_filename, "w", encoding="utf-8") as f:
        BioCJSON.dump(bioc_text, f, indent=4)

    out_table_filename = str(file_path).replace(".pdf", ".pdf_tables.json")
    with open(out_table_filename, "w", encoding="utf-8") as f:
        BioCTableJSON.dump(bioc_tables, f, indent=4)
    return True
