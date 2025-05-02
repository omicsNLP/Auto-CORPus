"""BioCTable Package.

This package provides classes for handling modified BioC table structures, including cells, collections, documents, JSON encoding, and passages.
"""

from .cell import BioCTableCell
from .collection import BioCTableCollection
from .document import BioCTableDocument
from .encoder import BioCTableJSONEncoder
from .passage import BioCTablePassage

__all__ = [
    "BioCTableCell",
    "BioCTableCollection",
    "BioCTableDocument",
    "BioCTableJSONEncoder",
    "BioCTablePassage",
]
