"""This module defines the BioCCollection class.

BioCCollection extends BioCCollection to include a list of BioCDocument objects and provides a method to convert
the collection to a dictionary representation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from .document import BioCDocument


@dataclass
class BioCCollection:
    """A class representing a BioC collection."""

    source: str = field(default_factory=str)
    date: str = field(default_factory=str)
    key: str = field(default_factory=str)
    documents: list[BioCDocument] = field(default_factory=list)
    infons: dict[str, str] = field(default_factory=dict)
    version: str = field(default="1.0")

    def to_dict(self):
        """Convert the BioCCollection instance to a dictionary.

        Returns:
            dict: A dictionary representation of the BioCCollection instance.
        """
        return {
            "source": self.source,
            "date": self.date,
            "key": self.key,
            "infons": self.infons,
            "documents": [d.to_dict() for d in self.documents],
        }

    def to_json(self) -> dict[str, Any]:
        """Convert the BioCCollection instance to a JSON-compatible dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the BioCCollection instance.
        """
        return self.to_dict()

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> BioCCollection:
        """Create a BioCCollection instance from a JSON dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing the JSON representation of a BioCCollection.

        Returns:
            BioCCollection: An instance of BioCCollection created from the JSON dictionary.
        """
        documents = [BioCDocument.from_dict(d) for d in data.get("documents", [])]
        return cls(
            source=data.get("source", ""),
            date=data.get("date", ""),
            key=data.get("key", ""),
            infons=data.get("infons", {}),
            version=data.get("version", ""),
            documents=documents,
        )

    def to_xml(self) -> ET.Element:
        """Convert the BioCCollection instance to an XML element.

        Returns:
            ET.Element: An XML element representation of the BioCCollection instance.
        """
        collection_elem = ET.Element("collection")

        if self.source:
            source_elem = ET.SubElement(collection_elem, "source")
            source_elem.text = self.source

        if self.date:
            date_elem = ET.SubElement(collection_elem, "date")
            date_elem.text = self.date

        if self.key:
            key_elem = ET.SubElement(collection_elem, "key")
            key_elem.text = self.key

        if self.infons:
            for k, v in self.infons.items():
                infon = ET.SubElement(collection_elem, "infon", {"key": k})
                infon.text = v

        for doc in self.documents:
            collection_elem.append(doc.to_xml())

        return collection_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCCollection:
        """Create a BioCCollection instance from an XML element.

        Args:
            elem (ET.Element): The XML element representing a BioCCollection.

        Returns:
            BioCCollection: An instance of BioCCollection created from the XML element.
        """
        source = elem.findtext("source", default="")
        date = elem.findtext("date", default="")
        key = elem.findtext("key", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        documents = [
            BioCDocument.from_xml(doc_elem) for doc_elem in elem.findall("document")
        ]

        return cls(
            source=source, date=date, key=key, infons=infons, documents=documents
        )
