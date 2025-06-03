"""Module providing functions for processing files with Auto-CORPus."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import logger
from .ac_bioc.bioctable.json import BioCTableJSONEncoder
from .ac_bioc.json import BioCJSONEncoder
from .autocorpus import Autocorpus
from .file_type import FileType, check_file_type
from .html import process_html_article


def process_file(
    config: dict[str, Any], file_path: Path, linked_tables: list[Path] = []
) -> Autocorpus:
    """Process the input file based on its type.

    This method checks the file type and processes the file accordingly.

    Args:
        config: Configuration dictionary for the input journal articles
        file_path: Path to the article file to be processed
        linked_tables: list of linked table file paths to be included in this run
            (HTML files only)

    Raises:
        NotImplementedError: For files types with no implemented processing.
        ModuleNotFoundError: For PDF processing if required packages are not found.
    """
    match check_file_type(file_path):
        case FileType.HTML:
            return Autocorpus(
                file_path, *process_html_article(config, file_path, linked_tables)
            )
        case FileType.XML:
            raise NotImplementedError(
                f"Could not process file {file_path}. Process XML files by running:\n\t"
                f"python -m autocorpus.parse_xml {file_path}"
            )
        case FileType.PDF:
            try:
                from .pdf import extract_pdf_content

                text, tables = extract_pdf_content(file_path)

                main_text: dict[str, Any] = {}
                if text:
                    main_text = text.to_dict()

                tables_dict: dict[str, Any] = {}
                if tables:
                    tables_dict = tables.to_dict()

                return Autocorpus(file_path, main_text, dict(), tables_dict)

            except ModuleNotFoundError:
                logger.error(
                    "Could not load necessary PDF packages. If you installed "
                    "Auto-CORPUS via pip, you can obtain these with:\n"
                    "    pip install autocorpus[pdf]"
                )
                raise
        case FileType.WORD:
            try:
                from .word import extract_word_content

                text, tbls = extract_word_content(file_path)

                # TODO: Use text.to_dict() after bugfix in ac_bioc (Issue #272)
                main_text: dict[str, Any] = {}
                if text:
                    main_text = text.to_dict()

                tables_dict: dict[str, Any] = {}
                if tbls:
                    tables_dict = tbls.to_dict()

                return Autocorpus(file_path, main_text, dict(), tables_dict)
            except ModuleNotFoundError:
                logger.error(
                    "Could not load necessary Word packages. Microsoft Word is required to process Word documents on Windows & MAC OS, or alternatively LibreOffice can be used on Linux.\n"
                )
                raise

        case FileType.UNKNOWN:
            raise NotImplementedError(f"Could not identify file type for {file_path}")


def process_directory(config: dict[str, Any], dir_path: Path) -> Iterable[Autocorpus]:
    """Process all files in a directory and its subdirectories.

    Args:
        config: Configuration dictionary for the input HTML journal articles
        dir_path: Path to the directory containing files to be processed.

    Returns:
        A generator yielding Autocorpus objects for each processed file.
    """
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            yield process_file(config, file_path)

        elif file_path.is_dir():
            # recursively process all files in the subdirectory
            for sub_file_path in file_path.rglob("*"):
                yield process_file(config, sub_file_path)


def process_files(config: dict[str, Any], files: list[Path]) -> Iterable[Autocorpus]:
    """Process all files in a list.

    Args:
        config: Configuration dictionary for the input HTML journal articles
        files: list of Paths to the files to be processed.

    Returns:
        A generator yielding Autocorpus objects for each processed file.

    Raises:
        RuntimeError: If the list of files is invalid.
    """
    if not all(file.is_file() for file in files):
        raise RuntimeError("All files must be valid file paths.")

    for file_path in files:
        yield process_file(config, file_path)
