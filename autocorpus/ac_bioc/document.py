"""This module defines the BioCDocument class.

BioCDocument objects include a list of BioCPassage objects and provide a method to
convert the document to a dictionary representation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from .annotation import BioCAnnotation
from .passage import BioCPassage
from .relation import BioCRelation


@dataclass
class BioCDocument:
    """Represents a BioC document containing passages, annotations, and relations."""

    id: str = field(default_factory=str)
    inputfile: str = field(default_factory=str)
    infons: dict[str, str] = field(default_factory=dict)
    passages: list[BioCPassage] = field(default_factory=list)
    relations: list[BioCRelation] = field(default_factory=list)

    def to_dict(self):
        """Convert the BioCDocument instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the document's ID, infons, and passages.
        """
        return {
            "id": self.id,
            "infons": self.infons,
            "passages": [p.to_dict() for p in self.passages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioCDocument:
        """Create a BioCDocument instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing the document's data.

        Returns:
            BioCDocument: An instance of BioCDocument created from the dictionary.
        """
        passages = [BioCPassage.from_dict(p) for p in data.get("passages", [])]
        return cls(
            id=data["id"],
            infons=data.get("infons", {}),
            passages=passages,
            relations=data.get("relations", []),
        )

    def to_json(self) -> dict[str, Any]:
        """Convert the BioCDocument instance to a JSON-compatible dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the document.
        """
        return self.to_dict()

    def to_xml(self) -> ET.Element:
        """Convert the BioCDocument instance to an XML element.

        Returns:
            ET.Element: An XML element representing the document.
        """
        doc_elem = ET.Element("document")

        id_elem = ET.SubElement(doc_elem, "id")
        id_elem.text = self.id

        for k, v in self.infons.items():
            infon = ET.SubElement(doc_elem, "infon", {"key": k})
            infon.text = v

        for passage in self.passages:
            doc_elem.append(passage.to_xml())

        for rel in self.relations:
            doc_elem.append(rel.to_xml())

        return doc_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCDocument:
        """Create a BioCDocument instance from an XML element.

        Args:
            elem (ET.Element): An XML element representing the document.

        Returns:
            BioCDocument: An instance of BioCDocument created from the XML element.
        """
        id_text = elem.findtext("id", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        passages = [BioCPassage.from_xml(p_elem) for p_elem in elem.findall("passage")]

        return cls(
            id=id_text,
            infons=infons,
            passages=passages,
        )
