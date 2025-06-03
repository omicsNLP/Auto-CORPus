"""This module defines the BioCTableDocument class.

Extends BioCDocument to include BioCTablePassage objects and provides a method to convert the
document to a dictionary representation.
"""

from dataclasses import dataclass, field

from ...ac_bioc import BioCAnnotation, BioCDocument, BioCPassage


@dataclass
class BioCTableDocument(BioCDocument):
    """Extends BioCDocument to include BioCTablePassage objects."""

    passages: list[BioCPassage] = field(default_factory=list)
    annotations: list[BioCAnnotation] = field(default_factory=list)
