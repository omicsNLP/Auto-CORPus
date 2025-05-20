"""This module provides functionality to extract text and tables from Word documents (.doc and .docx).

It includes methods to handle older .doc files by converting them to .docx format and processing them.
"""

import os
import platform
import subprocess
from pathlib import Path

from docx import Document

from autocorpus.bioc_supplementary import BioCTableConverter, BioCTextConverter

from . import logger


def __extract_tables(doc):
    """Extracts tables from a .docx document.

    Args:
        doc (docx.Document): The Document object representing the .docx document.

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
    tables = []
    # Iterate through the tables in the document
    for table in doc.tables:
        tables.append([])
        # Iterate through the rows in the table
        for row in table.rows:
            tables[-1].append([x.text for x in row.cells])
    return tables


def __convert_older_doc_file(file: Path, output_dir: Path) -> Path | bool:
    """Converts an older .doc file to .docx format using platform-specific methods."""
    operating_system = platform.system()
    docx_path = Path(str(file).replace(".doc", ".docx"))
    if operating_system == "Windows":
        import win32com.client

        word = None
        try:
            word = win32com.client.DispatchEx("Word.Application")
            doc = word.Documents.Open(file)
            doc.SaveAs(docx_path, 16)
            doc.Close()
            word.Quit()
            return docx_path
        except Exception:
            return False
        finally:
            if word:
                word.Quit()
    elif operating_system == "Linux":
        # Convert .doc to .docx using LibreOffice
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "docx",
                "--outdir",
                output_dir,
                file,
            ],
            check=True,
            capture_output=True,
        )
        return docx_path
    elif operating_system == "Darwin":  # macOS
        try:
            # AppleScript to open the file in Word and save as .docx
            applescript = f'''
            tell application "Microsoft Word"
                open "{file}"
                save as active document file name "{docx_path}" file format format document
                close active document saving no
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            return docx_path
        except Exception:
            return False
    else:
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
        bioc_text = BioCTextConverter(paragraphs, "word", str(file_path))
        bioc_text.output_bioc_json(file_path)
        bioc_tables = BioCTableConverter(tables, str(file_path))
        bioc_tables.output_tables_json(file_path)
        print(str(docx_path))
        os.unlink(str(docx_path))
    except FileNotFoundError:
        logger.error(
            "LibreOffice 'soffice' command not found. Ensure it is installed and in your PATH."
        )
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
