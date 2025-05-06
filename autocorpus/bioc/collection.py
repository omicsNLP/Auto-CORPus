"""This module defines the BioCCollection class.

BioCCollection extends BioCCollection to include a list of BioCDocument objects and provides a method to convert
the collection to a dictionary representation.
"""

from .document import BioCDocument


class BioCCollection:
    def __init__(
        self,
        source: str = "",
        date: str = "",
        key: str = "",
        documents: list[BioCDocument] | None = None,
        infons: dict[str, str] | None = None,
        version: str = "",
    ):
        self.source = source
        self.date = date
        self.key = key
        self.documents = documents or []
        self.infons = infons or {}
        self.version = version

    def to_dict(self):
        return {
            "source": self.source,
            "date": self.date,
            "key": self.key,
            "infons": self.infons,
            "documents": [d.to_dict() for d in self.documents],
        }

    def validate_with_key(self, key_file_path: str):
        # Placeholder: you'd load your schema and validate the collection here
        pass
