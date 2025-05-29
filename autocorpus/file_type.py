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
        OTHER: Represents any other file type that is not recognized.
    """

    HTML = auto()
    XML = auto()
    PDF = auto()
    OTHER = auto()


def check_file_type(file_path: Path) -> FileType:
    """Determines the type of a file based on its content and extension.

    This function checks the given file type by checking the file extension and then
    attempting to parse it using appropriate parsers. If the file cannot
    be parsed or the fileextension is not recognised, it is classified as "OTHER".

    Args:
        file_path: The path to the file to be checked.

    Returns:
        A FileType Enum value indicating the type of the file.
    """
    file_extension = file_path.suffix.lower()
    match file_extension:
        case ".html" | ".htm" | ".xml":
            try:
                assert etree.parse(file_path, etree.XMLParser()).docinfo.xml_version
                return FileType.XML
            except (etree.ParseError, AssertionError):
                etree.parse(file_path, etree.HTMLParser())
                return FileType.HTML
            except Exception as ex:
                logger.error(f"Error parsing file {file_path}: {ex}")
                return FileType.OTHER
        case ".pdf":
            return FileType.PDF
        case _:
            return FileType.OTHER
