"""Contains utilities for identifying file types based on content and extension."""

from enum import Enum, auto
from pathlib import Path

from lxml import etree

from . import logger


class FileType(Enum):
    """Enumeration for different file types."""

    HTML = auto()
    XML = auto()
    PDF = auto()
    OTHER = auto()


def check_file_type(file_path: Path) -> FileType:
    """Determines the type of a file based on its content and extension.

    This function checks whether the given file is an HTML or XML file by
    attempting to parse it using appropriate parsers. If the file cannot
    be parsed as either HTML or XML, it is classified as "other".

    Args:
        file_path: The path to the file to be checked.

    Returns:
        A string indicating the file type:
             - "html" if the file is determined to be an HTML file.
             - "xml" if the file is determined to be an XML file.
             - "other" if the file type cannot be determined as HTML or XML.
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
