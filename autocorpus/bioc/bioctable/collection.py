"""This module defines the BioCTableCollection class.

BioCTableCollection extends BioCCollection to include a list of BioCTableDocument objects and provides a method to convert
the collection to a dictionary representation.
"""

from typing import Any

from ...bioc import BioCCollection
from .document import BioCTableDocument


class BioCTableCollection(BioCCollection):
    """A collection of BioCTableDocument objects extending BioCCollection.

    Attributes:
        documents : list[BioCTableDocument]
            A list of BioCTableDocument objects in the collection.

    Methods:
        to_dict() -> dict[str, Any]
            Converts the collection to a dictionary representation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a BioCTableCollection with optional arguments.

        Args:
            *args: Variable length argument list passed to the parent class.
            **kwargs: Arbitrary keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.documents: list[BioCTableDocument] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert the BioCTableCollection to a dictionary representation.

        Returns:
            dict[str, Any]: A dictionary containing the collection's data, including its documents.
        """
        base = super().to_dict()
        base["documents"] = [doc.to_dict() for doc in self.documents]
        return base
