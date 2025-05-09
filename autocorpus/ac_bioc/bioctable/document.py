"""This module defines the BioCTableDocument class."""

from typing import Any

from ...ac_bioc import BioCDocument
from .passage import BioCTablePassage


class BioCTableDocument(BioCDocument):
    """Extends BioCDocument to include BioCTablePassage objects.

    Attributes:
        passages : list[BioCTablePassage]
            A list of BioCTablePassage objects associated with the document.

    Methods:
        to_dict() -> dict[str, Any]
            Converts the document and its passages to a dictionary representation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a BioCTableDocument instance.

        Args:
            *args: Variable length argument list for the parent class.
            **kwargs: Arbitrary keyword arguments for the parent class.
        """
        super().__init__(*args, **kwargs)
        self.passages: list[BioCTablePassage] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert the document and its passages to a dictionary representation.

        Returns:
            dict[str, Any]: A dictionary containing the document's data and its passages.
        """
        base = super().to_dict()
        base["passages"] = [p.to_dict() for p in self.passages]
        return base
