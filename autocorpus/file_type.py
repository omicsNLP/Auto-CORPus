"""Contains utilities for identifying file types based on content and extension."""

from enum import Enum, auto
from pathlib import Path

from lxml import etree

from . import logger


class FileType(Enum):
    """Enum for different file types.

    Access the attributes like so FileType.HTML, FileType.XML, etc.

    Attributes:
        HTML: Represents an HTML file.
        XML: Represents an XML file.
        PDF: Represents a PDF file.
        WORD: Represents a Word document (DOCX or DOC).
        UNKNOWN: Represents any other file type that is not recognized.
    """

    HTML = auto()
    XML = auto()
    PDF = auto()
    WORD = auto()
    UNKNOWN = auto()


def check_file_type(file_path: Path) -> FileType:
    """Determines the type of a file based on its content and extension.

    This function checks the given file type by checking the file extension and then
    attempting to parse it using appropriate parsers. If the file cannot
    be parsed or the fileextension is not recognised, it is classified as "OTHER".

    Args:
        file_path: The path to the file to be checked.

    Returns:
        A FileType Enum value indicating the type of the file.

    Raises:
        FileNotFoundError: If the provided path does not point to a file.
    """
    if not file_path.is_file():
        message = f"File {file_path} is not a file."
        logger.error(message)
        raise FileNotFoundError(message)
    file_extension = file_path.suffix.lower()
    match file_extension:
        case ".html" | ".htm" | ".xml":
            try:
                if not etree.parse(file_path, etree.XMLParser()).docinfo.xml_version:
                    raise etree.ParseError("Not a valid XML file")
                return FileType.XML
            except etree.ParseError:
                docinfo = etree.parse(file_path, etree.HTMLParser()).docinfo
                if not isinstance(docinfo, etree.DocInfo) and not docinfo.doctype:
                    raise etree.ParseError("Not a valid HTML file")
                return FileType.HTML
            except Exception as ex:
                logger.error(f"Error parsing file {file_path}: {ex}")
                return FileType.UNKNOWN
        case ".pdf":
            return FileType.PDF
        case ".docx" | ".doc":
            return FileType.WORD
        case _:
            return FileType.UNKNOWN
