"""This module defines the BioC class.

BioC extends BioC to include additional functionality for handling  data, such as
column headings and data sections.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from .annotation import BioCAnnotation
from .relation import BioCRelation
from .sentence import BioCSentence


@dataclass
class BioCPassage:
    """Represents a passage in a BioC document."""

    text: str = field(default_factory=str)
    offset: int = field(default_factory=int)
    infons: dict[str, Any] = field(default_factory=dict)
    sentences: list[BioCSentence] = field(default_factory=list)
    annotations: list[BioCAnnotation] = field(default_factory=list)
    relations: list[BioCRelation] = field(default_factory=list)

    def to_dict(self):
        """Convert the BioCPassage instance to a dictionary representation."""
        return {
            "text": self.text,
            "offset": self.offset,
            "infons": self.infons,
            "sentences": [s.to_dict() for s in self.sentences],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioCPassage:
        """Create a BioCPassage instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing passage data.

        Returns:
            BioCPassage: An instance of BioCPassage populated with the provided data.
        """
        sentences = [BioCSentence.from_dict(s) for s in data.get("sentences", [])]
        return cls(
            text=data.get("text", ""),
            offset=data.get("offset", 0),
            infons=data.get("infons", {}),
            sentences=sentences,
        )

    def to_json(self) -> dict[str, Any]:
        """Convert the BioCPassage instance to a JSON-compatible dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the BioCPassage instance.
        """
        return self.to_dict()

    def to_xml(self) -> ET.Element:
        """Convert the BioCPassage instance to an XML element.

        Returns:
            ET.Element: An XML element representation of the BioCPassage instance.
        """
        passage_elem = ET.Element("passage")

        for k, v in self.infons.items():
            infon = ET.SubElement(passage_elem, "infon", {"key": k})
            infon.text = v

        offset_elem = ET.SubElement(passage_elem, "offset")
        offset_elem.text = str(self.offset)

        text_elem = ET.SubElement(passage_elem, "text")
        text_elem.text = self.text

        for sentence in self.sentences:
            passage_elem.append(sentence.to_xml())

        return passage_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCPassage:
        """Create a BioCPassage instance from an XML element.

        Args:
            elem (ET.Element): An XML element representing a passage.

        Returns:
            BioCPassage: An instance of BioCPassage populated with the provided XML data.
        """
        offset = int(elem.findtext("offset", default="0"))
        text = elem.findtext("text", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        sentences = [
            BioCSentence.from_xml(s_elem) for s_elem in elem.findall("sentence")
        ]

        return cls(
            text=text,
            offset=offset,
            infons=infons,
            sentences=sentences,
        )
