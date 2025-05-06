"""BioCTable Package.

This package provides classes for handling modified BioC table structures, including cells, collections, documents, JSON encoding, and passages.
"""

from .annotation import BioCAnnotation
from .collection import BioCCollection
from .document import BioCDocument
from .encoder import BioCJSONEncoder
from .passage import BioCPassage
from .relation import BioCRelation
from .sentence import BioCSentence

__all__ = [
    "BioCAnnotation",
    "BioCCollection",
    "BioCDocument",
    "BioCJSONEncoder",
    "BioCKey",
    "BioCPassage",
    "BioCRelation",
    "BioCSentence",
]
