"""This module defines the BioCTableCollection class."""

from dataclasses import dataclass, field
from typing import Any

from ...ac_bioc import BioCCollection, BioCDocument


@dataclass
class BioCTableCollection(BioCCollection):
    """A collection of BioCTableDocument objects extending BioCCollection."""

    documents: list[BioCDocument] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the BioCTableCollection to a dictionary representation.

        Returns:
            dict[str, Any]: A dictionary containing the collection's data, including its documents.
        """
        base = super().to_dict()
        base["documents"] = [doc.to_dict() for doc in self.documents]
        return base
