"""BioCTable Package.

This package provides classes for handling modified BioC table structures, including cells, collections, documents, JSON encoding, and passages.
"""

from .cell import BioCTableCell
from .collection import BioCTableCollection
from .document import BioCTableDocument
from .json import BioCTableJSON
from .passage import BioCTablePassage

__all__ = [
    "BioCTableCell",
    "BioCTableCollection",
    "BioCTableDocument",
    "BioCTableJSON",
    "BioCTablePassage",
]
