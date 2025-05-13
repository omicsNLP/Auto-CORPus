"""This module defines the BioCTableDocument class.

Extends BioCDocument to include BioCTablePassage objects and provides a method to convert the
document to a dictionary representation.
"""

from dataclasses import dataclass, field
from typing import Any

from ...ac_bioc import BioCDocument, BioCPassage
from ...ac_bioc.bioctable.passage import BioCTablePassage


@dataclass
class BioCTableDocument(BioCDocument):
    """Extends BioCDocument to include BioCTablePassage objects."""

    passages: list[BioCPassage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the BioCTableDocument to a dictionary representation."""
        base = super().to_dict()
        base["passages"] = [
            p.to_dict() for p in self.passages if isinstance(p, BioCTablePassage)
        ]
        return base
