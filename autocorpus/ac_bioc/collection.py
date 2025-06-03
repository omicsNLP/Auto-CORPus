"""This module defines the BioCCollection class.

BioCCollection extends BioCCollection to include a list of BioCDocument objects and provides a method to convert
the collection to a dictionary representation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

from dataclasses_json import dataclass_json

from .document import BioCDocument


@dataclass_json
@dataclass
class BioCCollection:
    """A class representing a BioC collection."""

    source: str = field(default_factory=str)
    date: str = field(default_factory=str)
    key: str = field(default_factory=str)
    documents: list[BioCDocument] = field(default_factory=list)
    infons: dict[str, str] = field(default_factory=dict)

    to_dict = asdict

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
