"""BioCTable Package.

This package provides classes for handling modified BioC table structures, including cells, collections, documents, JSON encoding, and passages.
"""

from .annotation import BioCAnnotation
from .collection import BioCCollection
from .document import BioCDocument
from .json import BioCJSON
from .location import BioCLocation
from .node import BioCNode
from .passage import BioCPassage
from .relation import BioCRelation
from .sentence import BioCSentence
from .xml import BioCXML

__all__ = [
    "BioCAnnotation",
    "BioCCollection",
    "BioCDocument",
    "BioCJSON",
    "BioCKey",
    "BioCLocation",
    "BioCNode",
    "BioCPassage",
    "BioCRelation",
    "BioCSentence",
    "BioCXML",
]
