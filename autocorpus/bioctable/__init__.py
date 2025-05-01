"""BioCTable Package.

This package provides classes for handling modified BioC table structures, including cells, collections, documents, JSON encoding, and passages.
"""

from .BioCTableCell import BioCTableCell
from .BioCTableCollection import BioCTableCollection
from .BioCTableDocument import BioCTableDocument
from .BioCTableJSONEncoder import BioCTableJSONEncoder
from .BioCTablePassage import BioCTablePassage

__all__ = [
    "BioCTableCell",
    "BioCTableCollection",
    "BioCTableDocument",
    "BioCTableJSONEncoder",
    "BioCTablePassage",
]
