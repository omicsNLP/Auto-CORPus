"""This module provides functionality to extract text and tables from Word documents (.doc and .docx).

It includes methods to handle older .doc files by converting them to .docx format and processing them.
"""

import os
import platform
import subprocess
from pathlib import Path

import docx
from docx import Document

from autocorpus.ac_bioc.bioctable.collection import BioCTableCollection
from autocorpus.ac_bioc.bioctable.json import BioCTableJSON
from autocorpus.ac_bioc.collection import BioCCollection
from autocorpus.ac_bioc.json import BioCJSON
from autocorpus.bioc_supplementary import BioCTableConverter, BioCTextConverter

from . import logger


def __extract_tables(doc: docx.document.Document) -> list[list[list[str]]]:
    """Extracts tables from a .docx document.

    Args:
        doc: The Document object representing the .docx document.

    Returns:
        list: A list of tables extracted from the document. Each table is represented as a nested list,
              where each inner list corresponds to a row, and each element in the inner list corresponds
              to the text content of a cell in the row.

    Example:
        from docx import Document

        doc = Document("document.docx")
        tables = extract_tables(doc)
    """
    # Open the .docx file
    tables: list[list[list[str]]] = []
    # Iterate through the tables in the document
    for table in doc.tables:
        tables.append([])
        # Iterate through the rows in the table
        for row in table.rows:
            tables[-1].append([x.text for x in row.cells])
    return tables


def __windows_convert_doc_to_docx(docx_path: Path, file: Path) -> Path | bool:
    """Converts a .doc file to .docx format using Microsoft Word on Windows."""
    try:
        import win32com.client
    except ImportError as e:
        logger.error(
            "pywin32 is required to convert Word documents on Windows. Please install it via 'pip install pywin32'."
        )
        return False

    word = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        doc = word.Documents.Open(str(file))
        doc.SaveAs(str(docx_path), 16)  # 16 = wdFormatDocumentDefault (.docx)
        doc.Close()
        logger.info(
            f"Successfully converted '{file}' to '{docx_path}' using Word on Windows."
        )
        return docx_path
    except Exception as e:
        logger.exception(f"Failed to convert '{file}' on Windows: {e}")
        return False
    finally:
        if word:
            try:
                word.Quit()
            except Exception as quit_err:
                logger.warning(f"Could not quit Word application cleanly: {quit_err}")


def __linux_convert_doc_to_docx(docx_path: Path, file: Path) -> Path | bool:
    """Converts a .doc file to .docx format using LibreOffice on Linux."""
    try:
        result = subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "docx",
                "--outdir",
                str(docx_path.parent),
                str(file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"LibreOffice output: {result.stdout}")
        return docx_path
    except FileNotFoundError:
        logger.error(
            "LibreOffice ('soffice') not found. Please install it to enable DOC to DOCX conversion."
        )
        return False
    except subprocess.CalledProcessError as e:
        logger.exception(f"LibreOffice failed to convert '{file}': {e.stderr}")
        return False


def __macos_convert_doc_to_docx(docx_path: Path, file: Path) -> Path | bool:
    """Converts a .doc file to .docx format using AppleScript on macOS."""
    try:
        applescript = f'''
        tell application "Microsoft Word"
            open "{file}"
            save as active document file name "{docx_path}" file format format document
            close active document saving no
        end tell
        '''
        subprocess.run(["osascript", "-e", applescript], check=True)
        logger.info(
            f"Successfully converted '{file}' to '{docx_path}' using Word on macOS."
        )
        return docx_path
    except FileNotFoundError:
        logger.error(
            "osascript not found. Ensure you have AppleScript and Microsoft Word installed on macOS."
        )
        return False
    except subprocess.CalledProcessError as e:
        logger.exception(f"AppleScript failed to convert '{file}': {e}")
        return False


def __convert_older_doc_file(file: Path, output_dir: Path) -> Path | bool:
    """Converts an older .doc file to .docx format using platform-specific methods."""
    operating_system = platform.system()
    docx_path = output_dir / file.with_suffix(".docx").name

    if operating_system == "Windows":
        return __windows_convert_doc_to_docx(docx_path, file)
    elif operating_system == "Linux":
        return __linux_convert_doc_to_docx(docx_path, file)
    elif operating_system == "Darwin":  # macOS
        return __macos_convert_doc_to_docx(docx_path, file)
    else:
        logger.error(f"Unsupported operating system: {operating_system}")
        return False


def extract_word_content(file_path: Path):
    """Extracts text from a .doc file by converting it to .docx and processing with python-docx."""
    if file_path.suffix.lower() not in [".doc", ".docx"]:
        raise ValueError("Input file must be a .doc file.")
    try:
        output_dir = Path(file_path).parent.absolute()
        # Check if the file is a .doc file
        if file_path.suffix.lower() == ".doc":
            docx_path = __convert_older_doc_file(file_path, output_dir)

        # Extract text from the resulting .docx file
        doc = Document(str(docx_path))
        tables = __extract_tables(doc)
        text_sizes = set(
            [
                int(x.style.font.size)
                for x in doc.paragraphs
                if x.style and x.style.font.size
            ]
        )
        paragraphs = [
            (
                x.text,
                True
                if text_sizes
                and x.style
                and x.style.font.size
                and int(x.style.font.size) > min(text_sizes)
                else False,
            )
            for x in doc.paragraphs
        ]
        bioc_text: BioCCollection | None = None
        bioc_tables: BioCTableCollection | None = None

        if paragraphs:
            bioc_text = BioCTextConverter.build_bioc(paragraphs, str(file_path), "word")

        if tables:
            bioc_tables = BioCTableConverter.build_bioc(tables, str(file_path))

        if bioc_text:
            out_filename = str(file_path).replace(
                file_path.suffix, f"{file_path.suffix}_bioc.json"
            )
            with open(out_filename, "w", encoding="utf-8") as f:
                BioCJSON.dump(bioc_text, f, indent=4)

        if bioc_tables:
            out_table_filename = str(file_path).replace(
                file_path.suffix, f"{file_path.suffix}_tables.json"
            )
            with open(out_table_filename, "w", encoding="utf-8") as f:
                BioCTableJSON.dump(bioc_tables, f, indent=4)

        os.unlink(str(docx_path))
    except FileNotFoundError:
        logger.error(
            "LibreOffice 'soffice' command not found. Ensure it is installed and in your PATH."
        )
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
