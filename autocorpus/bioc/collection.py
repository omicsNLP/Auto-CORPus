"""This module defines the BioCCollection class.

BioCCollection extends BioCCollection to include a list of BioCDocument objects and provides a method to convert
the collection to a dictionary representation.
"""

import xml.etree.ElementTree as ET
from typing import Any

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

    def to_json(self) -> dict[str, Any]:
        return self.to_dict()

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "BioCCollection":
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
    def from_xml(cls, elem: ET.Element) -> "BioCCollection":
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
